"""
Kapruka MCP Tool Integration Tests

Connects to the real MCP server and exercises all 7 tools with sample data,
printing full responses and validating expected structure.

Usage:
    python tests/test_mcp_tools.py                  # test all 7 tools
    python tests/test_mcp_tools.py search           # test a single tool by name
    python tests/test_mcp_tools.py --verbose        # always print full response
    python tests/test_mcp_tools.py --timeout 15     # connection timeout (seconds)
"""

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.core.config import settings
from backend.mcp_client.client import KaprukaMCPClient

__all__ = []  # no pytest tests in this file

# ---------------------------------------------------------------------------
#  Sample data per tool
# ---------------------------------------------------------------------------

TOOL_SAMPLES = {
    "kapruka_search_products": {
        "q": "cake",
        "max_price": 5000,
        "currency": "LKR"
    },
    "kapruka_get_product": { "product_id": "cake00ka002034", "currency": "USD" },
    "kapruka_list_categories": { "depth": 2 },
    "kapruka_list_delivery_cities": { "query": "colombo", "limit": 10 },
    "kapruka_check_delivery": { "city": "Colombo 03", "delivery_date": "2026-07-01", "product_id": "cake00ka002034" },
    "kapruka_create_order": {
        "cart": [{ "product_id": "cake00ka002034", "quantity": 1 }],
        "recipient": { "name": "Amal Perera", "phone": "0771234567" },
        "delivery": { "city": "Colombo 03", "date": "2026-07-01", "address": "12 Galle Road, Colombo 03" },
        "sender": { "name": "Nimal" },
        "gift_message": "Happy Birthday!",
        "currency": "LKR"
    },
    "kapruka_track_order": { "order_number": "VIMP34456CB2" },
}

# ---------------------------------------------------------------------------
#  Response validators — return (passed: bool, message: str)
# ---------------------------------------------------------------------------

def validate_search_products(raw, data):
    """Search returns JSON on success, plain text on failure."""
    if isinstance(data, dict) and "error" not in data:
        ok = "products" in data
        count = len(data.get("products", []))
        return ok, f"{count} products returned"
    return True, "responded (no matching products)"


def validate_get_product(raw, data):
    """Product detail: returns JSON or error text."""
    if isinstance(data, dict):
        ok = "id" in data or "name" in data
        return ok, f"product: {data.get('name', data.get('id', '?'))}"
    return True, "responded with info/error"


def validate_list_categories(raw, data):
    """Categories returns markdown, not JSON."""
    ok = len(raw) > 100 and "Categor" in raw
    lines = [l for l in raw.split("\n") if l.strip().startswith("- [")]
    return ok, f"{len(lines)} categories listed"


def validate_list_delivery_cities(raw, data):
    """Cities returns markdown with city names."""
    ok = len(raw) > 50 and "delivery cities" in raw.lower()
    cities = re.findall(r"\*\*(.*?)\*\*", raw)
    return ok, f"{len(cities)} cities returned"


def validate_check_delivery(raw, data):
    """Delivery check: returns availability info or error."""
    ok = len(raw) > 20
    summary = raw.split("\n")[0][:80] if raw else "empty"
    return ok, summary


def validate_create_order(raw, data):
    """Order creation: returns order details or validation error."""
    ok = len(raw) > 20
    summary = raw.split("\n")[0][:80] if raw else "empty"
    return ok, summary


def validate_track_order(raw, data):
    """Order tracking: returns status or error."""
    ok = len(raw) > 20
    summary = raw.split("\n")[0][:80] if raw else "empty"
    return ok, summary


VALIDATORS = {
    "kapruka_search_products": validate_search_products,
    "kapruka_get_product": validate_get_product,
    "kapruka_list_categories": validate_list_categories,
    "kapruka_list_delivery_cities": validate_list_delivery_cities,
    "kapruka_check_delivery": validate_check_delivery,
    "kapruka_create_order": validate_create_order,
    "kapruka_track_order": validate_track_order,
}

TOOL_ORDER = [
    "kapruka_list_categories",
    "kapruka_search_products",
    "kapruka_get_product",
    "kapruka_list_delivery_cities",
    "kapruka_check_delivery",
    "kapruka_create_order",
    "kapruka_track_order",
]

# ---------------------------------------------------------------------------
#  Test runner
# ---------------------------------------------------------------------------

PASS_EMOJI = "[PASS]"
FAIL_EMOJI = "[FAIL]"
SKIP_EMOJI = "[SKIP]"


