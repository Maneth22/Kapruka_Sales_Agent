import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.image_scraper.image_scraper import scrape_product_image, download_image as download_image_direct
from backend.mcp_client.parsers import parse_tool_response


class ImageService:
    def __init__(self, storage_dir: str):
        self._storage_dir = storage_dir
        os.makedirs(self._storage_dir, exist_ok=True)

    def process_search_response(self, tool_name: str, mcp_response_text: str, timeout_per_item: int = 15) -> list[dict]:
        products = parse_tool_response(tool_name, mcp_response_text)
        if not products:
            return []

        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_map = {}
            for product in products:
                product_id = str(product.get("id", ""))
                if not product_id:
                    continue
                future = executor.submit(
                    self._process_single_product,
                    product, timeout_per_item,
                )
                future_map[future] = product_id

            for future in as_completed(future_map):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"[IMAGE_SERVICE] Error processing product {future_map.get(future, '?')}: {e}")

        return results

    def _process_single_product(self, product: dict, timeout: int) -> dict | None:
        product_id = str(product.get("id", ""))
        if not product_id:
            return None

        direct_image_url = product.get("_direct_image_url")
        product_url = product.get("url") or product.get("product_url") or ""

        image_path = None

        if direct_image_url and (direct_image_url.startswith("http://") or direct_image_url.startswith("https://")):
            image_path = download_image_direct(direct_image_url, self._storage_dir, timeout=timeout)
            if image_path:
                expected = os.path.join(self._storage_dir, f"{product_id}.jpg")
                if image_path != expected and os.path.isfile(image_path):
                    try:
                        os.rename(image_path, expected)
                        image_path = expected
                    except OSError:
                        pass

        if not image_path and product_url and (product_url.startswith("http://") or product_url.startswith("https://")):
            image_path = scrape_product_image(product_url, self._storage_dir, product_id, timeout=timeout)

        if not image_path:
            return None

        enriched = dict(product)
        enriched.pop("_direct_image_url", None)
        enriched["image_url"] = f"/static/images/{os.path.basename(image_path)}"
        return enriched
