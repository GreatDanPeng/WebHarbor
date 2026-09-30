#!/usr/bin/env python3
"""Scrape USPS.com content pages into structured source_data/pages.json.

Captures the public copy the mirror renders: title, meta description, hero
image, section headings with their paragraphs / bullet lists, and the
content images of each page.

Pages covered: ship/*, manage/*, international/*, help/*, business/* and
the shop money-orders page — the same sections www.usps.com organizes
its Quick Tools and navigation around.

Run from sites/usps:  python3 scripts_dev/scrape_pages.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "source_data" / "pages.json"
BASE = "https://www.usps.com"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}

PAGES = [
    ("ship", "ship/mail-shipping-services.htm"),
    ("ship", "ship/priority-mail.htm"),
    ("ship", "ship/priority-mail-express.htm"),
    ("ship", "ship/ground-advantage.htm"),
    ("ship", "ship/first-class-mail.htm"),
    ("ship", "ship/letters.htm"),
    ("ship", "ship/packages.htm"),
    ("ship", "ship/insurance-extra-services.htm"),
    ("ship", "ship/shipping-restrictions.htm"),
    ("ship", "ship/online-shipping.htm"),
    ("ship", "ship/apo-fpo-dpo.htm"),
    ("ship", "ship/custom-mail.htm"),
    ("ship", "ship/label-broker.htm"),
    ("manage", "manage/forward.htm"),
    ("manage", "manage/forward-premium.htm"),
    ("manage", "manage/hold-mail.htm"),
    ("manage", "manage/po-boxes.htm"),
    ("manage", "manage/package-intercept.htm"),
    ("manage", "manage/informed-delivery.htm"),
    ("manage", "manage/mailboxes.htm"),
    ("manage", "manage/mail-for-deceased.htm"),
    ("international", "international/international-how-to.htm"),
    ("international", "international/preparing-international-shipments.htm"),
    ("international", "international/customs-forms.htm"),
    ("international", "international/shipping-restrictions.htm"),
    ("international", "international/insurance-extra-services.htm"),
    ("international", "international/priority-mail-international.htm"),
    ("international", "international/priority-mail-express-international.htm"),
    ("international", "international/first-class-package-international-service.htm"),
    ("international", "international/money-transfers.htm"),
    ("international", "international/passports.htm"),
    ("international", "international/prepaid-import-duties.htm"),
    ("help", "help/claims.htm"),
    ("help", "help/missing-mail.htm"),
    ("help", "help/refunds.htm"),
    ("help", "help/international-claims.htm"),
    ("help", "help/contact-us.htm"),
    ("business", "business/postage-options.htm"),
    ("business", "business/postage-options-compare.htm"),
    ("business", "business/prices.htm"),
    ("shop", "shop/money-orders.htm"),
    ("help", "holiday/holiday-shipping-dates.htm"),
    ("help", "holiday/holiday-schedule.htm"),
]

ENTITIES = {"&nbsp;": " ", "&amp;": "&", "&quot;": '"', "&#39;": "'",
            "&rsquo;": "\u2019", "&ldquo;": "\u201c", "&rdquo;": "\u201d",
            "&mdash;": "\u2014", "&ndash;": "\u2013", "&reg;": "\u00ae",
            "&trade;": "\u2122", "&hellip;": "\u2026", "&bull;": "\u2022"}


def strip(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    for k, v in ENTITIES.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text).strip()


def decode(fragment: str) -> str:
    text = fragment
    for k, v in ENTITIES.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text).strip()


def extract(html: str) -> dict:
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    meta = re.search(r'name="description" content="([^"]*)"', html)
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>',
                   html, re.S)
    ld_description = None
    ld_image = None
    if ld:
        try:
            obj = json.loads(ld.group(1))
            ent = obj.get("mainEntityOfPage", obj)
            ld_description = ent.get("description")
            ld_image = (ent.get("image") or {}).get("url")
        except (json.JSONDecodeError, AttributeError):
            pass

    # main content: from the first <h1 to the footer
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    headline = decode(h1.group(1)) if h1 else None
    body_html = html
    if h1:
        body_html = html[h1.start():]
    for marker in ('id="global-footer"', 'class="global-footer"',
                   '<footer', 'id="utility-footer"'):
        f = body_html.find(marker)
        if f > 0:
            body_html = body_html[:f]
            break
    body_html = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->",
                       "", body_html, flags=re.S)

    # hero / content images (exclude chrome)
    images = []
    for m in re.finditer(r'<img[^>]*src="([^"]+)"[^>]*>', body_html):
        src = m.group(1)
        if any(c in src for c in ("global-elements", "data:image", "logo",
                                  "sprite", "icon_", "/icons/")):
            continue
        if not re.search(r"\.(jpg|jpeg|png|webp)", src.lower()):
            continue
        alt = re.search(r'alt="([^"]*)"', m.group(0))
        images.append({"src": src, "alt": decode(alt.group(1)) if alt else ""})

    # sections: h2/h3 followed by paragraphs/lists until the next heading
    sections = []
    heads = list(re.finditer(r"<h([23])[^>]*>(.*?)</h\1>", body_html, re.S))
    for idx, m in enumerate(heads):
        end = heads[idx + 1].start() if idx + 1 < len(heads) else len(body_html)
        chunk = body_html[m.end():end]
        paras = [decode(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", chunk, re.S)]
        bullets = [decode(li) for li in re.findall(r"<li[^>]*>(.*?)</li>", chunk, re.S)]
        tables = []
        for t in re.findall(r"<table[^>]*>(.*?)</table>", chunk, re.S):
            rows = []
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
                cells = [decode(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
                if cells and any(cells):
                    rows.append(cells)
            if rows:
                tables.append(rows)
        paras = [p for p in paras if p]
        bullets = [b for b in bullets if b]
        if strip(m.group(2)) and (paras or bullets or tables):
            sections.append({"heading": strip(m.group(2)),
                             "paragraphs": paras[:14],
                             "bullets": bullets[:18],
                             "tables": tables[:6]})
        if len(sections) >= 16:
            break

    # inline lead paragraph before the first h2 (after the h1 subhead)
    lead_m = re.search(r"</h2>\s*(.*?)<h2", body_html, re.S)
    if not lead_m:
        lead_m = re.search(r"</h1>\s*(.*?)<h2", body_html, re.S)
    lead = ""
    if lead_m:
        lead = decode(re.sub(r"<[^>]+>", " ", lead_m.group(1)))[:700]

    return {
        "title": decode(title.group(1)).replace(" | USPS", "") if title else None,
        "meta_description": decode(meta.group(1)) if meta else None,
        "ld_description": ld_description,
        "headline": headline,
        "lead": lead,
        "hero_image": ld_image,
        "images": images,
        "sections": sections,
    }


def main() -> int:
    out = {}
    session = requests.Session()
    session.headers.update(HEADERS)
    for section, path in PAGES:
        url = f"{BASE}/{path}"
        try:
            r = session.get(url, timeout=60)
            if r.status_code != 200:
                print(f"[pages] SKIP {url} -> {r.status_code}", file=sys.stderr)
                continue
            # USPS serves UTF-8; decode explicitly so requests never
            # guesses latin-1 and bakes mojibake into the snapshot
            # (reviewer F-5 root cause)
            html = r.content.decode("utf-8", "replace")
            page = extract(html)
            page["url"] = url
            out[path] = page
            print(f"[pages] {path}: {len(page['sections'])} sections, "
                  f"{len(page['images'])} images, hero={page['hero_image']}")
        except requests.RequestException as exc:
            print(f"[pages] ERROR {url}: {exc}", file=sys.stderr)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"[pages] wrote {OUT}: {len(out)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
