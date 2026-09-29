#!/usr/bin/env python3
"""Phase 2: newsroom scrape — media releases list + details + announcements.

Run: python3.11 scrape_news.py
Writes scraped_data/news/{list_page_N.json, releases.json, release_<slug>.json}
"""
import json
import pathlib
import random
import re
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "scraped_data" / "news"
OUT.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
BASE = "https://www.cbp.gov"
LIST_PAGES = 5  # 8 releases per page


def parse_list(html):
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main")
    items = []
    for li in main.select(".usa-collection"):
        a = li.select_one('a[href*="media-release/"]')
        if not a:
            continue
        date_el = li.select_one(".usa-collection__date, time")
        desc_el = li.select_one(".usa-collection__description")
        cat_el = li.select_one(".usa-collection__meta, .usa-tag")
        items.append({
            "title": " ".join(a.get_text().split()),
            "href": a.get("href"),
            "date": " ".join(date_el.get_text().split()) if date_el else "",
            "summary": " ".join(desc_el.get_text().split()) if desc_el else "",
            "category": " ".join(cat_el.get_text().split()) if cat_el else "",
        })
    return items


def parse_release(html, url):
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main")
    h1 = main.select_one("h1")
    for t in main.select("script,style,noscript"):
        t.decompose()
    # body: main content region after title
    text = "\n".join(ln.strip() for ln in main.get_text("\n").splitlines()
                     if ln.strip())
    # structured fields
    date = ""
    m = re.search(r"([A-Z][a-z]+ \d{1,2},? 20\d\d)", text[:600])
    if m:
        date = m.group(1).rstrip(",")
    location = ""
    m2 = re.search(r"^([A-Z][A-Za-z .'-]+[,—-]\s*[A-Z]{2}|WASHINGTON|[A-Z][A-Za-z .'-]+)\s*[–—-]\s*U\.S\.",
                   text[:900])
    if m2:
        location = m2.group(1).strip()
    category = "Local Media Release" if "/local-media-release/" in url else (
        "National Media Release" if "/national-media-release/" in url else "")
    images = []
    for im in main.select("img[src]"):
        src = im.get("src", "")
        if src.startswith("/"):
            src = BASE + src
        if src and not src.startswith("data:"):
            images.append({"src": src, "alt": (im.get("alt") or "")[:160]})
    # contact block
    contact = ""
    m3 = re.search(r"(U\.S\. Customs and Border Protection.*?is the unified.*)",
                   text, re.S)
    if m3:
        contact = " ".join(m3.group(1).split())[:800]
    return {"url": url, "title": " ".join(h1.get_text().split()) if h1 else "",
            "date": date, "location": location, "category": category,
            "text": text[:9000], "images": images, "boilerplate": contact}


def main():
    releases = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=UA,
                                  viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        # 1) list pages
        for n in range(LIST_PAGES):
            url = f"{BASE}/newsroom/media-releases/all?page={n}"
            for attempt in range(4):
                try:
                    r = page.goto(url, wait_until="domcontentloaded",
                                  timeout=45000)
                    page.wait_for_timeout(1800)
                    html = page.content()
                    if (r.status if r else 0) == 200 and len(html) > 20000:
                        items = parse_list(html)
                        (OUT / f"list_page_{n}.json").write_text(
                            json.dumps({"url": url, "items": items}, indent=1))
                        releases.extend(items)
                        print(f"[list {n}] {len(items)} items")
                        break
                except Exception as e:
                    print(f"[retry {n}.{attempt}] {str(e)[:70]}")
                time.sleep(4 + attempt * 4)
            time.sleep(random.uniform(1.2, 2.2))
        # dedupe
        seen = set()
        uniq = []
        for it in releases:
            if it["href"] not in seen:
                seen.add(it["href"])
                uniq.append(it)
        releases = uniq
        print(f"[news] {len(releases)} unique releases")
        # 2) release details
        for it in releases:
            slug = it["href"].rstrip("/").split("/")[-1]
            out = OUT / f"release_{slug}.json"
            if out.exists():
                continue
            url = BASE + it["href"]
            for attempt in range(4):
                try:
                    r = page.goto(url, wait_until="domcontentloaded",
                                  timeout=45000)
                    page.wait_for_timeout(1600)
                    html = page.content()
                    if (r.status if r else 0) == 200 and len(html) > 20000:
                        rec = parse_release(html, url)
                        rec["href"] = it["href"]
                        rec["list_date"] = it.get("date", "")
                        out.write_text(json.dumps(rec, indent=1))
                        print(f"[rel] {slug[:60]} imgs={len(rec['images'])}")
                        break
                except Exception as e:
                    print(f"[retry {slug[:30]}.{attempt}] {str(e)[:70]}")
                time.sleep(4 + attempt * 4)
            time.sleep(random.uniform(1.0, 2.0))
        browser.close()
    (OUT / "releases.json").write_text(json.dumps(releases, indent=1))
    print("[news] done")


if __name__ == "__main__":
    main()
