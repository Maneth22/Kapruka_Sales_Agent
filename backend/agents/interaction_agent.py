import json
import re
from pathlib import Path

from google import genai
from google.genai import types

from backend.core.config import settings
from backend.core.gemini_queue import GeminiRequestQueue


def _load_prompt() -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "interaction.md"
    return path.read_text(encoding="utf-8")


class InteractionAgent:
    def __init__(self, queue: GeminiRequestQueue):
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model
        self._prompt = _load_prompt()
        self._queue = queue
        print("[INTERACTION] Initialised")

    def chat(self, user_message: str, history: list[dict]) -> str:
        print(f"[INTERACTION] chat() - history:{len(history)} msgs, user:{user_message[:60]}...")
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])],
            ))
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        ))

        config = types.GenerateContentConfig(
            system_instruction=types.Content(
                role="user",
                parts=[types.Part(text=self._prompt)],
            ),
        )

        print("[INTERACTION] Calling Gemini API (via queue)...")
        response = self._queue.execute_with_retry(self._client, self._model, contents, config)

        if response.candidates and response.candidates[0].content.parts:
            text = response.candidates[0].content.parts[0].text or ""
            print(f"[INTERACTION] Response ({len(text)} chars): {text[:100]}...")
            return text
        print("[INTERACTION] No response from Gemini")
        return ""

    def present_results(self, results: str, history: list[dict]) -> str:
        print(f"[INTERACTION] present_results() - results:{len(results)} chars")
        msg = f"Here are the results from the system. Present them to the customer in a friendly way:\n\n{results}"
        return self.chat(msg, history)

    def explain_limitations(self, feedback: str, history: list[dict]) -> str:
        print(f"[INTERACTION] explain_limitations() - feedback:{feedback[:80]}...")
        msg = f"The system was unable to fulfill the request. Explain this politely to the customer and offer alternatives:\n\n{feedback}"
        return self.chat(msg, history)
