#!/usr/bin/env python3
"""Scrape Individual Country Listings from Postal Explorer (pe.usps.com).

For each country the IMM ICL page carries the real mailing conditions:
prohibitions, restrictions, observations, and per-service rules (price
group, weight limit, customs forms). This captures the directory page
plus a curated world-wide subset of country pages.

Output: source_data/countries.json

Run from sites/usps:  python3 scripts_dev/scrape_countries.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "source_data" / "countries.json"
INDEX_URL = "https://pe.usps.com/text/imm/immiclstg.htm"
BASE = "https://pe.usps.com"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
}

COUNTRIES = [
    "Australia", "Austria", "Bahamas", "Belgium", "Brazil", "Canada",
    "Chile", "China", "Colombia", "Costa Rica", "Czech Republic",
    "Denmark", "Egypt", "Finland", "France", "Germany", "Greece", "India",
    "Indonesia", "Ireland", "Israel", "Italy", "Jamaica", "Japan",
    "Kenya", "Mexico", "Netherlands", "New Zealand", "Nigeria", "Norway",
    "Pakistan", "Peru", "Philippines", "Poland", "Portugal", "Qatar",
    "Russia", "Saudi Arabia", "Singapore", "South Africa",
    "Korea, Republic of", "Spain", "Sweden", "Switzerland", "Taiwan",
    "Thailand", "Turkey", "Ukraine", "United Arab Emirates",
    "United Kingdom of Great Britain and Northern Ireland", "Vietnam",
]

SERVICE_KEYS = {
    "Global Express Guaranteed": "ggx",
    "Priority Mail Express International": "pmei",
    "Priority Mail International": "pmi",
    "First-Class Mail International": "fcmi",
    "First-Class Package International Service": "fcpis",
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


def index_links(html: str) -> dict[str, str]:
    links = {}
    for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>\s*([^<]+?)\s*</a>', html):
        url, name = m.group(1), m.group(2).strip()
        if re.search(r"/text/imm/[a-z]{2}_\d+\.htm$", url):
            links.setdefault(name, url)
    return links


def parse_icl(html: str, country: str) -> dict:
    start = 0
    for m in re.finditer(r"Conditions for Mailing", html):
        window = html[m.start():m.start() + 220]
        if country in strip(window):
            start = m.start()
            break
    # cut at the IMM footer
    for marker in ("List of Exhibits", "was not found", "HELPFUL LINKS"):
        f = html.find(marker, start)
        if f > 0:
            html = html[:f]
            break
    body = html[start:]
    body = re.sub(r"<script.*?</script>", "", body, flags=re.S)

    def section_list(cls: str) -> list[str]:
        """ICL sections are <p class="Prohibitions">Prohibitions (130)</p>
        followed by <p class="P"> paragraphs / <ol><li> lists until the next
        class-paragraph."""
        m = re.search(rf'<p class="{cls}">', body)
        if not m:
            return []
        end = len(body)
        for nxt in ("Prohibitions", "Restrictions", "Observations",
                    "GXG", "EMIbreak", "EMI", "PriorityMail", "CustomForms",
                    "First-ClassMail", "CustomForm") + tuple(SERVICE_KEYS):
            j = body.find(nxt, m.end() + 80)
            if 0 < j < end and f'class="{nxt}' in body[max(0, j - 60):j + 40]:
                end = j
        seg = body[m.end():end]
        seg = re.sub(r"<sup.*?</sup>", "", seg, flags=re.S)
        items = []
        for li in re.findall(r"<li[^>]*>(.*?)</li>", seg, re.S):
            t = strip(li)
            if t:
                items.append(t)
        for p in re.findall(r'<p class="P"[^>]*>(.*?)</p>', seg, re.S):
            t = strip(p)
            if t:
                items.append(t)
        return items

    services = {}
    head_classes = {"GXG": "ggx", "EMI": "pmei", "EMIbreak": "pmei",
                    "PriorityMail": "pmi", "First-ClassMail": "fcmi"}
    head_matches = []
    for cls, svc in head_classes.items():
        for m in re.finditer(rf'<p class="{cls}">(.*?)(?=<p class=)',
                             body, re.S):
            head_matches.append((m.start(), svc, m.group(1)))
    # FCPIS appears as a heading link in some pages
    for m in re.finditer(r"First-Class Package International Service", body):
        if '<a name=' in body[max(0, m.start() - 40):m.start()]:
            head_matches.append((m.start(), "fcpis",
                                 body[m.start():m.start() + 5000]))
    head_matches.sort()
    for idx, (pos, svc, seg) in enumerate(head_matches):
        end = head_matches[idx + 1][0] if idx + 1 < len(head_matches) else len(body)
        chunk = body[pos:end]
        price_group = None
        pg = re.search(r"Price Group\s*:?\s*</?[^>]*>?\s*([0-9]+|n/a)", strip(chunk))
        if pg:
            price_group = pg.group(1)
        weight = None
        wl = re.search(r"Weight Limit:?(?:\s|</?[^>]+>)*([0-9]+(?:\.[0-9]+)?)\s*lbs?",
                       strip(chunk))
        if wl:
            weight = wl.group(1) + " lbs"
        forms = []
        cust_i = chunk.find("Customs Form")
        if cust_i >= 0:
            cseg = chunk[cust_i:]
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", cseg, re.S)
            for row in rows:
                cells = [strip(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
                if (len(cells) >= 2 and cells[0] and len(cells[0]) > 15
                        and not cells[0].startswith(("Articles", "Weight", "Refer"))
                        and "Form" in cells[1]):
                    forms.append(f"{cells[0][:90]} → {cells[1][:150]}")
            if not forms:
                flat = strip(cseg)[:600]
                fm = re.findall(r"PS Form[s]? [0-9]+(?:-[A-Z])?"
                               r"(?:\s*inside PS Form[s]? [0-9]+(?:-[A-Z])?)?"
                               r"(?:\s*\([^)]{0,40}\))?", flat)
                forms = list(dict.fromkeys(fm))[:3]
                lead = re.match(r"Customs Form[s]?\s*(?:Required)?\s*\([^)]*\)\s*"
                                r"([^.]{5,90}?)[:.]?\s*(?=PS Form|Obtain|When|$)", flat)
                if lead and forms:
                    forms = [f"{lead.group(1).strip()}: " + f for f in forms]
        notes = []
        for note in re.findall(r"Note:?(.{10,180})", strip(chunk)):
            notes.append(("Note:" + note).strip())
        rec = {"price_group": price_group, "weight_limit": weight,
               "customs_forms": forms[:3], "notes": notes[:3]}
        if svc not in services or len(rec["notes"]) > len(services[svc]["notes"]):
            services.setdefault(svc, rec)
            if svc != "fcpis":
                services[svc] = rec

    return {
        "prohibitions": section_list("Prohibitions"),
        "restrictions": section_list("Restrictions"),
        "observations": section_list("Observations"),
        "services": services,
    }


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)
    index_html = session.get(INDEX_URL, timeout=60).content.decode("utf-8", "replace")
    links = index_links(index_html)
    print(f"[countries] index has {len(links)} ICL links")

    out = {}
    for name in COUNTRIES:
        url = links.get(name)
        if not url:
            print(f"[countries] MISSING index link for {name}", file=sys.stderr)
            continue
        r = session.get(BASE + url, timeout=60)
        if r.status_code != 200:
            print(f"[countries] SKIP {name} -> {r.status_code}", file=sys.stderr)
            continue
        data = parse_icl(r.content.decode("utf-8", "replace"), name)
        data["source_url"] = BASE + url
        out[name] = data
        print(f"[countries] {name}: {len(data['prohibitions'])} prohibitions, "
              f"{len(data['restrictions'])} restrictions, "
              f"{len(data['observations'])} observations, "
              f"services={sorted(data['services'])}")

    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"[countries] wrote {OUT}: {len(out)} countries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
