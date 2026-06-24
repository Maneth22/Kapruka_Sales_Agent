# Kapruka MCP Server

Kapruka is the main E market that we are building the agent it consists of all kinds of products for gifting and buying fo user needs

## MCP Endpoints

1. kapruka_search_products
*  Search the catalog by keyword with category, price range, stock, and sort filters. Pagination capped at 3 pages.

Parameters
- q
- category
- min_price
- max_price
- in_stock_only
- sort
- limit
- cursor
- currency

2. kapruka_get_product
* Full details for any product by ID — name, price, stock, variants, images, shipping, and a direct URL.

Parameters
- product_id
- currency

3. kapruka_list_categories
* Top-level category names with browse URLs — pass any name as the category filter to search.

Parameters
- depth

3. kapruka_list_delivery_cities
* Search Kapruka's delivery network by canonical name or vernacular alias. Returns up to 50 matches per query.

Parameters
- query
- limit

4. kapruka_check_delivery
* Check whether an order can be delivered to a city on a given date, with the flat LKR rate and a perishable warning when the product code is a cake / flower / combo.

Parameters
- city
- delivery_date
- product_id

5. kapruka_create_order
* Create a guest-checkout order and return a click-to-pay URL — no Kapruka account required. Prices are locked for 60 minutes, multi-currency, capped at 30 orders/hr per IP.

Parameters
- cart
- recipient
- delivery
- sender
- gift_message
- currency

6. kapruka_track_order
* Look up status, recipient, items, and timestamped delivery progress for any Kapruka order. Customer reads the order number off their confirmation email or order complete page.

Parameters
- order_number

*Tool Usage Example*
```
import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def main():
    async with streamablehttp_client("https://mcp.kapruka.com/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Wrap arguments in a "params" key
            result = await session.call_tool(
                "kapruka_search_products",
                arguments={
                    "params": {
                        "q": "Kapruka cakes",
                        "category": "",
                        "min_price": 0,
                        "max_price": 10000,
                        "in_stock_only": True,
                        "sort": "relevance",
                        "cursor": "eyJ1IjoiTlE9PSIsInAiOjJ9",
                        "limit": 5,
                        "currency": "LKR", 
                    }
                }
            )
            print(result.content[0].text)

asyncio.run(main())
```