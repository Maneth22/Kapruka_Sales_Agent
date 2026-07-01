import os
import sys
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
    port: int = int(os.getenv("PORT", "8080"))
    pipeline_max_concurrency: int = int(os.getenv("PIPELINE_MAX_CONCURRENCY", "1"))
    pipeline_interval_ms: int = int(os.getenv("PIPELINE_INTERVAL_MS", "3000"))
    image_storage_dir: str = os.getenv(
        "IMAGE_STORAGE_DIR",
        str(_project_root / "backend" / "static" / "images"),
    )
    image_scrape_timeout: int = int(os.getenv("IMAGE_SCRAPE_TIMEOUT", "15"))
    session_timeout_minutes: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "15"))
    retry_delay_ms: int = int(os.getenv("RETRY_DELAY_MS", "1500"))


settings = Settings()

if settings.jwt_secret == "change-me":
    print("[CONFIG] WARNING: JWT_SECRET is still the default 'change-me' — tokens are trivially forgeable!")
    print("[CONFIG] Set a strong random secret in your .env file before deploying to production.")

if not settings.admin_password:
    print("[CONFIG] WARNING: ADMIN_PASSWORD is empty — admin account will have no password!")
    print("[CONFIG] Set a strong ADMIN_PASSWORD in your .env file before deploying to production.")
    sys.stdout.flush()
