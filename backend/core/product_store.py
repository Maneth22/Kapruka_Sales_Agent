import json
from datetime import datetime, timezone

from backend.core.database import get_connection


def add_search_results(user_id: str, tool_call: dict, raw_response: str, products: list[dict], image_results: list[dict] | None = None):
    conn = get_connection()
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO product_results (user_id, tool_call, raw_response, products, image_results, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, json.dumps(tool_call), raw_response, json.dumps(products), json.dumps(image_results) if image_results else None, ts),
    )
    conn.commit()


def get_search_history(user_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT tool_call, raw_response, products, image_results, timestamp FROM product_results WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    result = []
    for r in rows:
        entry = {
            "tool_call": json.loads(r["tool_call"]),
            "raw_response": r["raw_response"],
            "products": json.loads(r["products"]),
            "image_results": json.loads(r["image_results"]) if r["image_results"] else [],
            "timestamp": r["timestamp"],
        }
        result.append(entry)
    return result


def get_latest_products(user_id: str) -> list[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT products FROM product_results WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    if row is None:
        return []
    return json.loads(row["products"])


def get_latest_image_results(user_id: str) -> list[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT image_results FROM product_results WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    if row is None or not row["image_results"]:
        return []
    return json.loads(row["image_results"])


def format_products_context(user_id: str) -> str:
    conn = get_connection()
    rows = conn.execute(
        "SELECT products FROM product_results WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    if not rows:
        return ""

    parts = []
    for i, r in enumerate(rows):
        products = json.loads(r["products"])
        if not products:
            continue
        lines = []
        for j, p in enumerate(products):
            name = p.get("name", "Unknown")
            pid = p.get("id", "")
            price = p.get("price", "N/A")
            currency = p.get("currency", "LKR")
            url = p.get("url") or p.get("product_url") or ""
            lines.append(f"  {j+1}. [{name}](ID: {pid}) — {price} {currency}")
        if lines:
            parts.append(f"Search result set #{i+1}:\n" + "\n".join(lines))
    return "\n\n".join(parts) if parts else ""


def clear_search_history(user_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM product_results WHERE user_id = ?", (user_id,))
    conn.commit()
