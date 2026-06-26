from abc import ABC, abstractmethod
from collections.abc import Callable


class BaseAgent(ABC):
    @abstractmethod
    def process_message(
        self,
        user_message: str,
        history: list[dict],
        mcp_client,
        send_status: Callable[[str, str], None] | None = None,
        send_agent_output: Callable[[str, str, str], None] | None = None,
    ) -> str:
        ...
