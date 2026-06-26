"""Tests for MCP Markdown response parsers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.mcp_client.parsers import parse_search_products, parse_product_detail, parse_tool_response


MID_DOT = "\u00b7"

SEARCH_MD = (
    '## Kapruka search: "cake"\n'
    "Showing 7 results (LKR)\n"
    "\n"
    "**1. Blueberry Bliss Bento Cheesecake**\n"
    f"   ID: `CAKE00KA002034` {MID_DOT} LKR 4,200 {MID_DOT} In stock (low) {MID_DOT} ships internationally\n"
    "   [View product](https://www.kapruka.com/buyonline/blueberry-bliss-bento-cheeseca/kid/cake00ka002034)\n"
    "\n"
    "**2. Blackcherry Velvet Bento Cheesecake**\n"
    f"   ID: `CAKE00KA002035` {MID_DOT} LKR 3,980 {MID_DOT} In stock (low) {MID_DOT} ships internationally\n"
    "   [View product](https://www.kapruka.com/buyonline/blackcherry-velvet-bento-chees/kid/cake00ka002035)\n"
)

DETAIL_MD = (
    "## Blueberry Bliss Bento Cheesecake\n"
    "**ID**: `cake00KA002034`\n"
    "**Price**: LKR 4,200\n"
    "**Stock**: In stock (low)\n"
    "**Category**: cakes\n"
    "**Vendor**: Kapruka Cakes Cake\n"
    "**Weight**: 1.11 lbs\n"
    "**International shipping**: Yes\n"
    "\n"
    "CAKE00KA002034 Weight: 1.11 Lbs (0.5 KG)     Kapruka Cakes Cakes     Indulge in the delicious Blueberry Bliss Bento Cheesecake.\n"
    "\n"
    "**Image**: https://www.kapruka.com/shops/cakes/productImages/zoom/1763114612717_dsc04266.jpg\n"
    "\n"
    "[View on Kapruka](https://www.kapruka.com/buyonline/blueberry-bliss-bento-cheeseca/kid/cake00ka002034)\n"
)


def test_parse_search_products():
    products = parse_search_products(SEARCH_MD)
    assert len(products) == 2, f"Expected 2, got {len(products)}"

    p = products[0]
    assert p["id"] == "CAKE00KA002034", p["id"]
    assert p["name"] == "Blueberry Bliss Bento Cheesecake", p["name"]
    assert p["price"] == 4200.0, p["price"]
    assert p["currency"] == "LKR", p["currency"]
    assert p["in_stock"] is True, f"in_stock is {p['in_stock']}"
    assert "kapruka.com/buyonline/blueberry" in p["url"], p["url"]

    p2 = products[1]
    assert p2["name"] == "Blackcherry Velvet Bento Cheesecake", p2["name"]
    assert p2["price"] == 3980.0, p2["price"]


def test_parse_product_detail():
    detail = parse_product_detail(DETAIL_MD)
    assert detail is not None
    assert detail["id"] == "cake00KA002034", detail["id"]
    assert detail["name"] == "Blueberry Bliss Bento Cheesecake", detail["name"]
    assert detail["price"] == 4200.0, detail["price"]
    assert detail["currency"] == "LKR", detail["currency"]
    assert detail["in_stock"] is True, f"in_stock is {detail['in_stock']}"
    assert detail["category"] == "cakes", detail["category"]
    assert detail["vendor"] == "Kapruka Cakes Cake", detail["vendor"]
    assert "_direct_image_url" in detail, "Missing _direct_image_url"
    assert detail["_direct_image_url"] == "https://www.kapruka.com/shops/cakes/productImages/zoom/1763114612717_dsc04266.jpg"
    assert "kapruka.com/buyonline/blueberry" in detail["url"], detail["url"]


def test_parse_tool_response_search():
    products = parse_tool_response("kapruka_search_products", SEARCH_MD)
    assert len(products) == 2
    assert products[0]["id"] == "CAKE00KA002034"


def test_parse_tool_response_detail():
    products = parse_tool_response("kapruka_get_product", DETAIL_MD)
    assert len(products) == 1
    assert products[0]["id"] == "cake00KA002034"
    assert "_direct_image_url" in products[0]


def test_parse_tool_response_unknown():
    products = parse_tool_response("kapruka_list_categories", "# Categories\n- Cakes")
    assert products == []


def test_parse_real_world_example():
    """Test with the actual format observed from MCP server (with U+00B7 middot)."""
    md = (
        "**1. Blueberry Bliss Bento Cheesecake**\n"
        f"   ID: `CAKE00KA002034` {MID_DOT} LKR 4,200 {MID_DOT} In stock (low) {MID_DOT} ships internationally\n"
        "   [View product](https://www.kapruka.com/buyonline/test)\n"
    )
    products = parse_search_products(md)
    assert len(products) == 1
    assert products[0]["name"] == "Blueberry Bliss Bento Cheesecake"
    assert products[0]["in_stock"] is True


if __name__ == "__main__":
    test_parse_search_products()
    test_parse_product_detail()
    test_parse_tool_response_search()
    test_parse_tool_response_detail()
    test_parse_tool_response_unknown()
    test_parse_real_world_example()
    print("ALL PARSER TESTS PASSED")
