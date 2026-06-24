import threading
import time

from google.genai.errors import ServerError as GeminiServerError


class GeminiRequestQueue:
    def __init__(self, max_concurrency: int = 2, min_delay_ms: int = 500):
        self._semaphore = threading.Semaphore(max_concurrency)
        self._min_delay = min_delay_ms / 1000.0
        self._last_request_time = 0.0
        self._lock = threading.Lock()

    def execute(self, client, model: str, contents, config):
        with self._semaphore:
            with self._lock:
                elapsed = time.monotonic() - self._last_request_time
                if elapsed < self._min_delay:
                    time.sleep(self._min_delay - elapsed)
                self._last_request_time = time.monotonic()

            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

    def execute_with_retry(
        self, client, model: str, contents, config,
        max_retries: int = 2, base_delay: float = 2.0,
    ):
        for attempt in range(max_retries + 1):
            try:
                return self.execute(client, model, contents, config)
            except GeminiServerError as e:
                if attempt == max_retries:
                    raise
                if e.code == 503:
                    delay = base_delay * (2 ** attempt)
                    print(f"[GEMINI_Q] 503 on attempt {attempt + 1}/{max_retries + 1}, retrying in {delay}s...")
                elif e.code == 429:
                    delay = base_delay * (2 ** (attempt + 1))
                    print(f"[GEMINI_Q] 429 on attempt {attempt + 1}/{max_retries + 1}, retrying in {delay}s...")
                else:
                    raise
                time.sleep(delay)
