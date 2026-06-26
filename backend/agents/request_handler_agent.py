import json
import re
from pathlib import Path

from google import genai
from google.genai import types

from backend.core.config import settings
from backend.core.gemini_queue import GeminiRequestQueue


def _load_prompt() -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "request_handler.md"
    return path.read_text(encoding="utf-8")


class RequestHandlerAgent:
    def __init__(self, queue: GeminiRequestQueue):
        self._model = settings.gemini_model
        self._prompt = _load_prompt()
        self._queue = queue
        print("[REQUEST_HANDLER] Initialised")

    def build_request(self, requirements: str, send_agent_output=None) -> dict | None:
        print(f"[REQUEST_HANDLER] build_request() - input:{requirements[:150]}...")
        client = genai.Client(api_key=settings.gemini_api_key)
        config = types.GenerateContentConfig(
            system_instruction=types.Content(
                role="user",
                parts=[types.Part(text=self._prompt)],
            ),
        )

        print("[REQUEST_HANDLER] Calling Gemini API (via queue)...")
        response = self._queue.execute_with_retry(
            client,
            self._model,
            [types.Content(
                role="user",
                parts=[types.Part(text=requirements)],
            )],
            config,
        )

        if not response.candidates or not response.candidates[0].content.parts:
            print("[REQUEST_HANDLER] No response from Gemini")
            return None

        text = response.candidates[0].content.parts[0].text or ""
        print(f"[REQUEST_HANDLER] Raw response: {text[:200]}")

        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
            print(f"[REQUEST_HANDLER] Extracted JSON block: {text[:200]}")

        try:
            result = json.loads(text.strip())
            print(f"[REQUEST_HANDLER] Parsed tool call: {json.dumps(result)[:200]}")
            return result
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[REQUEST_HANDLER] JSON parse failed: {e}")
            return None
