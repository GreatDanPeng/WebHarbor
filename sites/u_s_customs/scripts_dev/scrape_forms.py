#!/usr/bin/env python3
"""Phase 4: CBP forms catalog scrape (paginated view) + PDF downloads.

Run: python3.11 scrape_forms.py
Writes scraped_data/forms/forms.json and raw PDFs to static/forms/upstream/.
"""
import json
import pathlib
import random
import re
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "scraped_data" / "forms"
PDF_DIR = ROOT / "static" / "forms" / "upstream"
OUT.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
BASE = "https://www.cbp.gov"
PAGES = 20  # 5 forms per page × 20 = 97+ entries


def parse_forms(html):
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main")
    forms = []
    for row in main.select(".usa-collection__item"):
        title_el = row.select_one("h3, h2, .usa-collection__heading")
        title = " ".join(title_el.get_text().split()) if title_el else ""
        m = re.search(r"CBP Form (\w+)\s*[-–]?\s*(.*)", title)
        form_number = m.group(1) if m else ""
        form_name = m.group(2).strip(" -–") if m else title
        link = row.select_one("a[href*='.pdf']")
        href = link.get("href") if link else None
        if href and href.startswith("/"):
            href = BASE + href
        date = ""
        dm = re.search(r"([A-Z][a-z]{2})\s+(\d{1,2})\s*\n?\s*(20\d\d)", row.get_text("\n"))
        if dm:
            date = f"{dm.group(1)} {dm.group(2)} {dm.group(3)}"
        desc = " ".join(row.get_text(" ").split())
        forms.append({"title": title, "form_number": form_number,
                      "name": form_name, "pdf": href, "date": date,
                      "raw": desc[:600]})
    return forms


def main():
    all_forms = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=UA,
                                  viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        for n in range(PAGES):
            out = OUT / f"page_{n}.json"
            if out.exists():
                all_forms.extend(json.load(open(out))["forms"])
                continue
            url = f"{BASE}/newsroom/publications/forms?page={n}"
            for attempt in range(4):
                try:
                    r = page.goto(url, wait_until="domcontentloaded",
                                  timeout=45000)
                    page.wait_for_timeout(1500)
                    html = page.content()
                    if (r.status if r else 0) == 200:
                        forms = parse_forms(html)
                        if forms:
                            out.write_text(json.dumps({"url": url,
                                                       "forms": forms}, indent=1))
                            all_forms.extend(forms)
                            print(f"[forms {n}] {len(forms)}")
                            break
                except Exception as e:
                    print(f"[retry {n}.{attempt}] {str(e)[:60]}")
                time.sleep(4 + attempt * 3)
            time.sleep(random.uniform(0.8, 1.5))
        browser.close()
    # dedupe by pdf url/title
    seen = set()
    uniq = []
    for f in all_forms:
        key = f["pdf"] or f["title"]
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    (OUT / "forms.json").write_text(json.dumps(uniq, indent=1))
    print(f"[forms] {len(uniq)} unique forms")


if __name__ == "__main__":
    main()
