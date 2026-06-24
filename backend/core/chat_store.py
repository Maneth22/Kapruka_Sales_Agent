from datetime import datetime, timezone


_chat_store: dict[str, list[dict]] = {}


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
