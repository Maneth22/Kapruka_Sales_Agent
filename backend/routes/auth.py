import re

from flask import Blueprint, request, jsonify

from backend.models.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.core.security import authenticate_user, create_token, register_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")


def _validate_credentials(username: str, password: str, require_password: bool = True) -> str | None:
    if not username or not username.strip():
        return "Username is required"
    username = username.strip()
    if len(username) < 3 or len(username) > 50:
        return "Username must be between 3 and 50 characters"
    if not _USERNAME_RE.match(username):
        return "Username can only contain letters, numbers, underscores, dots, and hyphens"
    if require_password:
        if not password:
            return "Password is required"
        if len(password) < 6:
            return "Password must be at least 6 characters"
    return None


@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"detail": "Invalid JSON body"}), 400
    req = LoginRequest(body.get("username", ""), body.get("password", ""))
    err = _validate_credentials(req.username, req.password)
    if err:
        return jsonify({"detail": err}), 422
    user = authenticate_user(req.username.strip(), req.password)
    if not user:
        return jsonify({"detail": "Invalid credentials"}), 401
    token = create_token(user["username"])
    return jsonify(TokenResponse(access_token=token).to_dict())


@auth_bp.route("/register", methods=["POST"])
def register():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"detail": "Invalid JSON body"}), 400
    req = RegisterRequest(body.get("username", ""), body.get("password", ""))
    err = _validate_credentials(req.username, req.password)
    if err:
        return jsonify({"detail": err}), 422
    user = register_user(req.username.strip(), req.password)
    if not user:
        return jsonify({"detail": "Username already exists"}), 409
    token = create_token(user["username"])
    return jsonify(TokenResponse(access_token=token).to_dict())
