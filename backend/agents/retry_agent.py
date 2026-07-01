import json
import re
import time
from pathlib import Path

from google import genai
from google.genai import types

from backend.core.config import settings
from backend.core.gemini_queue import GeminiRequestQueue


def _load_prompt() -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "retry.md"
    return path.read_text(encoding="utf-8")


class RetryAgent:
    MAX_RETRIES = 3

    def __init__(self, queue: GeminiRequestQueue):
        self._model = settings.gemini_model
        self._prompt = _load_prompt()
        self._queue = queue
        print("[RETRY_AGENT] Initialised")

    def retry(
        self,
        user_message: str,
        original_requirements: dict,
        failed_tool_call: dict,
        mcp_response: str,
        validation_verdict: dict,
        history: list[dict],
        mcp_client,
        send_status=None,
        send_agent_output=None,
        user_id=None,
    ) -> dict:
        print(f"[RETRY_AGENT] Starting retry loop for: {user_message[:60]}...")

        context = {
            "user_message": user_message,
            "original_requirements": original_requirements,
            "failed_tool_call": failed_tool_call,
            "mcp_response": mcp_response,
            "validation_verdict": validation_verdict,
            "history_summary": self._summarize_history(history),
            "attempts": [],
        }

        last_tool_call = failed_tool_call
        last_mcp_response = mcp_response
        any_connection_error = False

        for attempt in range(1, self.MAX_RETRIES + 1):
            print(f"[RETRY_AGENT] --- Internal attempt {attempt}/{self.MAX_RETRIES} ---")
            if send_status:
                send_status("retrying", f"Analysing and correcting request (attempt {attempt}/{self.MAX_RETRIES})...")

            prompt_text = self._build_prompt(context)

            client = genai.Client(api_key=settings.gemini_api_key)
            config = types.GenerateContentConfig(
                system_instruction=types.Content(
                    role="user",
                    parts=[types.Part(text=self._prompt)],
                ),
            )

            print(f"[RETRY_AGENT] Calling Gemini (attempt {attempt})...")
            response = self._queue.execute_with_retry(
                client,
                self._model,
                [types.Content(
                    role="user",
                    parts=[types.Part(text=prompt_text)],
                )],
                config,
            )

            action = self._parse_response(response)
            if not action:
                print("[RETRY_AGENT] Failed to parse action, giving up")
                return {"success": False, "feedback": "Could not analyse the failure to retry."}

            if send_agent_output:
                send_agent_output(f"Retry Analysis (attempt {attempt})", json.dumps(action, indent=2), "info")

            action_type = action.get("action")
            reasoning = action.get("reasoning", "")
            print(f"[RETRY_AGENT] Action: {action_type} - {reasoning[:100]}")

            if action_type == "satisfied":
                print("[RETRY_AGENT] Retry succeeded — MCP response is satisfactory")
                return {"success": True, "tool_call": last_tool_call, "mcp_response": last_mcp_response}

            if action_type == "give_up":
                print(f"[RETRY_AGENT] Giving up: {reasoning[:100]}")
                return {"success": False, "feedback": reasoning or "Could not find suitable results."}

            if action_type == "retry_same":
                tool_name = last_tool_call.get("tool")
                tool_args = last_tool_call.get("arguments", {})
                print(f"[RETRY_AGENT] Retrying same call: {tool_name}")
            elif action_type == "retry":
                tool_name = action.get("tool")
                tool_args = action.get("arguments", {})
                print(f"[RETRY_AGENT] Retrying with corrected call: {tool_name}({json.dumps(tool_args)[:120]})")
            else:
                print(f"[RETRY_AGENT] Unknown action type '{action_type}', giving up")
                return {"success": False, "feedback": "Could not determine how to retry."}

            try:
                if send_status:
                    detail = tool_name.replace("kapruka_", "").replace("_", " ")
                    send_status("searching", f"{detail}... (retry {attempt}/{self.MAX_RETRIES})")

                new_response = mcp_client.call_tool(tool_name, tool_args)
                any_connection_error = False
                print(f"[RETRY_AGENT] MCP call succeeded ({len(new_response)} chars)")
            except RuntimeError as e:
                any_connection_error = True
                print(f"[RETRY_AGENT] Connection error: {e}")
                context["attempts"].append({
                    "attempt": attempt,
                    "action": action_type,
                    "tool": tool_name,
                    "arguments": tool_args,
                    "error": f"Connection error: {e}",
                })
                if send_agent_output:
                    send_agent_output(f"Retry Attempt {attempt}", f"Connection error: {e}", "failure")
                if attempt < self.MAX_RETRIES:
                    delay = settings.retry_delay_ms / 1000.0
                    print(f"[RETRY_AGENT] Waiting {delay:.1f}s before next retry...")
                    time.sleep(delay)
                continue

            last_tool_call = {"tool": tool_name, "arguments": tool_args}
            last_mcp_response = new_response

            context["attempts"].append({
                "attempt": attempt,
                "action": action_type,
                "tool": tool_name,
                "arguments": tool_args,
                "response_preview": new_response[:600],
                "reasoning": reasoning,
            })

            if send_agent_output:
                send_agent_output(f"Retry Attempt {attempt}", f"Response ({len(new_response)} chars):\n{new_response[:300]}", "info")

            if attempt < self.MAX_RETRIES:
                delay = settings.retry_delay_ms / 1000.0
                print(f"[RETRY_AGENT] Waiting {delay:.1f}s before next retry...")
                time.sleep(delay)

        print("[RETRY_AGENT] Max internal retries exhausted")
        if any_connection_error:
            return {
                "success": False,
                "connection_error": True,
                "feedback": "The service is currently unavailable due to a connection issue. Please try again later.",
            }
        return {"success": False, "feedback": "Could not find suitable results after multiple attempts."}

    def _summarize_history(self, history: list[dict]) -> str:
        if not history:
            return "No prior conversation."
        lines = []
        for msg in history[-6:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"[{role}]: {content[:200]}")
        return "\n".join(lines)

    def _build_prompt(self, context: dict) -> str:
        parts = [
            "## Original user request",
            context["user_message"],
            "",
            "## Original requirements",
            json.dumps(context["original_requirements"], indent=2),
            "",
            "## Failed tool call",
            json.dumps(context["failed_tool_call"], indent=2),
            "",
            "## MCP response from failed call",
            context["mcp_response"][:1000],
            "",
            "## Validation feedback",
            json.dumps(context["validation_verdict"], indent=2),
            "",
            "## Chat history (recent)",
            context["history_summary"],
        ]

        if context["attempts"]:
            parts.append("")
            parts.append("## Previous retry attempts")
            for att in context["attempts"]:
                parts.append(json.dumps(att, indent=2))

        return "\n".join(parts)

    def _parse_response(self, response) -> dict | None:
        if not response.candidates or not response.candidates[0].content.parts:
            print("[RETRY_AGENT] No response from Gemini")
            return None

        text = response.candidates[0].content.parts[0].text or ""
        print(f"[RETRY_AGENT] Raw response: {text[:200]}")

        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)

        try:
            result = json.loads(text.strip())
            return result
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[RETRY_AGENT] JSON parse failed: {e}")
            return None
