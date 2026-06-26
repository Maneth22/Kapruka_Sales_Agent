import re


def parse_search_products(markdown: str) -> list[dict]:
    products = []
    sep = r'[\xb7\u2022\*]'

    block_pattern = re.compile(
        r'\*\*(\d+)\.\s+(.+?)\*\*\s*\n'
        r'\s+ID:\s*`([^`]+)`\s*'
        rf'{sep}\s*(\w+(?:\s*\w+)?)\s+([\d,]+)'
        r'\s*.*?\n'
        r'\s+\[View product\]\(([^)]+)\)',
        re.MULTILINE,
    )

    for match in block_pattern.finditer(markdown):
        name = match.group(2).strip()
        product_id = match.group(3).strip()
        currency = match.group(4).strip()
        price_raw = match.group(5).strip().replace(",", "")
        url = match.group(6).strip()

        try:
            price = float(price_raw) if price_raw else None
        except ValueError:
            price = None

        block_start = match.start()
        block_end = match.end()
        block_text = markdown[block_start:block_end]

        stock_text = ""
        shipping = ""
        in_stock = True

        after_price = match.group(0)
        line2_match = re.search(
            rf'`[^`]+`\s*{sep}\s*\w+(?:\s*\w+)?\s+[\d,]+\s*{sep}\s*(.+?)\s*{sep}\s*(.*)',
            block_text,
        )
        if line2_match:
            stock_text = line2_match.group(1).strip()
            shipping = line2_match.group(2).strip()
        else:
            rest_match = re.search(r'[\d,]+' + rf'\s*{sep}\s*(.+?)(?:\s*{sep}\s*(.*?))?\s*$', block_text)
            if rest_match:
                stock_text = rest_match.group(1).strip() if rest_match.group(1) else ""
                shipping = rest_match.group(2).strip() if rest_match.lastindex and rest_match.lastindex >= 2 and rest_match.group(2) else ""

        in_stock = "in stock" in stock_text.lower() and "out of stock" not in stock_text.lower()

        products.append({
            "id": product_id,
            "name": name,
            "price": price,
            "currency": currency,
            "in_stock": in_stock,
            "stock_text": stock_text,
            "shipping": shipping,
            "url": url,
            "product_url": url,
        })

    return products


def parse_product_detail(markdown: str) -> dict | None:
    lines = markdown.strip().split("\n")
    if not lines:
        return None

    name = ""
    product_id = ""
    price = None
    currency = "LKR"
    in_stock = True
    stock_text = ""
    image_url = None
    url = ""
    category = ""
    vendor = ""
    description = ""

    for line in lines:
        ls = line.strip()

        if ls.startswith("## ") and not ls.startswith("## Kapruka search"):
            name = ls[3:].strip()

        id_match = re.match(r'\*\*ID\*\*:\s*`([^`]+)`', ls)
        if id_match:
            product_id = id_match.group(1).strip()

        price_match = re.match(r'\*\*Price\*\*:\s*(\w+)\s+([\d,]+)', ls)
        if price_match:
            currency = price_match.group(1).strip()
            price_raw = price_match.group(2).strip().replace(",", "")
            try:
                price = float(price_raw)
            except ValueError:
                price = None

        stock_match = re.match(r'\*\*Stock\*\*:\s*(.+)', ls)
        if stock_match:
            stock_text = stock_match.group(1).strip()
            in_stock = "in stock" in stock_text.lower() and "out of stock" not in stock_text.lower()

        category_match = re.match(r'\*\*Category\*\*:\s*(.+)', ls)
        if category_match:
            category = category_match.group(1).strip()

        vendor_match = re.match(r'\*\*Vendor\*\*:\s*(.+)', ls)
        if vendor_match:
            vendor = vendor_match.group(1).strip()

        image_match = re.match(r'\*\*Image\*\*:\s*(https?://\S+)', ls)
        if image_match:
            image_url = image_match.group(1).strip()

        url_match = re.match(r'\[View on Kapruka\]\(([^)]+)\)', ls)
        if url_match:
            url = url_match.group(1).strip()

    if not product_id:
        return None

    desc_lines = []
    in_desc = False
    for line in lines:
        ls = line.strip()
        if product_id in ls and "Weight" in ls:
            in_desc = True
            parts = ls.split("    ", 2)
            if len(parts) > 2:
                desc_lines.append(parts[2])
            continue
        if in_desc and ls and not ls.startswith("**") and not ls.startswith("[View"):
            desc_lines.append(ls)

    description = " ".join(desc_lines).strip() if desc_lines else ""

    result = {
        "id": product_id,
        "name": name,
        "price": price,
        "currency": currency,
        "in_stock": in_stock,
        "stock_text": stock_text,
        "category": category,
        "vendor": vendor,
        "description": description,
        "url": url,
        "product_url": url,
    }

    if image_url:
        result["_direct_image_url"] = image_url

    return result


def parse_tool_response(tool_name: str, markdown: str):
    if tool_name == "kapruka_search_products":
        return parse_search_products(markdown)
    elif tool_name == "kapruka_get_product":
        detail = parse_product_detail(markdown)
        return [detail] if detail else []
    return []
