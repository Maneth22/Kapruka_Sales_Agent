import os
from pathlib import Path

from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)


class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "https://mcp.kapruka.com/mcp")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiry_hours: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()
