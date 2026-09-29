#!/usr/bin/env python3
"""Download every managed upstream image for the zara mirror.

Reads source_data/*.json (built by build_source_data.py) and fetches the
exact upstream CDN URLs (static.zara.net) the mirror will render, at the
render widths used by the templates: PDP gallery images at w=1024, color
selector thumbs at w=400, campaign posters at w=1400. Produces
static/images/upstream/ + asset_inventory.json (path, bytes, sha256,
source_url for every file). Idempotent: re-running refetches nothing that
already matches its sha256.

Run:  python3 scripts_dev/download_images.py
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
SRC = os.path.join(SITE, "source_data")
IMG_ROOT = os.path.join(SITE, "static", "images", "upstream")
INVENTORY = os.path.join(SITE, "asset_inventory.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

GALLERY_W = 1024
THUMB_W = 400
CAMPAIGN_W = 1400


def load(name):
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        return json.load(f)


def sized(url, width):
    if "{width}" in url:
        return url.replace("{width}", str(width))
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}w={width}"


def fetch(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Referer": "https://www.zara.com/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    return data


def name_for(url, prefix):
    m = re.search(r"/([0-9a-z-]+)(?:/[0-9a-z-]+)?\.jpg", url)
    base = m.group(1) if m else re.sub(r"[^0-9a-z-]+", "-", url.lower())[-60:]
    return f"{prefix}-{base}.jpg"


def main():
    plan = {}   # filename -> source url

    products = load("products.json")["products"]
    for p in products:
        pid = p["seo_product_id"]
        for ci, c in enumerate(p["colors"]):
            if ci == 0:
                for gi, g in enumerate(c["gallery"]):
                    plan[f"p{pid}-gal{gi}.jpg"] = sized(g, GALLERY_W)
            else:
                if c.get("thumb"):
                    plan[f"p{pid}-c{c['id']}-thumb.jpg"] = sized(c["thumb"], THUMB_W)

    home = load("home.json")
    for block in home.get("campaigns", []):
        t = re.sub(r"[^a-z0-9]+", "-", (block.get("title") or "camp").lower()).strip("-")
        for si, s in enumerate(block.get("slides", [])):
            plan[f"home-{t}-{si}.jpg"] = sized(s["poster"], CAMPAIGN_W)

    os.makedirs(IMG_ROOT, exist_ok=True)
    rows = []
    ok = skip = fail = 0
    for fname, url in sorted(plan.items()):
        dest = os.path.join(IMG_ROOT, fname)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            skip += 1
        else:
            try:
                fetch(url, dest)
                ok += 1
                time.sleep(0.05)
            except Exception as e:
                print(f"FAIL {fname} <- {url}: {e}", file=sys.stderr)
                fail += 1
                continue
        data = open(dest, "rb").read()
        rows.append({
            "path": f"static/images/upstream/{fname}",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_url": url,
        })

    inventory = {
        "asset_count": len(rows),
        "assets": rows,
        "schema_version": 1,
    }
    with open(INVENTORY, "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"downloaded {ok}, skipped {skip}, failed {fail}; "
          f"inventory rows: {len(rows)}")


if __name__ == "__main__":
    main()
