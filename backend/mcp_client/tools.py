from google.genai import types


def _prop(t, description=None, enum=None):
    kwargs = {"type": t, "description": description}
    if enum:
        kwargs["enum"] = enum
    return types.Schema(**kwargs)


def get_tools() -> list[types.Tool]:
    return [
        types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name="kapruka_search_products",
                description="Search the catalog by keyword with category, price range, stock, and sort filters. Pagination capped at 3 pages. returns product IDs, names, prices, and a direct URL.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "q": _prop(types.Type.STRING, "Search query keyword"),
                        "min_price": _prop(types.Type.NUMBER, "Minimum price filter"),
                        "max_price": _prop(types.Type.NUMBER, "Maximum price filter"),
                        "in_stock_only": _prop(types.Type.BOOLEAN, "Filter only in-stock items"),
                        "sort": _prop(types.Type.STRING, "Sort order", ["relevance"]),
                        "limit": _prop(types.Type.INTEGER, "Results per page"),
                        "cursor": _prop(types.Type.STRING, "Pagination cursor"),
                        "currency": _prop(types.Type.STRING, "Currency code (LKR, USD, etc.)"),
                    },
                ),
            ),
            types.FunctionDeclaration(
                name="kapruka_get_product",
                description="Full details for any product by ID — name, price, stock, variants, images, shipping, and a direct URL.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "product_id": _prop(types.Type.STRING, "Product ID"),
                        "currency": _prop(types.Type.STRING, "Currency code"),
                    },
                    required=["product_id"],
                ),
            ),
            types.FunctionDeclaration(
                name="kapruka_list_categories",
                description="Top-level category names with browse URLs — pass any name as the category filter to search.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "depth": _prop(types.Type.INTEGER, "Category depth"),
                    },
                ),
            ),
            types.FunctionDeclaration(
                name="kapruka_list_delivery_cities",
                description="Search Kapruka's delivery network by canonical name or vernacular alias. Returns up to 50 matches per query.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": _prop(types.Type.STRING, "City name or alias to search"),
                        "limit": _prop(types.Type.INTEGER, "Max results"),
                    },
                ),
            ),
            types.FunctionDeclaration(
                name="kapruka_check_delivery",
                description="Check whether an order can be delivered to a city on a given date, with the flat LKR rate and a perishable warning when the product code is a cake / flower / combo.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "city": _prop(types.Type.STRING, "Delivery city name"),
                        "delivery_date": _prop(types.Type.STRING, "Delivery date"),
                        "product_id": _prop(types.Type.STRING, "Product ID to check"),
                    },
                    required=["city", "delivery_date", "product_id"],
                ),
            ),
            types.FunctionDeclaration(
                name="kapruka_create_order",
                description="Create a guest-checkout order and return a click-to-pay URL — no Kapruka account required. Prices are locked for 60 minutes, multi-currency, capped at 30 orders/hr per IP.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "cart": types.Schema(
                            type=types.Type.ARRAY,
                            description="Cart items — each item has product_id (string) and quantity (integer)",
                            items=types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "product_id": types.Schema(type=types.Type.STRING, description="Product ID"),
                                    "quantity": types.Schema(type=types.Type.INTEGER, description="Quantity"),
                                },
                                required=["product_id", "quantity"],
                            ),
                        ),
                        "recipient": types.Schema(
                            type=types.Type.OBJECT,
                            description="Recipient details — name (string, required), phone (string, required), address (string), city (string)",
                            properties={
                                "name": types.Schema(type=types.Type.STRING, description="Recipient name"),
                                "phone": types.Schema(type=types.Type.STRING, description="Recipient phone number"),
                            },
                            required=["name", "phone"],
                        ),
                        "delivery": types.Schema(
                            type=types.Type.OBJECT,
                            description="Delivery details — city (string, required), date (string, required), address (string, required)",
                            properties={
                                "city": types.Schema(type=types.Type.STRING, description="Delivery city"),
                                "date": types.Schema(type=types.Type.STRING, description="Delivery date"),
                                "address": types.Schema(type=types.Type.STRING, description="Delivery address"),
                            },
                            required=["city", "date", "address"],
                        ),
                        "sender": types.Schema(
                            type=types.Type.OBJECT,
                            description="Sender details — name (string, required)",
                            properties={
                                "name": types.Schema(type=types.Type.STRING, description="Sender name"),
                            },
                            required=["name"],
                        ),
                        "gift_message": _prop(types.Type.STRING, "Gift message"),
                        "currency": _prop(types.Type.STRING, "Currency code (LKR, USD, etc.)"),
                    },
                    required=["cart", "recipient", "delivery", "sender"],
                ),
            ),
            types.FunctionDeclaration(
                name="kapruka_track_order",
                description="Look up status, recipient, items, and timestamped delivery progress for any Kapruka order.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "order_number": _prop(types.Type.STRING, "Order number from confirmation email"),
                    },
                    required=["order_number"],
                ),
            ),
        ]),
    ]
