from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from backend.core.config import settings
from backend.core.database import get_connection


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def seed_admin():
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO users (username, password_hash) VALUES (?, ?)",
        (settings.admin_username, _hash_password(settings.admin_password)),
    )
    conn.commit()


def register_user(username: str, password: str) -> dict | None:
    conn = get_connection()
    existing = conn.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        return None
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, _hash_password(password)),
    )
    conn.commit()
    return {"username": username}


def authenticate_user(username: str, password: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()
    if not row or not _verify_password(password, row["password_hash"]):
        return None
    return {"username": username}


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None
