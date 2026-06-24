"""
Kapruka Sales Agent - Pipeline Test & Debug Script

Run this to test the full 3-agent pipeline with detailed console output.
All agent logs (prefixed with [ORCHESTRATOR], [INTERACTION], etc.) will print to stdout.

Usage:
    python run_pipeline_test.py "I want to buy a birthday cake under 5000 LKR"
    python run_pipeline_test.py                          # uses default message
    python run_pipeline_test.py --no-mcp                 # skip actual MCP call (use mock)
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.core.config import settings
from backend.agents.gemini_agent import GeminiAgent


class MockMCPClient:
    """A mock MCP client that returns canned responses for testing."""

    def __init__(self):
        self._responses = {
            "kapruka_search_products": json.dumps({
                "products": [
                    {"id": "123", "name": "Chocolate Birthday Cake", "price": 3500, "currency": "LKR", "in_stock": True},
                    {"id": "456", "name": "Vanilla Birthday Cake", "price": 4200, "currency": "LKR", "in_stock": True},
                ],
                "total": 2,
                "page": 1,
            }),
            "kapruka_get_product": json.dumps({
                "id": "123", "name": "Chocolate Birthday Cake",
                "price": 3500, "currency": "LKR", "in_stock": True,
                "description": "A delicious chocolate cake perfect for birthdays.",
                "variants": [{"size": "1kg", "price": 3500}, {"size": "2kg", "price": 6000}],
            }),
            "kapruka_list_categories": json.dumps({
                "categories": [
                    {"name": "Cakes & Flowers", "url": "/cakes-flowers"},
                    {"name": "Electronics", "url": "/electronics"},
                ]
            }),
            "kapruka_check_delivery": json.dumps({
                "available": True,
                "city": "Colombo",
                "delivery_date": "2026-06-15",
                "delivery_charge_lkr": 350,
            }),
            "kapruka_create_order": json.dumps({
                "order_id": "ORD-12345",
                "payment_url": "https://pay.kapruka.com/orders/ORD-12345",
                "status": "pending_payment",
            }),
            "kapruka_track_order": json.dumps({
                "order_number": "ORD-12345",
                "status": "in_transit",
                "estimated_delivery": "2026-06-15",
            }),
            "kapruka_list_delivery_cities": json.dumps({
                "cities": [
                    {"name": "Colombo", "aliases": ["Colombo 1", "Colombo 2"]},
                    {"name": "Kandy", "aliases": ["Mahanuwara"]},
                    {"name": "Galle", "aliases": []},
                ]
            }),
        }

    async def call_tool(self, name: str, arguments: dict | None = None) -> str:
        print(f"\n  [MOCK_MCP] Called: {name}")
        if arguments:
            print(f"  [MOCK_MCP] Args: {json.dumps(arguments)[:150]}")
        response = self._responses.get(name, json.dumps({"error": "Unknown tool"}))
        print(f"  [MOCK_MCP] Response ({len(response)} chars): {response[:200]}...")
        return response


async def send_status(status: str, detail: str = ""):
    """Print status updates (mirrors what would be sent via WebSocket)."""
    print(f"\n  [STATUS] {status}: {detail}")


async def main():
    # Parse args
    args = sys.argv[1:]
    user_message = "I want to buy a birthday cake under 5000 LKR"
    use_mock = True

    i = 0
    while i < len(args):
        if args[i] == "--no-mock":
            use_mock = False
        elif args[i] == "--mock":
            use_mock = True
        elif not args[i].startswith("--"):
            user_message = args[i]
        i += 1

    print("=" * 70)
    print("  KAPRUKA SALES AGENT - PIPELINE TEST")
    print("=" * 70)
    print(f"\n  User message: {user_message}")
    print(f"  Using mock MCP: {use_mock}")
    print(f"  Gemini model: {settings.gemini_model}")
    print(f"\n  Initialising agent...")

    agent = GeminiAgent()
    mcp_client = MockMCPClient() if use_mock else None

    if not use_mock:
        from backend.mcp_client.client import KaprukaMCPClient
        mcp_client = KaprukaMCPClient(settings.mcp_server_url)

    print("\n" + "-" * 70)
    print("  RUNNING PIPELINE")
    print("-" * 70)

    try:
        response = await agent.process_message(
            user_message=user_message,
            history=[],
            mcp_client=mcp_client,
            send_status=send_status,
        )

        print("\n" + "-" * 70)
        print("  FINAL RESPONSE")
        print("-" * 70)
        print(f"\n  {response}")
        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n  [ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
