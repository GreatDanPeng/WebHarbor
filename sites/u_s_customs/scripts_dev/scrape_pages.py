#!/usr/bin/env python3
"""Phase 1: batch scrape of public cbp.gov Drupal pages.

Fetches a fixed list of pages with a real headless Chromium (cbp.gov blocks
plain HTTP clients), saves the full rendered HTML plus extracted main-content
records to scraped_data/pages/.

Run:  python3.11 scrape_pages.py            (all pages; skips already-fetched)
      python3.11 scrape_pages.py --refresh  (re-fetch everything)
"""
import json
import pathlib
import random
import sys
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "scraped_data" / "pages"
OUT.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
BASE = "https://www.cbp.gov"

# (url, slug) — the frozen page set for the mirror snapshot.
PAGES = [
    ("/", "home"),
    ("/travel", "travel"),
    ("/travel/international-visitors", "intl_visitors"),
    ("/travel/international-visitors/esta", "esta"),
    ("/travel/international-visitors/know-before-you-visit", "know_before_you_visit"),
    ("/travel/international-visitors/visa-waiver-program", "vwp"),
    ("/travel/international-visitors/i-94", "i94"),
    ("/travel/trusted-traveler-programs", "ttp"),
    ("/travel/trusted-traveler-programs/global-entry", "global_entry"),
    ("/travel/trusted-traveler-programs/nexus", "nexus"),
    ("/travel/trusted-traveler-programs/sentri", "sentri"),
    ("/travel/trusted-traveler-programs/fast", "fast"),
    ("/travel/trusted-traveler-programs/tsa-precheck", "tsa_precheck"),
    ("/travel/us-citizens", "us_citizens"),
    ("/travel/us-citizens/know-before-you-go", "know_before_you_go"),
    ("/travel/us-citizens/mobile-passport-control", "mpc"),
    ("/travel/us-citizens/canada-mexico-travel", "canada_mexico"),
    ("/travel/advisories-wait-times", "advisories_wait_times"),
    ("/travel/biometrics", "biometrics"),
    ("/trade", "trade"),
    ("/trade/basic-import-export", "basic_import_export"),
    ("/trade/basic-import-export/importing-car", "importing_car"),
    ("/trade/basic-import-export/internet-purchases", "internet_purchases"),
    ("/trade/basic-import-export/importer-exporter-tips", "importer_exporter_tips"),
    ("/trade/priority-issues", "priority_issues"),
    ("/trade/priority-issues/adcvd", "ptl_adcvd"),
    ("/trade/priority-issues/ipr", "ptl_ipr"),
    ("/trade/priority-issues/import-safety", "ptl_import_safety"),
    ("/trade/priority-issues/textiles", "ptl_textiles"),
    ("/trade/priority-issues/quotas", "ptl_quotas"),
    ("/trade/priority-issues/revenue", "ptl_revenue"),
    ("/trade/priority-issues/trade-agreements", "ptl_trade_agreements"),
    ("/trade/automated", "ace"),
    ("/trade/rulings/informed-compliance-publications", "icp"),
    ("/newsroom", "newsroom"),
    ("/newsroom/announcements", "announcements"),
    ("/newsroom/publications/forms", "forms"),
    ("/about/contact", "contact"),
    ("/about", "about"),
    ("/border-security/ports-entry", "ports_entry"),
    ("/contact/ports", "ports_landing"),
]

# States with land border ports of entry (real lookups the mirror serves).
PORT_STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
               "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
               "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
               "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
               "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
               "GU", "MP", "PR", "VI"]


def extract_record(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main") or soup
    title_el = main.select_one("h1")
    title = " ".join(title_el.get_text().split()) if title_el else ""
    # strip scripts/styles for text dump
    for t in main.select("script,style,noscript"):
        t.decompose()
    text = "\n".join(
        ln.strip() for ln in main.get_text("\n").splitlines() if ln.strip())
    # headings outline
    outline = [{"tag": h.name, "text": " ".join(h.get_text().split())}
               for h in main.select("h1,h2,h3,h4") if h.get_text().strip()]
    # links + documents (PDFs)
    links, docs = [], []
    for a in main.select("a[href]"):
        href = a.get("href", "")
        label = " ".join(a.get_text().split())
        if href.startswith("/"):
            href = BASE + href
        if ".pdf" in href.lower() or ".docx" in href.lower() or ".xlsx" in href.lower():
            docs.append({"url": href, "label": label[:120]})
        else:
            links.append({"url": href, "label": label[:120]})
    # images inside main
    images = []
    for im in main.select("img[src]"):
        src = im.get("src", "")
        if src.startswith("/"):
            src = BASE + src
        if src and not src.startswith("data:"):
            images.append({"src": src, "alt": (im.get("alt") or "")[:160]})
    last_mod = ""
    lm = soup.find(string=lambda s: s and s.strip().startswith("Last Modified"))
    if lm:
        last_mod = " ".join(lm.strip().split())
    return {"url": url, "title": title, "text": text,
            "outline": outline, "links": links[:400], "docs": docs,
            "images": images, "last_modified": last_mod[:60]}


def main():
    refresh = "--refresh" in sys.argv
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=UA,
                                  viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        todo = []
        for path, slug in PAGES:
            out_html = OUT / f"{slug}.html"
            out_json = OUT / f"{slug}.json"
            if refresh or not (out_html.exists() and out_json.exists()):
                todo.append((path, slug))
        print(f"[scrape] {len(todo)} of {len(PAGES)} pages to fetch")
        for path, slug in todo:
            url = BASE + path if path != "/" else BASE + "/"
            ok = False
            for attempt in range(4):
                try:
                    r = page.goto(url, wait_until="domcontentloaded",
                                  timeout=45000)
                    page.wait_for_timeout(1800)
                    html = page.content()
                    status = r.status if r else 0
                    if status == 200 and len(html) > 5000:
                        (OUT / f"{slug}.html").write_text(html)
                        (OUT / f"{slug}.json").write_text(
                            json.dumps(extract_record(html, url), indent=1))
                        print(f"[ok] {slug} ({len(html)}B)")
                        ok = True
                        break
                    print(f"[retry {attempt}] {slug} status={status}")
                except Exception as e:
                    print(f"[retry {attempt}] {slug} err={str(e)[:70]}")
                time.sleep(4 + attempt * 4)
            if not ok:
                print(f"[FAIL] {slug} {url}")
            time.sleep(random.uniform(1.2, 2.6))
        browser.close()
    print("[scrape] done")


if __name__ == "__main__":
    main()
