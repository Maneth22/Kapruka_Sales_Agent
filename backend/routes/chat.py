from flask import request, session
from flask_socketio import emit

from backend.core.chat_store import get_history, add_message
from backend.core.security import verify_token


def register_socket_handlers(socketio, pipeline_queue, mcp_client):
    @socketio.on("connect")
    def on_connect():
        token = request.args.get("token")
        user_id = verify_token(token)
        if not user_id:
            print(f"[CHAT] SocketIO rejected: invalid token")
            return False
        print(f"[CHAT] SocketIO accepted for user: {user_id}")
        session["user_id"] = user_id

    @socketio.on("message")
    def on_message(data):
        user_id = session.get("user_id")
        if not user_id:
            emit("message", {"role": "assistant", "content": "Not authenticated"})
            return

        user_content = data.get("content", "")
        print(f"\n[CHAT] Received message from {user_id}: {user_content[:80]}")
        add_message(user_id, "user", user_content)

        def send_status(status: str, detail: str = ""):
            print(f"[CHAT] Status [{status}]: {detail[:80]}")
            emit("status", {"status": status, "detail": detail})

        def send_agent_output(label: str, content: str, status: str = "info"):
            print(f"[CHAT] Agent output [{status}] {label}: {content[:80]}...")
            emit("agent_output", {"label": label, "content": content, "status": status})

        def send_products(products_data: list[dict]):
            print(f"[CHAT] Emitting {len(products_data)} products with images")
            emit("products", {"products": products_data})

        send_status("thinking", "Processing your request...")

        history = get_history(user_id)
        print(f"[CHAT] History has {len(history)} entries")
        response_text = pipeline_queue.process_message(
            user_content, history, mcp_client, send_status, send_agent_output, send_products, user_id
        )

        add_message(user_id, "assistant", response_text)
        print(f"[CHAT] Sending response ({len(response_text)} chars): {response_text[:100]}...")

        emit("message", {"role": "assistant", "content": response_text})
