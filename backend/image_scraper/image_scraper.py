import os
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


STATE_CLASSES = {
    "active", "inactive", "visible", "hidden", "selected", "current",
    "open", "closed", "expanded", "collapsed", "disabled", "enabled",
    "loaded", "loading",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}


def _fetch_page(url, timeout=15):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException:
        return None


def _extract_img_signature(img_tag):
    return {
        "classes": set(img_tag.get("class", [])),
        "width": img_tag.get("width"),
        "height": img_tag.get("height"),
        "alt": (img_tag.get("alt") or "").lower(),
        "src_path": urlparse(img_tag.get("src", "")).path.lower(),
    }


def _score_img_candidate(img, sig):
    score = 0
    img_classes = set(img.get("class", []))
    common = sig["classes"] & img_classes
    score += len(common) * 3
    if sig["width"] and img.get("width") == sig["width"]:
        score += 2
    if sig["height"] and img.get("height") == sig["height"]:
        score += 2
    src = img.get("src") or img.get("data-src") or ""
    if src:
        path = urlparse(src).path.lower()
        if "product-image" in path:
            score += 2
    img_alt = (img.get("alt") or "").lower()
    if sig["alt"] and sig["alt"] in img_alt:
        score += 1
    return score, src


def _find_image_url_in_html(page_html, selectors=None, sig=None):
    soup = BeautifulSoup(page_html, "lxml")

    if selectors:
        for sel in selectors:
            img = soup.select_one(sel)
            if img:
                src = img.get("src") or img.get("data-src")
                if src:
                    return src

    if sig:
        candidates = []
        for img in soup.find_all("img"):
            score, src = _score_img_candidate(img, sig)
            if src:
                candidates.append((score, src))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_src = candidates[0]
            if best_score > 0:
                return best_src

    best_img = None
    best_area = 0
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if "product" in src.lower() or "image" in src.lower():
            try:
                w = int(img.get("width", 0) or 0)
                h = int(img.get("height", 0) or 0)
                area = w * h
                if area > best_area:
                    best_area = area
                    best_img = src
            except (ValueError, TypeError):
                if not best_img:
                    best_img = src

    return best_img


def _resolve_url(base_url, src):
    if not src:
        return None
    if src.startswith("http://") or src.startswith("https://"):
        return src
    parsed = urlparse(base_url)
    if src.startswith("//"):
        return f"{parsed.scheme}:{src}"
    if src.startswith("/"):
        return f"{parsed.scheme}://{parsed.netloc}{src}"
    base_path = "/".join(parsed.path.rsplit("/", 1)[0]) if "/" in parsed.path else ""
    return f"{parsed.scheme}://{parsed.netloc}{base_path}/{src}"


def get_image_url(page_url, timeout=15):
    html = _fetch_page(page_url, timeout=timeout)
    if not html:
        return None
    src = _find_image_url_in_html(html)
    if src:
        return _resolve_url(page_url, src)
    return None


def download_image(image_url, output_dir, timeout=15):
    os.makedirs(output_dir, exist_ok=True)
    parsed = urlparse(image_url)
    basename = os.path.basename(parsed.path)
    if not basename or "." not in basename:
        basename = "image.jpg"
    name, ext = os.path.splitext(basename)
    if ext.lower() not in IMAGE_EXTENSIONS:
        basename = name + ".jpg"
    dest = os.path.join(output_dir, basename)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(image_url, headers=headers, stream=True, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        return None

    content_type = resp.headers.get("Content-Type", "")
    if "image" not in content_type:
        return None

    with open(dest, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    return os.path.normpath(dest)


def scrape_product_image(product_page_url, storage_dir, product_id, timeout=15):
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', str(product_id))
    filename = f"{sanitized}.jpg"
    dest_path = os.path.join(storage_dir, filename)
    if os.path.isfile(dest_path):
        return dest_path

    image_url = get_image_url(product_page_url, timeout=timeout)
    if not image_url:
        return None

    result = download_image(image_url, storage_dir, timeout=timeout)
    if not result:
        return None

    expected = os.path.normpath(dest_path)
    if result != expected:
        try:
            os.rename(result, dest_path)
        except OSError:
            pass

    if os.path.isfile(dest_path):
        return dest_path
    return result
