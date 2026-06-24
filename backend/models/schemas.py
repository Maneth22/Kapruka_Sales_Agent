from dataclasses import dataclass


class LoginRequest:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


class RegisterRequest:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


class TokenResponse:
    def __init__(self, access_token: str, token_type: str = "bearer"):
        self.access_token = access_token
        self.token_type = token_type

    def to_dict(self):
        return {"access_token": self.access_token, "token_type": self.token_type}


class WsMessage:
    def __init__(self, type: str, data: dict | None = None):
        self.type = type
        self.data = data or {}
