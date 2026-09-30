#!/usr/bin/env python3
"""Scrape real products from The Postal Store (store.usps.com) with Playwright.

Captures the stamp categories the store organizes its catalog around, the
product tiles on each category page, and for every product its title, SKU,
price, description and image URLs (the USPS ecp asset CDN).

Output: source_data/store_products.json

Run from sites/usps:  python3 scripts_dev/scrape_store.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "source_data" / "store_products.json"
BASE = "https://store.usps.com"

CATEGORIES = [
    ("stamps-new-releases", "/store/stamps/new-releases"),
    ("stamps-all", "/store/stamps"),
    ("shipping-supplies-priority-mail", "/store/shipping-supplies/priority-mail"),
    ("shipping-supplies-priority-mail-express",
     "/store/shipping-supplies/priority-mail-express"),
    ("cards-envelopes", "/store/cards-envelopes"),
    ("gifts-collectors", "/store/collectors"),
]

EXTRA_PRODUCTS = [
    "/store/product/breast-cancer-research-stamps-S_555304",
    "/store/product/american-icons-oversized-postcards-S_582466",
]


def product_slug(href: str) -> str | None:
    m = re.search(r"/store/product/([^/#?]+)", href or "")
    return m.group(1) if m else None


def scrape_category(page, key: str, path: str) -> list[dict]:
    page.goto(BASE + path, timeout=60000, wait_until="load")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2500)
    # dismiss the occasional marketing overlay
    for sel in ("button:has-text('Accept')", ".close", "[aria-label='Close']"):
        try:
            page.locator(sel).first.click(timeout=1200)
            page.wait_for_timeout(400)
        except Exception:
            pass
    tiles = page.eval_on_selector_all(
        "a[href*='/store/product/']",
        "els => els.map(e => ({href: e.getAttribute('href'),"
        " text: (e.innerText || '').trim().slice(0, 300),"
        " img: (e.querySelector('img') ? (e.querySelector('img').src ||"
        " e.querySelector('img').getAttribute('data-src')) : null)}))")
    products = []
    seen = set()
    for tile in tiles:
        slug = product_slug(tile.get("href") or "")
        if not slug or slug in seen:
            continue
        seen.add(slug)
        entry = {"slug": slug, "category": key}
        img = tile.get("img")
        if img:
            entry["tile_image"] = img
        text = (tile.get("text") or "").split("\n")
        text = [t.strip() for t in text if t.strip()]
        if text:
            entry["tile_text"] = text[:6]
        products.append(entry)
    return products


def scrape_product(page, entry: dict) -> dict:
    page.goto(BASE + "/store/product/" + entry["slug"], timeout=60000,
              wait_until="load")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    html = page.content()
    m = re.search(r'<input id="skuprice_[^"]+" value="([0-9.]+)"', html)
    if m:
        entry["price"] = float(m.group(1))
    m = re.search(r"(?:S|P)_(\d+)", entry["slug"])
    if m:
        entry["sku"] = m.group(1)
    sku_dom = page.locator("text=/^SKU:?\\s*\\d+$/").first
    try:
        sku_text = sku_dom.inner_text(timeout=2000)
        sm = re.search(r"(\d+)", sku_text)
        if sm:
            entry["sku"] = sm.group(1)
    except Exception:
        pass
    h1 = page.locator("h1").first
    try:
        entry["name"] = h1.inner_text().strip()
    except Exception:
        entry["name"] = None
    md = re.search(r'name="description" content="([^"]*)"', html)
    if md:
        entry["description"] = md.group(1)
    images = page.eval_on_selector_all(
        "img",
        "els => els.map(e => (e.currentSrc || e.src || ''))"
        ".filter(u => u.includes('/ecp/asset/images/'))")
    images = sorted(set(u.split("?")[0] for u in images if u))
    entry["images"] = images
    # price fallback from tile
    if "price" not in entry:
        pm = re.search(r"\$([0-9]+\.[0-9]{2})", " ".join(entry.get("tile_text", [])))
        if pm:
            entry["price"] = float(pm.group(1))
    return entry


def main() -> int:
    catalog: dict[str, list[dict]] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        wanted = []
        for key, path in CATEGORIES:
            try:
                products = scrape_category(page, key, path)
            except Exception as exc:
                print(f"[store] category {key} ERROR: {str(exc)[:120]}",
                      file=sys.stderr)
                continue
            catalog[key] = products
            wanted.extend(products)
            print(f"[store] {key}: {len(products)} products")
        for path in EXTRA_PRODUCTS:
            slug = product_slug(path)
            if slug:
                wanted.append({"slug": slug, "category": "featured"})
        # dedupe
        uniq = {}
        for w in wanted:
            uniq.setdefault(w["slug"], w)
        # scrape details (limit per category for a balanced, tractable catalog)
        LIMITS = {"stamps-all": 30, "stamps-new-releases": 20,
                  "shipping-supplies-priority-mail": 12,
                  "shipping-supplies-priority-mail-express": 8,
                  "cards-envelopes": 12, "gifts-collectors": 10}
        counts = {k: 0 for k in LIMITS}
        details = []
        for slug, w in uniq.items():
            cat = w.get("category")
            if cat in LIMITS and counts.get(cat, 99) >= LIMITS[cat]:
                continue
            try:
                details.append(scrape_product(page, dict(w)))
                counts[cat] = counts.get(cat, 0) + 1
                print(f"[store] detail {slug}: ok")
            except Exception as exc:
                print(f"[store] detail {slug} ERROR: {str(exc)[:120]}",
                      file=sys.stderr)
            time.sleep(0.35)
        browser.close()

    out = {"categories": catalog, "products": details}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    priced = [d for d in details if d.get("price")]
    print(f"[store] wrote {OUT}: {len(details)} products "
          f"({len(priced)} with price), {len(catalog)} categories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
