from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from backend.core.config import settings


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


_users_store: dict[str, dict] = {}


def seed_admin():
    _users_store[settings.admin_username] = {
        "username": settings.admin_username,
        "password_hash": _hash_password(settings.admin_password),
    }


def register_user(username: str, password: str) -> dict | None:
    if username in _users_store:
        return None
    _users_store[username] = {
        "username": username,
        "password_hash": _hash_password(password),
    }
    return {"username": username}


def authenticate_user(username: str, password: str) -> dict | None:
    user = _users_store.get(username)
    if not user or not _verify_password(password, user["password_hash"]):
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