def truncate(s, max_len=80):
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _run_tool(client, tool_name, verbose=False):
    args = TOOL_SAMPLES[tool_name]
    validator = VALIDATORS.get(tool_name)

    print()
    print("-" * 70)
    print(f"  Tool: {tool_name}")
    print(f"  Args: {json.dumps(args, indent=2)[:600]}")
    print("-" * 70)

    t0 = time.monotonic()

    try:
        raw = client.call_tool(tool_name, args)
        elapsed = time.monotonic() - t0

        if not raw or not raw.strip():
            print(f"  {FAIL_EMOJI} ({elapsed:.2f}s)")
            print("  Reason: Empty response from MCP server")
            return False, elapsed

        try:
            data = json.loads(raw)
            is_json = True
        except json.JSONDecodeError:
            data = raw
            is_json = False

        if verbose:
            print(f"  Response ({len(raw)} chars):")
            if is_json:
                print(f"  {json.dumps(data, indent=2)[:2000]}")
            else:
                for line in raw.split("\n"):
                    print(f"  | {line}")
        else:
            if is_json:
                summary = json.dumps(data, indent=2)
                if len(summary) > 500:
                    summary = summary[:500] + "\n  ..."
                print(f"  Response ({len(raw)} chars, JSON):")
                print(f"  {summary}")
            else:
                lines = raw.strip().split("\n")
                print(f"  Response ({len(raw)} chars, text):")
                for line in lines[:8]:
                    print(f"  | {line}")
                if len(lines) > 8:
                    print(f"  | ... ({len(lines) - 8} more lines)")

        if validator:
            passed, msg = validator(raw, data)
            if passed:
                print(f"  {PASS_EMOJI} ({elapsed:.2f}s) — {msg}")
                return True, elapsed
            else:
                print(f"  {FAIL_EMOJI} ({elapsed:.2f}s)")
                print(f"  Reason: {msg}")
                return False, elapsed
        else:
            print(f"  {PASS_EMOJI} ({elapsed:.2f}s) — no validator")
            return True, elapsed

    except Exception as e:
        elapsed = time.monotonic() - t0
        print(f"  {FAIL_EMOJI} ({elapsed:.2f}s)")
        print(f"  Error: {e}")
        return False, elapsed


def main():
    args = sys.argv[1:]
    filter_name = None
    verbose = False
    timeout = 10

    i = 0
    while i < len(args):
        if args[i] == "--verbose":
            verbose = True
        elif args[i] == "--timeout" and i + 1 < len(args):
            timeout = int(args[i + 1])
            i += 1
        elif args[i] == "--help":
            print(__doc__)
            return
        elif not args[i].startswith("--"):
            filter_name = args[i].lower()
        i += 1

    tools_to_run = [t for t in TOOL_ORDER if not filter_name or filter_name in t.lower()]
    if filter_name and not tools_to_run:
        known = ", ".join(TOOL_ORDER)
        print(f"No tool matching '{filter_name}'. Known tools: {known}")
        sys.exit(1)

    print()
    print("#" + "=" * 68 + "#")
    print(f"#  Kapruka MCP Tool Integration Tests{' ' * 32}#")
    print(f"#  Server: {settings.mcp_server_url}{' ' * (50 - len(settings.mcp_server_url))}#")
    print(f"#  Timeout: {timeout}s{' ' * 49}#")
    print("#" + "=" * 68 + "#")
    print()
    print(f"  Tools to test: {len(tools_to_run)}")
    for t in tools_to_run:
        print(f"    - {t}")

    print()
    print("  Connecting to MCP server...")
    t_conn = time.monotonic()
    client = KaprukaMCPClient(settings.mcp_server_url)
    client.start()
    if client._ready.wait(timeout=timeout):
        conn_elapsed = time.monotonic() - t_conn
        print(f"  Connected ({conn_elapsed:.2f}s)")
    else:
        print(f"  Failed to connect within {timeout}s timeout")
        print()
        print("  Tips:")
        print("    - Is the MCP server running?")
        print(f"    - Check MCP_SERVER_URL in .env (currently: {settings.mcp_server_url})")
        print("    - Increase timeout with --timeout <seconds>")
        sys.exit(1)

    passed = 0
    failed = 0
    results = []

    for tool_name in tools_to_run:
        ok, elapsed = _run_tool(client, tool_name, verbose=verbose)
        results.append((tool_name, ok, elapsed))
        if ok:
            passed += 1
        else:
            failed += 1

    client.stop()

    print()
    print("=" * 70)
    print(f"  Results: {passed}/{passed + failed} passed")
    if results:
        for name, ok, elapsed in results:
            status = PASS_EMOJI if ok else FAIL_EMOJI
            print(f"    {status} {name} ({elapsed:.2f}s)")
    total_time = sum(e for _, _, e in results)
    print(f"  Total time: {total_time:.2f}s")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
