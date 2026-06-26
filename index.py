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


