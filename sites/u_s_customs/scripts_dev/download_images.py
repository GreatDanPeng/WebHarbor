#!/usr/bin/env python3
"""Phase 8: download every upstream image referenced by the scraped pages.

Real upstream media only: each file is fetched from the resolved URL the
live pages render, through a real headless Chromium (cbp.gov's CDN blocks
plain HTTP clients), saved under static/images/upstream/ and recorded in
scraped_data/image_manifest.json (sha256 + source URL + alt text + which
records use it). Ad/analytics pixels are excluded.

Run: python3.11 download_images.py
"""
import hashlib
import json
import pathlib
import re
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "static" / "images" / "upstream"
IMG_DIR.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "scraped_data" / "image_manifest.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CBP = "https://www.cbp.gov"

EXCLUDE = ("adnxs.com", "analytics.twitter", "t.co/1/i/adsct",
           "google-analytics", "doubleclick", "googletagmanager",
           "facebook.com/tr", "dap.digitalgov", "c.go-mpulse",
           "cloudflare", "scorecardresearch", "moatads", "star.gif",
           "pixel", "beacon", "adsct")


def collect():
    entries = []

    def add(src, alt, used_by):
        if not src or any(x in src for x in EXCLUDE):
            return
        src = re.sub(r"\?itok=[A-Za-z0-9_-]+$", "", src)
        if src.startswith("/"):
            src = CBP + src
        entries.append({"url": src, "alt": (alt or "")[:200],
                        "used_by": used_by})

    pages = ROOT / "scraped_data" / "pages"
    for f in pages.glob("*.json"):
        d = json.load(open(f))
        for im in d.get("images", []):
            add(im["src"], im.get("alt"), f"page:{f.stem}")
    for f in (ROOT / "scraped_data" / "news").glob("release_*.json"):
        d = json.load(open(f))
        for im in d.get("images", []):
            add(im["src"], im.get("alt"), f"release:{f.stem}")
    for f in (ROOT / "scraped_data" / "careers").glob("*.json"):
        d = json.load(open(f))
        for im in d.get("images", []):
            add(im["src"], im.get("alt"), f"careers:{f.stem}")
    # theme chrome from the raw home page
    home = (ROOT / "scraped_data" / "pages" / "home.html")
    if home.exists():
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(home.read_text(), "lxml")
        for im in soup.select("img[src]"):
            add(im.get("src"), im.get("alt"), "chrome")
    seen = {}
    for e in entries:
        seen.setdefault(e["url"], e)
    return sorted(seen.values(), key=lambda e: e["url"])


def filename_for(url, idx):
    tail = url.split("?")[0].rstrip("/").split("/")[-1]
    tail = urllib.request.unquote(tail)
    tail = re.sub(r"[^A-Za-z0-9._-]", "_", tail)[:120]
    m = re.search(r"\.(png|jpe?g|gif|webp|svg)$", tail, re.I)
    ext = m.group(1).lower() if m else None
    if not ext:
        return None
    stem = re.sub(r"\.(png|jpe?g|gif|webp|svg)$", "", tail, flags=re.I)
    stem = re.sub(r"\.webp$", "", stem)
    return f"{idx:04d}_{stem}.{ext}"


def main():
    entries = collect()
    print(f"[imgs] {len(entries)} unique upstream images")
    manifest = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=UA,
                                  viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        # warm up a cbp.gov session so the CDN cookies/TLS are established
        try:
            page.goto(CBP + "/", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print("[warmup] err", str(e)[:60])
        for idx, e in enumerate(entries):
            name = filename_for(e["url"], idx)
            if not name:
                continue
            path = IMG_DIR / name
            if path.exists():
                data = path.read_bytes()
            else:
                data = None
                for attempt in range(3):
                    try:
                        r = page.goto(e["url"], wait_until="commit",
                                      timeout=30000)
                        page.wait_for_timeout(600)
                        if r and r.status == 200:
                            data = r.body()
                            if len(data) < 300:
                                data = None
                            break
                        print(f"[{r.status if r else '?'}] {e['url'][-60:]}")
                    except Exception as ex:
                        print(f"[retry {idx}.{attempt}] {str(ex)[:60]}")
                    time.sleep(2 + attempt * 3)
                if not data:
                    print(f"[FAIL] {e['url'][:100]}")
                    continue
                path.write_bytes(data)
                time.sleep(0.25)
            sha = hashlib.sha256(data).hexdigest()
            manifest.append({"file": f"static/images/upstream/{name}",
                             "url": e["url"], "sha256": sha,
                             "bytes": len(data), "alt": e["alt"],
                             "used_by": e["used_by"]})
        browser.close()
    OUT.write_text(json.dumps(manifest, indent=1))
    print(f"[imgs] {len(manifest)} files on disk")


if __name__ == "__main__":
    main()
