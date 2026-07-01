import time
from datetime import datetime, timezone

from backend.core.config import settings
from backend.core.database import get_connection


_last_activity: dict[str, float] = {}


def get_history(user_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, timestamp FROM messages WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def add_message(user_id: str, role: str, content: str):
    conn = get_connection()
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO messages (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, role, content, ts),
    )
    conn.commit()
    return {"role": role, "content": content, "timestamp": ts}


def clear_history(user_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    conn.commit()


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
