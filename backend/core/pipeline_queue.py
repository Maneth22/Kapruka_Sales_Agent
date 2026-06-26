import threading
import time


class PipelineQueue:
    def __init__(self, agent, max_concurrency: int = 1, pipeline_interval_ms: int = 3000):
        self._agent = agent
        self._semaphore = threading.Semaphore(max_concurrency)
        self._min_interval = pipeline_interval_ms / 1000.0
        self._last_pipeline_end = 0.0
        self._lock = threading.Lock()
        print(f"[PIPELINE_Q] Initialised (concurrency={max_concurrency}, interval={pipeline_interval_ms}ms)")

    def process_message(self, user_message, history, mcp_client, send_status=None, send_agent_output=None):
        with self._semaphore:
            with self._lock:
                elapsed = time.monotonic() - self._last_pipeline_end
                if elapsed < self._min_interval:
                    sleep_time = self._min_interval - elapsed
                    print(f"[PIPELINE_Q] Waiting {sleep_time:.1f}s for pipeline interval...")
                    time.sleep(sleep_time)
            try:
                return self._agent.process_message(
                    user_message, history, mcp_client,
                    send_status=send_status,
                    send_agent_output=send_agent_output,
                )
            finally:
                with self._lock:
                    self._last_pipeline_end = time.monotonic()
