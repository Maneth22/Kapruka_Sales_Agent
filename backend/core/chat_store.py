import time
from datetime import datetime, timezone

from backend.core.config import settings


_chat_store: dict[str, list[dict]] = {}
_last_activity: dict[str, float] = {}


def get_history(user_id: str) -> list[dict]:
    return _chat_store.get(user_id, [])


def add_message(user_id: str, role: str, content: str):
    msg = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _chat_store.setdefault(user_id, []).append(msg)
    return msg


def clear_history(user_id: str):
    _chat_store.pop(user_id, None)


def update_activity(user_id: str):
    _last_activity[user_id] = time.monotonic()


def get_last_activity(user_id: str) -> float | None:
    return _last_activity.get(user_id)


def remove_activity(user_id: str):
    _last_activity.pop(user_id, None)


def check_session_timeout(user_id: str) -> bool:
    last = _last_activity.get(user_id)
    if last is None:
        return False
    elapsed = time.monotonic() - last
    return elapsed > settings.session_timeout_minutes * 60
