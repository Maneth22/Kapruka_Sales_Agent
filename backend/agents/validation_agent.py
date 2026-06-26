import json
import re
from pathlib import Path

from google import genai
from google.genai import types

from backend.core.config import settings
from backend.core.gemini_queue import GeminiRequestQueue


def _load_prompt() -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "validation.md"
    return path.read_text(encoding="utf-8")


class ValidationAgent:
    def __init__(self, queue: GeminiRequestQueue):
        self._model = settings.gemini_model
        self._prompt = _load_prompt()
        self._queue = queue
        print("[VALIDATION] Initialised")

    def validate(
        self, user_request: str, tool_call: dict, mcp_response: str,
        send_agent_output=None,
    ) -> dict:
        print(f"[VALIDATION] validate() - request:{user_request[:80]}... tool:{tool_call.get('tool')}")
        print(f"[VALIDATION] MCP response length: {len(mcp_response)} chars")
        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = (
            f"## Original user request\n{user_request}\n\n"
            f"## Tool call made\n{json.dumps(tool_call, indent=2)}\n\n"
            f"## MCP response\n{mcp_response}"
        )

        config = types.GenerateContentConfig(
            system_instruction=types.Content(
                role="user",
                parts=[types.Part(text=self._prompt)],
            ),
        )

        print("[VALIDATION] Calling Gemini API (via queue)...")
        response = self._queue.execute_with_retry(
            client,
            self._model,
            [types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )],
            config,
        )

        if not response.candidates or not response.candidates[0].content.parts:
            print("[VALIDATION] No response from Gemini")
            return {"satisfied": False, "feedback": "Validation failed", "refined_request": None}

        text = response.candidates[0].content.parts[0].text or ""
        print(f"[VALIDATION] Raw response: {text[:200]}")

        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
            print(f"[VALIDATION] Extracted JSON: {text[:200]}")

        try:
            result = json.loads(text.strip())
            print(f"[VALIDATION] Verdict: satisfied={result.get('satisfied')}, feedback={result.get('feedback','')[:80]}")
            has_refined = result.get("refined_request") is not None
            print(f"[VALIDATION] Has refined_request: {has_refined}")
            return result
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[VALIDATION] JSON parse failed: {e}, fallback to text")
            return {"satisfied": False, "feedback": text, "refined_request": None}
