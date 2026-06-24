from flask import Blueprint, request, jsonify

from backend.models.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.core.security import authenticate_user, create_token, register_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"detail": "Invalid JSON body"}), 400
    req = LoginRequest(body.get("username", ""), body.get("password", ""))
    user = authenticate_user(req.username, req.password)
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
    user = register_user(req.username, req.password)
    if not user:
        return jsonify({"detail": "Username already exists"}), 409
    token = create_token(user["username"])
    return jsonify(TokenResponse(access_token=token).to_dict())
