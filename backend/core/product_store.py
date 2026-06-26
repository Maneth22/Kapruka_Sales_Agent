import json
from datetime import datetime, timezone


_product_store: dict[str, list[dict]] = {}


def add_search_results(user_id: str, tool_call: dict, raw_response: str, products: list[dict], image_results: list[dict] | None = None):
    entry = {
        "tool_call": tool_call,
        "raw_response": raw_response,
        "products": products,
        "image_results": image_results or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _product_store.setdefault(user_id, []).append(entry)
    return entry


def get_search_history(user_id: str) -> list[dict]:
    return _product_store.get(user_id, [])


def get_latest_products(user_id: str) -> list[dict]:
    history = _product_store.get(user_id, [])
    if not history:
        return []
    return history[-1].get("products", [])


def get_latest_image_results(user_id: str) -> list[dict]:
    history = _product_store.get(user_id, [])
    if not history:
        return []
    return history[-1].get("image_results", [])


def format_products_context(user_id: str) -> str:
    history = _product_store.get(user_id, [])
    if not history:
        return ""

    parts = []
    for i, entry in enumerate(history):
        products = entry.get("products", [])
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
    _product_store.pop(user_id, None)
