"""
Kapruka MCP — full Python example list
========================================

This calls the Kapruka MCP tools through the Anthropic Messages API's
`mcp_servers` parameter. Claude (model) decides when to invoke a tool based
on your prompt; the actual tool call + result come back as content blocks
of type `mcp_tool_use` / `mcp_tool_result`.

IMPORTANT: Replace MCP_SERVER_URL with the real Kapruka MCP server URL from
your own connector setup — it is not exposed to me in this conversation.

Install:
    pip install anthropic --break-system-packages
"""

import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

MCP_SERVER_URL = "https://REPLACE-ME-kapruka-mcp-url"  # <-- fill in your real URL
MCP_SERVERS = [
    {
        "type": "url",
        "url": MCP_SERVER_URL,
        "name": "kapruka-mcp",
    }
]


def call_with_mcp(prompt: str, max_tokens: int = 1000):
    """Send a prompt that should trigger an MCP tool call, and return the raw response."""
    response = client.beta.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        mcp_servers=MCP_SERVERS,
        messages=[{"role": "user", "content": prompt}],
    )
    return response


def extract_blocks(response):
    """Split a response into text, tool_use, and tool_result blocks."""
    text_blocks = [b.text for b in response.content if b.type == "text"]
    tool_calls = [
        {"name": b.name, "input": b.input}
        for b in response.content
        if b.type == "mcp_tool_use"
    ]
    tool_results = []
    for b in response.content:
        if b.type == "mcp_tool_result":
            raw = b.content[0].text if b.content else ""
            try:
                tool_results.append(json.loads(raw))
            except (json.JSONDecodeError, TypeError):
                tool_results.append(raw)
    return text_blocks, tool_calls, tool_results


# ---------------------------------------------------------------------------
# 1. kapruka_check_delivery
# ---------------------------------------------------------------------------
def example_check_delivery():
    prompt = (
        "Using the Kapruka tools, check if Kapruka can deliver to "
        "'Colombo 03' on 2026-07-01, for product 'cake00ka002034'."
    )
    return call_with_mcp(prompt)


# ---------------------------------------------------------------------------
# 2. kapruka_create_order
# ---------------------------------------------------------------------------
def example_create_order():
    prompt = (
        "Using the Kapruka tools, create an order:\n"
        "- Cart: product_id 'cake00ka002034', quantity 1, icing_text 'Happy Birthday Amal'\n"
        "- Recipient: Amal Perera, phone 0771234567\n"
        "- Delivery: 12 Galle Road, Colombo 03, date 2026-07-01, location_type house, "
        "instructions 'Call on arrival'\n"
        "- Sender: Nimal, not anonymous\n"
        "- Gift message: 'Happy Birthday! Love, Nimal'\n"
        "- Currency: LKR"
    )
    return call_with_mcp(prompt)


# ---------------------------------------------------------------------------
# 3. kapruka_get_product
# ---------------------------------------------------------------------------
def example_get_product():
    prompt = (
        "Using the Kapruka tools, get full product details for product_id "
        "'cake00ka002034' priced in USD."
    )
    return call_with_mcp(prompt)


# ---------------------------------------------------------------------------
# 4. kapruka_list_categories
# ---------------------------------------------------------------------------
def example_list_categories():
    prompt = "Using the Kapruka tools, list product categories with depth 2."
    return call_with_mcp(prompt)


# ---------------------------------------------------------------------------
# 5. kapruka_list_delivery_cities
# ---------------------------------------------------------------------------
def example_list_delivery_cities():
    prompt = "Using the Kapruka tools, list delivery cities matching 'colombo', limit 10."
    return call_with_mcp(prompt)


# ---------------------------------------------------------------------------
# 6. kapruka_search_products
# ---------------------------------------------------------------------------
def example_search_products():
    prompt = (
        "Using the Kapruka tools, search products for 'chocolate cake' in "
        "category 'Cakes', max price 5000 LKR, in stock only, sorted by price "
        "ascending, limit 5."
    )
    return call_with_mcp(prompt)


# ---------------------------------------------------------------------------
# 7. kapruka_track_order
# ---------------------------------------------------------------------------
def example_track_order():
    prompt = "Using the Kapruka tools, track order number 'VIMP34456CB2'."
    return call_with_mcp(prompt)


# ---------------------------------------------------------------------------
# Run all examples
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    examples = {
        "check_delivery": example_check_delivery,
        "create_order": example_create_order,
        "get_product": example_get_product,
        "list_categories": example_list_categories,
        "list_delivery_cities": example_list_delivery_cities,
        "search_products": example_search_products,
        "track_order": example_track_order,
    }

    for name, fn in examples.items():
        print(f"\n=== {name} ===")
        try:
            resp = fn()
            text, calls, results = extract_blocks(resp)
            print("Tool calls:", calls)
            print("Tool results:", results)
            print("Text:", text)
        except Exception as e:
            print(f"Error running {name}: {e}")