#!/usr/bin/env python3
"""Download every upstream image the mirror renders, into static/images/.

Sources, all real upstream URLs the mirror pages use:
  * www.usps.com site chrome (logo, quick-tool icons, hero / featured art)
  * content-page hero images captured in source_data/pages.json
  * The Postal Store product images (store_products.json)
  * newsroom release photos (news.json)
  * ship-page flat rate / packaging art

Output files land in static/images/<group>/; the per-file source map is
written to scraped_data/image_manifest.json (consumed by
build_asset_inventory.py).

Run from sites/usps:  python3 scripts_dev/download_images.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

SITE = Path(__file__).resolve().parents[1]
IMG = SITE / "static" / "images"
MANIFEST = SITE / "scraped_data" / "image_manifest.json"
BASE = "https://www.usps.com"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Referer": "https://www.usps.com/",
}

CHROME = [
    "/global-elements/images/logo-sb.svg",
    "/global-elements/images/logo_mobile.svg",
    "/global-elements/images/tracking.svg",
    "/global-elements/images/location.svg",
    "/global-elements/images/stamps.svg",
    "/global-elements/images/calculate_price.svg",
    "/global-elements/images/schedule_pickup.svg",
    "/global-elements/images/find_zip.svg",
    "/global-elements/images/holdmail.svg",
    "/global-elements/images/change_address.svg",
    "/global-elements/images/po_box.svg",
    "/global-elements/images/free_boxes.svg",
    "/global-elements/images/featured_clicknship.svg",
    "/global-elements/images/mailman.svg",
    "/global-elements/images/transit-time.svg",
    "/global-elements/images/search.svg",
    "/global-elements/images/hs-code-search.svg",
    "/global-elements/images/book-passport-appt.svg",
    "/assets/images/welcome/carousel/pme-supplies-26.jpg",
    "/assets/images/welcome/carousel/sept26-cards.jpg",
    "/assets/images/welcome/carousel/sept26-gifts.jpg",
    "/assets/images/welcome/carousel/sept26-stamps.jpg",
    "/assets/images/welcome/carousel/supplies-boxes-clr.jpg",
    "/assets/images/welcome/featured/cns26-9.jpg",
    "/assets/images/welcome/featured/hold-mail_couple-hugging-after-hiking.jpg",
    "/assets/images/welcome/featured/idapp26-3.jpg",
    "/assets/images/welcome/featured/pp-red-door.jpg",
    "/assets/images/welcome/featured/250-landing-promo.png",
    "/assets/images/welcome/premium/bca26-m.jpg",
    "/assets/images/campaigns/postmark/postmark-home.png",
    "/ship/ship-go-now.png",
    "/store/store-go-now.png",
    "/manage/manage-go-now.png",
    "/business/business-go-now.png",
    "/international/international-go-now.png",
    "/assets/images/home/hamburger.svg",
]

# ship-page art (flat rate boxes / envelopes / service heroes)
SHIP_ART = [
    "/assets/images/ship/mail-ship/hero_pm-image-generic.jpg",
    "/assets/images/ship/mail-ship/hero_pmx-image-generic.jpg",
    "/assets/images/ship/mail-ship/hero_ga-image-generic.jpg",
    "/assets/images/ship/mail-ship/hero_fcm-image-generic.jpg",
    "/assets/images/ship/mail-ship/pm-fr-boxes.jpg",
    "/assets/images/ship/mail-ship/pm-fr-envelope.jpg",
    "/assets/images/ship/mail-ship/pmx-fr-envelope.jpg",
    "/assets/images/ship/mail-ship/pmx-fr-boxes.jpg",
    "/assets/images/ship/mail-ship/ga-hero.jpg",
    "/assets/images/ship/mail-ship/boxes.jpg",
    "/assets/images/ship/mail-ship/envelopes.jpg",
    "/assets/images/ship/mail-ship/insurance.jpg",
    "/assets/images/ship/mail-ship/apo-fpo.jpg",
    "/assets/images/ship/mail-ship/clicknship-hero.jpg",
    "/assets/images/manage/hero_coa.jpg",
    "/assets/images/manage/hero_hm.jpg",
    "/assets/images/manage/hero_pobox.jpg",
    "/assets/images/manage/hero_informed.jpg",
    "/assets/images/manage/hero_intercept.jpg",
    "/assets/images/international/intl_hero.jpg",
    "/assets/images/international/customs-forms.jpg",
    "/assets/images/help/claims_hero.jpg",
    "/assets/images/business/postage_hero.jpg",
    "/assets/images/shop/money-orders_hero.jpg",
    "/assets/images/store/store_hero.jpg",
]


def slugify(url: str) -> str:
    name = url.rsplit("/", 1)[-1].split("?")[0]
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if len(name) > 90:
        stem, ext = name.rsplit(".", 1)
        name = stem[:80] + "." + ext
    return name


def fetch(session, url: str, dest: Path) -> tuple[str, int] | None:
    if dest.exists() and dest.stat().st_size > 0:
        return None
    for attempt in range(3):
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > 100:
                dest.write_bytes(r.content)
                return url, len(r.content)
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(1.2)
    return None


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)
    manifest = []

    def grab(url: str, group: str, label: str = ""):
        if url.startswith("/"):
            url = BASE + url
        if not re.match(r"https?://", url):
            return
        if not re.search(r"\.(png|jpe?g|svg|webp)(\?|$)", url.lower()):
            return
        if any(m["url"] == url for m in manifest):
            return
        dest_dir = IMG / group
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / slugify(url)
        got = fetch(session, url, dest)
        manifest.append({"url": url, "path": f"static/images/{group}/{dest.name}",
                         "label": label})

    for u in CHROME:
        grab(u, "chrome")
    for u in SHIP_ART:
        grab(u, "pages")

    pages = json.loads((SITE / "source_data" / "pages.json").read_text())
    for path, page in pages.items():
        if page.get("hero_image"):
            grab(page["hero_image"], "pages", label=path)
        for img in page.get("images", []):
            grab(img["src"], "pages", label=path)

    store = json.loads((SITE / "source_data" / "store_products.json").read_text())
    for product in store.get("products", []):
        sku = product.get("sku") or product["slug"][:24]
        picked = []
        for img in product.get("images", []):
            if re.search(r"(-00_(?:512|360|520)x\2|-S0\.jpg)".replace(r"\2", r"1")
                         if False else r"(-00_512x512|-00_360x360|-S0)\.jpg$", img):
                picked.append(img)
        # de-dup the same base image at multiple sizes
        bases = {}
        for img in picked:
            base = re.sub(r"(-\d+)?_(?:512x512|360x360|520x520)\.jpg$",
                          ".jpg", img)
            bases.setdefault(base, img)
        for base, img in bases.items():
            ext = ".jpg"
            dest_name = f"store/{slugify(img)}"
            grab(img, "store", label=product.get("name", "")[:60])

    news = json.loads((SITE / "source_data" / "news.json").read_text())
    for i, rel in enumerate(news.get("releases", [])):
        for img in rel.get("images", [])[:2]:
            grab(img["src"], "news", label=rel.get("title", "")[:60])
    for i, alert in enumerate(news.get("service_alerts", [])):
        for img in alert.get("images", [])[:2]:
            grab(img["src"], "news", label=alert.get("title", "")[:60])

    SITE.joinpath("scraped_data").mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    count = sum(1 for p in IMG.rglob("*") if p.is_file() and p.name != ".gitkeep")
    print(f"[images] manifest rows: {len(manifest)}, files on disk: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
