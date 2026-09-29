#!/usr/bin/env python3
"""Phase 5: careers.cbp.gov scrape (Salesforce-rendered pages).

Captures the careers homepage, career-path pages, applicant-resources pages,
plus the Featured Jobs / Events blocks they render (real CBP recruitment
data surfaced by the upstream site).

Run: python3.11 scrape_careers.py
Writes scraped_data/careers/<slug>.json
"""
import json
import pathlib
import random
import re
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "scraped_data" / "careers"
OUT.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
BASE = "https://careers.cbp.gov"

PAGES = [
    ("/s/", "home"),
    ("/s/career-paths", "career_paths"),
    ("/s/career-paths/usbp", "usbp"),
    ("/s/career-paths/amo", "amo"),
    ("/s/career-paths/ofo", "ofo"),
    ("/s/career-paths/trade", "trade"),
    ("/s/career-paths/opr", "opr"),
    ("/s/career-paths/mission-ops", "mission_ops"),
    ("/s/career-paths/veterans", "veterans"),
    ("/s/applicant-resources", "applicant_resources"),
    ("/s/applicant-resources/study-guides", "study_guides"),
    ("/s/benefits", "benefits"),
    ("/s/events", "events"),
    ("/s/search-careers", "search_careers"),
]


def extract(html, url):
    soup = BeautifulSoup(html, "lxml")
    for t in soup.select("script,style,noscript"):
        t.decompose()
    text = "\n".join(ln.strip() for ln in soup.get_text("\n").splitlines()
                     if ln.strip())
    title = ""
    if soup.title:
        title = " ".join(soup.title.get_text().split()).replace(" | CBP Careers", "")
    jobs = []
    # Featured Jobs blocks: cards with job title + usajobs link
    for a in soup.select('a[href*="usajobs.gov/job/"]'):
        label = " ".join(a.get_text().split())
        if label and "usajobs.gov/job" not in label.lower():
            jobs.append({"title": label[:140], "url": a.get("href")})
    events = []
    txt = " ".join(text.split())
    # events markers: dates + city + 'Register Now'
    ev_iter = re.finditer(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d\d)\s+(.{3,60}?)\s+(In Person Live Event|National Webinar|Online|Virtual)", txt)
    for m in ev_iter:
        events.append({"date": m.group(1), "event": m.group(2).strip(),
                       "type": m.group(3)})
    images = []
    for im in soup.select("img[src]"):
        src = im.get("src", "")
        if src.startswith("/") and "cbp.gov" in url:
            src = BASE + src
        if src and not src.startswith("data:"):
            images.append({"src": src, "alt": (im.get("alt") or "")[:120]})
    return {"url": url, "title": title, "text": text[:12000],
            "jobs": jobs, "events": events, "images": images}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=UA,
                                  viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        for path, slug in PAGES:
            out = OUT / f"{slug}.json"
            if out.exists():
                continue
            url = BASE + path
            ok = False
            for attempt in range(4):
                try:
                    r = page.goto(url, wait_until="domcontentloaded",
                                  timeout=60000)
                    page.wait_for_timeout(6000)  # Salesforce renders slowly
                    html = page.content()
                    if (r.status if r else 0) == 200 and len(html) > 30000:
                        out.write_text(json.dumps(extract(html, url), indent=1))
                        print(f"[ok] {slug} ({len(html)}B)")
                        ok = True
                        break
                except Exception as e:
                    print(f"[retry {slug}.{attempt}] {str(e)[:60]}")
                time.sleep(5 + attempt * 4)
            if not ok:
                print(f"[FAIL] {slug}")
            time.sleep(random.uniform(1.5, 3.0))
        browser.close()
    print("[careers] done")


if __name__ == "__main__":
    main()
