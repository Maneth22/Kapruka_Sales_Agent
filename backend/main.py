import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS

from backend.core.config import settings
from backend.core.security import seed_admin
from backend.core.gemini_queue import GeminiRequestQueue
from backend.core.pipeline_queue import PipelineQueue
from backend.mcp_client.client import KaprukaMCPClient
from backend.agents.gemini_agent import GeminiAgent
from backend.routes.auth import auth_bp
from backend.routes.chat import register_socket_handlers

mcp_client = KaprukaMCPClient(settings.mcp_server_url)
gemini_queue = GeminiRequestQueue(max_concurrency=1, min_delay_ms=1000)
agent = GeminiAgent(gemini_queue)
pipeline_queue = PipelineQueue(
    agent,
    max_concurrency=settings.pipeline_max_concurrency,
    pipeline_interval_ms=settings.pipeline_interval_ms,
)

app = Flask(__name__, static_folder=None)
app.config["SECRET_KEY"] = settings.jwt_secret
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

app.register_blueprint(auth_bp)

register_socket_handlers(socketio, pipeline_queue, mcp_client)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


@app.route("/")
@app.route("/<path:path>")
def serve_frontend(path="index.html"):
    file_path = os.path.join(STATIC_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, "index.html")


if __name__ == "__main__":
    seed_admin()
    mcp_client.start()
    print(f"[MAIN] Starting server on {settings.host}:{settings.port}")
    socketio.run(app, host=settings.host, port=settings.port, allow_unsafe_werkzeug=True)
