import json
from pathlib import Path

from google.genai.errors import ServerError as GeminiServerError

from backend.agents.base import BaseAgent
from backend.agents.interaction_agent import InteractionAgent
from backend.agents.request_handler_agent import RequestHandlerAgent
from backend.agents.validation_agent import ValidationAgent
from backend.core.gemini_queue import GeminiRequestQueue

MAX_RETRIES = 2


def _load_system_prompt() -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "system.md"
    return path.read_text(encoding="utf-8")


class GeminiAgent(BaseAgent):
    def __init__(self, queue: GeminiRequestQueue):
        self._system_prompt = _load_system_prompt()
        self._interaction = InteractionAgent(queue)
        self._request_handler = RequestHandlerAgent(queue)
        self._validation = ValidationAgent(queue)
        print("[ORCHESTRATOR] Initialised with 3 sub-agents")

    def process_message(
        self,
        user_message: str,
        history: list[dict],
        mcp_client,
        send_status=None,
        send_agent_output=None,
    ) -> str:
        print(f"\n{'='*60}")
        print(f"[ORCHESTRATOR] Received user message: {user_message[:80]}...")
        print(f"[ORCHESTRATOR] History entries: {len(history)}")

        if send_status:
            send_status("interacting", "Understanding your request...")

        try:
            return self._process(user_message, history, mcp_client, send_status, send_agent_output)
        except GeminiServerError as e:
            print(f"[ORCHESTRATOR] Gemini API error: {e.code} - {e.message[:100]}")
            if send_status:
                send_status("done", "Service temporarily unavailable")
            return (
                "I'm sorry, the AI service is temporarily overloaded. "
                "Please try again in a moment."
            )

    def _process(
        self, user_message, history, mcp_client, send_status, send_agent_output,
    ) -> str:
        print("[ORCHESTRATOR] >> Sending to InteractionAgent.chat()...")
        chat_response = self._interaction.chat(user_message, history, send_agent_output)
        print(f"[ORCHESTRATOR] << InteractionAgent response ({len(chat_response)} chars)")
        if send_agent_output:
            send_agent_output("Conversation Analysis", chat_response, "info")

        requirements = self._extract_requirements(chat_response)
        if requirements is None:
            print("[ORCHESTRATOR] No structured requirements found, returning raw response")
            return chat_response

        print(f"[ORCHESTRATOR] Extracted requirements: {json.dumps(requirements, indent=2)[:200]}...")

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n[ORCHESTRATOR] --- Attempt {attempt}/{MAX_RETRIES} ---")
            if send_status:
                send_status("building_request", f"Building request (attempt {attempt}/{MAX_RETRIES})...")

            req_text = json.dumps(requirements, indent=2)
            print(f"[ORCHESTRATOR] >> Sending to RequestHandlerAgent.build_request()...")
            tool_call = self._request_handler.build_request(req_text, send_agent_output)
            if tool_call is None:
                print("[ORCHESTRATOR] RequestHandlerAgent returned None")
                return self._interaction.explain_limitations(
                    "Could not build a valid request from the requirements.", history
                )

            tool_name = tool_call.get("tool")
            tool_args = tool_call.get("arguments", {})
            tool_call_str = json.dumps(tool_call, indent=2)
            print(f"[ORCHESTRATOR] Tool call: {tool_name}({json.dumps(tool_args)[:150]})")
            if send_agent_output:
                send_agent_output("Request Builder", tool_call_str, "success")

            if send_status:
                detail = tool_name.replace("kapruka_", "").replace("_", " ")
                send_status("searching", f"{detail}... (attempt {attempt}/{MAX_RETRIES})")

            print(f"[ORCHESTRATOR] >> Calling MCP tool: {tool_name}...")
            mcp_response = mcp_client.call_tool(tool_name, tool_args)
            print(f"[ORCHESTRATOR] << MCP response ({len(mcp_response)} chars)")
            print(f"[ORCHESTRATOR] MCP response preview: {mcp_response[:200]}")

            if send_status:
                send_status("validating", f"Checking results (attempt {attempt}/{MAX_RETRIES})...")

            user_req_text = user_message
            if isinstance(requirements, dict):
                user_req_text = json.dumps(requirements, indent=2)

            print(f"[ORCHESTRATOR] >> Sending to ValidationAgent.validate()...")
            verdict = self._validation.validate(
                user_req_text, tool_call, mcp_response, send_agent_output
            )
            verdict_satisfied = verdict.get("satisfied")
            print(f"[ORCHESTRATOR] << Validation verdict: satisfied={verdict_satisfied}")
            print(f"[ORCHESTRATOR]    Feedback: {verdict.get('feedback', '')[:150]}")
            if send_agent_output:
                status = "success" if verdict_satisfied else ("retry" if attempt < MAX_RETRIES else "failure")
                send_agent_output("Validation", json.dumps(verdict, indent=2), status)

            if verdict_satisfied:
                print("[ORCHESTRATOR] Validation PASSED - presenting results")
                if send_status:
                    send_status("done", "Found matching results!")
                final = self._interaction.present_results(mcp_response, history)
                if send_agent_output:
                    send_agent_output("Final Response", final, "success")
                return final

            if attempt < MAX_RETRIES:
                refined = verdict.get("refined_request")
                if refined and isinstance(refined, dict):
                    requirements = refined
                    print(f"[ORCHESTRATOR] Retry with refined request: {json.dumps(refined)[:200]}")
                    if send_status:
                        fb = verdict.get("feedback", "Refining search...")
                        send_status("retrying", f"{fb} (retry {attempt + 1}/{MAX_RETRIES})")
                    continue

            fb = verdict.get("feedback", "Could not find suitable results.")
            print(f"[ORCHESTRATOR] No retry possible, explaining limitations: {fb[:150]}")
            limitation = self._interaction.explain_limitations(fb, history)
            if send_agent_output:
                send_agent_output("Unable to Fulfill", limitation, "failure")
            return limitation

        print("[ORCHESTRATOR] Max retries exhausted")
        limitation = self._interaction.explain_limitations(
            "Could not find suitable results after multiple attempts.", history
        )
        if send_agent_output:
            send_agent_output("Unable to Fulfill", limitation, "failure")
        return limitation

    def _extract_requirements(self, text: str) -> dict | None:
        import re
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except (ValueError, json.JSONDecodeError):
                return None
        return None
