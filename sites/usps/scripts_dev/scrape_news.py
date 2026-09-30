#!/usr/bin/env python3
"""Scrape real USPS newsroom releases and service alerts (about.usps.com).

The mirror's Latest News panel and Service Alerts section render these
articles: national press releases (2026) with their photos, and the
current retail / residential weather alerts.

Output: source_data/news.json

Run from sites/usps:  python3 scripts_dev/scrape_news.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "source_data" / "news.json"
BASE = "https://about.usps.com"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
}

ENTITIES = {"&nbsp;": " ", "&amp;": "&", "&quot;": '"', "&#39;": "'",
            "&rsquo;": "\u2019", "&ldquo;": "\u201c", "&rdquo;": "\u201d",
            "&mdash;": "\u2014", "&ndash;": "\u2013", "&reg;": "\u00ae",
            "&trade;": "\u2122", "&hellip;": "\u2026", "&bull;": "\u2022"}


def strip(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    for k, v in ENTITIES.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text).strip()


def parse_article(html: str) -> dict:
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    title = strip(m.group(1)) if m else None
    body_html = html
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    if h1:
        body_html = html[h1.end():]
    for marker in ("<footer", 'id="utility-footer"', "Related News"):
        f = body_html.find(marker)
        if f > 0:
            body_html = body_html[:f]
            break
    body_html = re.sub(r"<script.*?</script>|<style.*?</style>", "",
                       body_html, flags=re.S)
    paragraphs = [strip(p) for p in re.findall(r"<p[^>]*>(.*?)</p>",
                                               body_html, re.S)]
    paragraphs = [p for p in paragraphs if len(p) > 2][:28]
    images = []
    for m in re.finditer(r'<img[^>]*src="([^"]+)"[^>]*>', body_html):
        src = m.group(1)
        if src.startswith("/"):
            src = BASE + src
        if any(c in src for c in ("logo", "icon", "sprite", "social")):
            continue
        alt = re.search(r'alt="([^"]*)"', m.group(0))
        if re.search(r"\.(jpg|jpeg|png|webp)", src.lower()):
            images.append({"src": src, "alt": strip(alt.group(1)) if alt else ""})
    date = None
    for pat in (r'"datePublished"\s*:\s*"([^"]+)"',
                r'<meta[^>]*property="article:published_time"[^>]*content="([^"]+)"',
                r'((?:January|February|March|April|May|June|July|August|September'
                r"|October|November|December)\s+\d{1,2},\s+20\d\d)"):
        dm = re.search(pat, html)
        if dm:
            date = dm.group(1)
            break
    return {"title": title, "date": date, "paragraphs": paragraphs,
            "images": images}


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)
    out = {"releases": [], "service_alerts": []}

    index = session.get(f"{BASE}/newsroom/national-releases/2026/data.json",
                         timeout=60)
    if index.status_code == 200:
        try:
            rows = index.json()
        except json.JSONDecodeError:
            rows = []
        rows = sorted(rows, key=lambda r: r.get("date", ""), reverse=True)[:14]
        for row in rows:
            link = row.get("url")
            if not link:
                continue
            r = session.get(BASE + link, timeout=60)
            if r.status_code != 200:
                continue
            # explicit UTF-8 decode (reviewer F-5 root cause)
            art = parse_article(r.content.decode("utf-8", "replace"))
            art["url"] = BASE + link
            art["release_type"] = row.get("release-type")
            art["date"] = row.get("date") or art.get("date")
            out["releases"].append(art)
            print(f"[news] release: {art['title'][:60]} ({art['date']})")
            time.sleep(0.3)

    alerts = session.get(f"{BASE}/newsroom/service-alerts/", timeout=60)
    if alerts.status_code == 200:
        alerts_html = alerts.content.decode("utf-8", "replace")
        links = sorted(set(re.findall(r'href="(/newsroom/service-alerts'
                                      r"/[^\"']+\.htm)", alerts_html)))
        for link in links[:10]:
            r = session.get(BASE + link, timeout=60)
            if r.status_code != 200:
                continue
            art = parse_article(r.content.decode("utf-8", "replace"))
            art["url"] = BASE + link
            out["service_alerts"].append(art)
            print(f"[news] alert: {art['title'][:60]}")
            time.sleep(0.3)

    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"[news] wrote {OUT}: {len(out['releases'])} releases, "
          f"{len(out['service_alerts'])} service alerts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
