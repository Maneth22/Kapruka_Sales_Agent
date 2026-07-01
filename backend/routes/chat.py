import os

from flask import request, session
from flask_socketio import emit, disconnect

from backend.core.chat_store import (
    get_history,
    add_message,
    clear_history,
    update_activity,
    check_session_timeout,
    remove_activity,
)
from backend.core.product_store import (
    clear_search_history,
    get_search_history,
)
from backend.core.config import settings
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
        update_activity(user_id)

    @socketio.on("disconnect")
    def on_disconnect():
        user_id = session.get("user_id")
        if user_id:
            print(f"[CHAT] SocketIO disconnected for user: {user_id}")

    @socketio.on("heartbeat")
    def on_heartbeat():
        user_id = session.get("user_id")
        if user_id:
            update_activity(user_id)

    @socketio.on("message")
    def on_message(data):
        user_id = session.get("user_id")
        if not user_id:
            emit("message", {"role": "assistant", "content": "Not authenticated"})
            return

        if check_session_timeout(user_id):
            print(f"[CHAT] Session timed out for user: {user_id}")
            remove_activity(user_id)
            emit("session_timeout", {"reason": "Session timed out due to inactivity"})
            disconnect()
            return

        update_activity(user_id)

        user_content = data.get("content", "")
        print(f"\n[CHAT] Received message from {user_id}: {user_content[:80]}")
        add_message(user_id, "user", user_content)

        def send_status(status: str, detail: str = ""):
            print(f"[CHAT] Status [{status}]: {detail[:80]}")
            emit("status", {"status": status, "detail": detail})

        def send_agent_output(label: str, content: str, status: str = "info"):
            print(f"[CHAT] Agent output [{status}] {label}: {content[:80]}...")
            emit("agent_output", {"label": label, "content": content, "status": status})

        last_products = []

        def send_products(products_data: list[dict]):
            nonlocal last_products
            last_products = products_data

        send_status("thinking", "Processing your request...")

        history = get_history(user_id)
        print(f"[CHAT] History has {len(history)} entries")
        response_text = pipeline_queue.process_message(
            user_content, history, mcp_client, send_status, send_agent_output, send_products, user_id
        )

        add_message(user_id, "assistant", response_text)
        print(f"[CHAT] Sending response ({len(response_text)} chars): {response_text[:100]}...")

        payload = {"role": "assistant", "content": response_text}
        if last_products:
            payload["products"] = last_products
        emit("message", payload)

    @socketio.on("clear_history")
    def on_clear_history():
        user_id = session.get("user_id")
        if not user_id:
            emit("message", {"role": "assistant", "content": "Not authenticated"})
            return

        print(f"[CHAT] Clearing history for user: {user_id}")

        search_history = get_search_history(user_id)
        deleted_files = 0
        for entry in search_history:
            for img in entry.get("image_results", []):
                img_url = img.get("image_url", "")
                if img_url.startswith("/static/images/"):
                    filename = os.path.basename(img_url)
                    filepath = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "static", "images", filename,
                    )
                    if os.path.isfile(filepath):
                        try:
                            os.remove(filepath)
                            deleted_files += 1
                        except OSError:
                            pass

        clear_history(user_id)
        clear_search_history(user_id)
        update_activity(user_id)

        print(f"[CHAT] History cleared for {user_id} ({deleted_files} images deleted)")
        emit("history_cleared", {"deleted_images": deleted_files})
