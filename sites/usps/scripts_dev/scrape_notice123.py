#!/usr/bin/env python3
"""Scrape the USPS Notice 123 price list (pe.usps.com/text/dmm300/Notice123.htm).

Extracts the retail tables the mirror's Calculate-a-Price tool prices from:

  * domestic: Priority Mail Express / Priority Mail / USPS Ground Advantage /
    Media Mail retail zone grids, First-Class Mail retail single-piece
    letters / flats / postcards, domestic flat-rate options
  * domestic extra services: Certified Mail, Registered Mail, insurance,
    COD, Return Receipt, Signature Confirmation, Certificate of Mailing,
    USPS Tracking, Extended Mail Forwarding
  * domestic PO Box fees (competitive + market-dominant size schedules)
  * international: PMEI / PMI / FCPIS retail group price grids, FCMI retail
    letters / flats / postcards, international flat-rate rows, international
    extra services, and the country price-group directory

Output: source_data/pricing.json (deterministic ordering).

Run from sites/usps:  python3 scripts_dev/scrape_notice123.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "source_data" / "pricing.json"
URL = "https://pe.usps.com/text/dmm300/Notice123.htm"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
}

DASH = re.compile(r"[\u2013-]")


def strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&quot;", '"').replace("&#39;", "'"))
    return re.sub(r"\s+", " ", text).strip()


def money(cell: str) -> float | None:
    cell = strip_tags(cell).replace("$", "").replace(",", "")
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", cell):
        return None
    return float(cell)


def table_rows(html: str) -> list[list[str]]:
    """All <table> bodies -> list of (rows of raw cell html)."""
    out = []
    for table in re.findall(r"<table[^>]*>(.*?)</table>", html, re.S):
        rows = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S):
            rows.append(re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S))
        out.append(rows)
    return out


def headings(html: str) -> list[tuple[int, int, int, str]]:
    return [(m.start(), m.end(), int(m.group(1)), strip_tags(m.group(2)))
            for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", html, re.S)]


def span(hs, i) -> tuple[int, int]:
    """Section i spans from just after its heading to the next heading of
    level <= its own."""
    lo = hs[i][1]
    hi = len(html_cache)
    for pos, _end, level, _text in hs[i + 1:]:
        if level <= hs[i][2]:
            hi = pos
            break
    return lo, hi


html_cache = ""


def find(hs, needle, level=None, after=0, nth=0, exact=False) -> int:
    seen = 0
    for i, (_pos, _end, lvl, text) in enumerate(hs):
        if i < after:
            continue
        hit = (text.strip().lower() == needle.strip().lower() if exact
               else needle.lower() in text.lower())
        if hit and (level is None or lvl == level):
            if seen == nth:
                return i
            seen += 1
    raise KeyError(f"{needle} (level={level}, after={after}, nth={nth})")


def parse_grid(section_html: str) -> list[dict]:
    """Parse weight x column price grids across continuation tables.

    Recognizes header rows whose cells are column keys (zones / price groups,
    possibly ranged like '3-5' or labeled like 'Canada 1') and value rows
    whose first cell is a weight ('1', '3.5', '1-8 oz', ...).
    """
    rates: list[dict] = []
    current_cols: list[str] | None = None
    current_unit: str | None = None
    for rows in table_rows(section_html):
        for cells in rows:
            stripped = [strip_tags(c) for c in cells]
            if not stripped:
                continue
            # header row 1: 'Weight Not Over (lbs.)' + column-set label
            # header row 2: column keys
            if stripped[0].lower().startswith(("weight", "price group")) and len(stripped) >= 2:
                current_cols = None
                head = " ".join(stripped).lower()
                if "oz" in head:
                    current_unit = "oz"
                elif "lb" in head:
                    current_unit = "lb"
                continue
            if current_cols is None and all(re.fullmatch(
                    r"[A-Za-z .()/']*[0-9]+(?:[A-Za-z .()/']|\s)*?(?:[\u2013-]\s*\d+)?\s*[A-Za-z .()/']*", c)
                    for c in stripped if c):
                keys = [c for c in stripped if c]
                if len(keys) >= 4:
                    current_cols = keys
                    continue
            if current_cols is None:
                # continuation header: pure column keys (no label cell)
                keys = [c for c in stripped if c and re.search(r"\d", c)
                        and money(c) is None]
                if len(keys) >= 4 and keys == [c for c in stripped if c]:
                    current_cols = keys
                    continue
            # value row: weight + prices aligned to current_cols
            if current_cols and len(stripped) == len(current_cols) + 1:
                weight_label = stripped[0]
                base = weight_label.lower().replace("over", "").strip()
                is_weight = bool(re.fullmatch(
                    r"\d+(?:\.\d+)?(?:\s*(?:oz\.?|lbs?\.?|lb))?"
                    r"(?:\s*[\u2013-]\s*\d+(?:\.\d+)?)?", base))
                if not is_weight:
                    continue
                band_parts = DASH.split(weight_label) if DASH.search(weight_label) else None
                band = [p for p in (band_parts or []) if p.strip()]
                try:
                    lo = float(re.sub(r"[^0-9.]", "", band[0])) if band else float(
                        re.sub(r"[^0-9.]", "", weight_label))
                    hi = float(re.sub(r"[^0-9.]", "", band[1])) if len(band) > 1 else None
                except ValueError:
                    continue
                for col, cell in zip(current_cols, stripped[1:]):
                    price = money(cell)
                    if price is None:
                        continue
                    # column key: 'Canada 1', '2', '3-5', '1 Canada'...
                    m = re.search(r"(\d+)(?:\s*[\u2013-]\s*(\d+))?", strip_tags(col))
                    if not m:
                        continue
                    g_lo, g_hi = int(m.group(1)), (int(m.group(2)) if m.group(2) else None)
                    unit = current_unit
                    if re.search(r"\boz", weight_label.lower()):
                        unit = "oz"
                    elif re.search(r"\blbs?\b", weight_label.lower()):
                        unit = "lb"
                    rates.append({"weight": lo, "weight_hi": hi, "col": g_lo,
                                   "col_hi": g_hi, "col_label": strip_tags(col),
                                   "price": price, "unit": unit})
    return rates


def parse_single_column(section_html: str, col_label: str) -> list[dict]:
    """Two-column tables: weight ('Weight Not Over ...') + one price column."""
    rates: list[dict] = []
    for rows in table_rows(section_html):
        for cells in rows:
            stripped = [strip_tags(c) for c in cells]
            if len(stripped) != 2:
                continue
            if stripped[0].lower().startswith("weight"):
                continue
            weight = money(stripped[0])
            price = money(stripped[1])
            if weight is not None and price is not None:
                rates.append({"weight": weight, "weight_hi": None, "col": 1,
                              "col_hi": None, "col_label": col_label,
                              "price": price})
    return rates


def parse_flat_rate_table(section_html: str) -> list[dict]:
    """The Flat Rate tables: rows of (label h5) | (size) | (price), with
    service header rows ('Priority Mail Express', 'Priority Mail', ...)."""
    items: list[dict] = []
    service = None
    for rows in table_rows(section_html):
        for cells in rows:
            stripped = [strip_tags(c) for c in cells]
            if not stripped:
                continue
            if len(stripped) == 3 and stripped[1].strip().lower() == "size" and stripped[0]:
                service = stripped[0]
                continue
            if len(stripped) == 3 and money(stripped[2]) is not None:
                items.append({"service": service, "label": stripped[0],
                               "size": stripped[1], "price": money(stripped[2])})
    return items


def parse_label_grid(section_html: str) -> list[dict]:
    """Line-item x group tables (international flat rate): rows are labels,
    columns are price groups."""
    rows_out: list[dict] = []
    current_cols: list[str] | None = None
    for rows in table_rows(section_html):
        for cells in rows:
            stripped = [strip_tags(c) for c in cells]
            if not stripped:
                continue
            if len(stripped) == 2 and stripped[1].lower().startswith("price group"):
                current_cols = None
                continue
            if current_cols is None:
                keys = [c for c in stripped if re.fullmatch(r"\d+", c)]
                if len(keys) >= 4 and keys == [c for c in stripped if c]:
                    current_cols = keys
                    continue
            if current_cols and len(stripped) == len(current_cols) + 1 and money(stripped[1]) is not None:
                for col, cell in zip(current_cols, stripped[1:]):
                    price = money(cell)
                    if price is not None:
                        rows_out.append({"label": stripped[0], "group": int(col),
                                         "price": price})
    return rows_out


def parse_linear(section_html: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for m in re.finditer(
            r"<div[^>]*col-10[^>]*>(.*?)</div>\s*<div[^>]*col-2[^>]*>(.*?)</div>",
            section_html, re.S):
        label = strip_tags(m.group(1)).rstrip(":").strip()
        price = money(m.group(2))
        if price is not None and label:
            out[label] = price
    return out


def parse_pair_tables(section_html: str) -> list[dict]:
    rows_out: list[dict] = []
    for rows in table_rows(section_html):
        for cells in rows:
            stripped = [strip_tags(c) for c in cells]
            if len(stripped) < 2 or not stripped[0]:
                continue
            price = None
            for cell in stripped[1:]:
                if cell and money(cell) is not None:
                    price = money(cell)
                    break
            if price is not None:
                rows_out.append({"label": stripped[0], "price": price})
    return rows_out


def section_rows(hs, i) -> list[dict]:
    lo, hi = span(hs, i)
    return parse_pair_tables(html_cache[lo:hi])


def main() -> int:
    global html_cache
    resp = requests.get(URL, headers=HEADERS, timeout=180)
    resp.raise_for_status()
    html_cache = resp.text
    hs = headings(html_cache)
    data: dict = {"source_url": URL, "currency": "USD"}

    def section_html(i) -> str:
        lo, hi = span(hs, i)
        return html_cache[lo:hi]

    # ---- domestic zone grids ----
    pm = find(hs, "Priority Mail", level=2, exact=True)
    data["priority_mail_retail"] = parse_grid(section_html(pm))
    pme = find(hs, "Priority Mail Express", level=2, exact=True)
    data["priority_mail_express_retail"] = parse_grid(section_html(pme))
    ga = find(hs, "Ground Advantage-Retail", level=2, nth=0)
    data["ground_advantage_retail"] = parse_grid(section_html(ga))
    mm = find(hs, "Media Mail—Retail", level=3, nth=0)
    lo, hi = span(hs, mm)
    data["media_mail_retail"] = parse_single_column(html_cache[lo:hi], "Single-Piece")

    # ---- First-Class Mail retail single-piece (letters stamped/metered,
    #      flats, postcards) ----
    fcm: dict[str, list[dict]] = {}
    fcm_sec = find(hs, "Retail—Single Piece", level=3)
    lo, hi = span(hs, fcm_sec)
    for j, (pos, _e, lvl, text) in enumerate(hs):
        if lo <= pos < hi and lvl == 4 and not any(
                k in text for k in ("EDDM", "Semipostal", "Keys")):
            clean = re.sub(r"\s*\d+(?:,\d+)*$", "", text).strip()
            rows = parse_single_column(section_html(j), clean)
            if not rows:  # postcards: a single flat price cell
                lo2, hi2 = span(hs, j)
                price = None
                for t2 in table_rows(html_cache[lo2:hi2]):
                    for r2 in t2:
                        for c2 in r2:
                            if money(strip_tags(c2)) is not None:
                                price = money(strip_tags(c2))
                                break
                        if price is not None:
                            break
                    if price is not None:
                        break
                if price is not None:
                    rows = [{"weight": 1.0, "weight_hi": None, "col": 1,
                             "col_hi": None, "col_label": clean,
                             "price": price}]
            fcm[clean] = rows
    data["first_class_mail_retail"] = fcm

    # ---- domestic flat rate ----
    fr_dom = find(hs, "Flat Rate—Domestic", level=2)
    data["domestic_flat_rate"] = parse_flat_rate_table(section_html(fr_dom))

    # ---- domestic extra services ----
    extras: dict[str, list[dict]] = {}
    for label in ("Certificate of Mailing", "Certified Mail",
                  "Collect on Delivery", "Insurance", "Return Receipt",
                  "Signature Confirmation", "Registered Mail",
                  "USPS Tracking", "Extended Mail Forwarding",
                  "PO Box Service—Competitive", "PO Box Service—Market Dominant",
                  "Additional Fees and Services"):
        try:
            i = find(hs, label, level=4)
        except KeyError:
            continue
        rows = section_rows(hs, i)
        if rows:
            extras[label] = rows
    # dedupe USPS Tracking / extended sections that repeat
    data["domestic_extra_services"] = extras

    # ---- PO Box fees (nested h5 schedules under the h4 PO Box headings) ----
    po_box: dict[str, list[dict]] = {}
    for label in ("PO Box Service—Competitive", "PO Box Service—Market Dominant"):
        try:
            i = find(hs, label, level=4)
        except KeyError:
            continue
        lo, hi = span(hs, i)
        for j, (pos, _e, lvl, text) in enumerate(hs):
            if lo <= pos < hi and lvl == 5:
                key = (("competitive" if "Competitive" in label else "market_dominant")
                       + ("_6mo" if "Semi-Annual" in text else "_3mo"))
                rows = section_rows(hs, j)
                if rows and key not in po_box:
                    po_box[key] = rows
    data["po_box_fees"] = po_box

    # ---- international grids (retail sections repeat under a second h2 with
    #      'Price Group—Continued' tables — merge both halves) ----
    pmei_rows = []
    for nth in (0, 1):
        try:
            i = find(hs, "Priority Mail Express International", level=2, nth=nth)
        except KeyError:
            continue
        pmei_rows.extend(parse_grid(section_html(i)))
    data["priority_mail_express_intl_retail"] = pmei_rows

    pmi_rows = []
    for nth in (0, 1):
        try:
            i = find(hs, "Priority Mail International", level=2, nth=nth)
        except KeyError:
            continue
        pmi_rows.extend(parse_grid(section_html(i)))
    data["priority_mail_intl_retail"] = pmi_rows

    fcmi: dict[str, list[dict]] = {}
    for label in ("Retail Postcards", "Retail Letters",
                  "Retail Large Envelopes (Flats)"):
        i = find(hs, label, level=5)
        rows = parse_grid(section_html(i))
        if not rows:  # label + price layout (postcards)
            lo, hi = span(hs, i)
            rows = [{"weight": 1.0, "weight_hi": None, "col": 0,
                     "col_hi": None, "col_label": r["label"], "price": r["price"]}
                    for r in parse_pair_tables(html_cache[lo:hi])]
        fcmi[label] = rows
    i = find(hs, "Retail Packages", level=5)
    fcmi["Retail Packages"] = parse_grid(section_html(i))
    data["first_class_intl_retail"] = fcmi

    # ---- international flat rate (label x group tables) ----
    ifr: dict[str, list[dict]] = {}
    ifr_sec = find(hs, "Flat Rate—International", level=2)
    lo, hi = span(hs, ifr_sec)
    after = len([1 for p, _e, _l, _t in hs if p < lo])
    retail = find(hs, "Retail", level=3, after=after)
    rlo, _rhi = span(hs, retail)
    rows = parse_label_grid(html_cache[rlo:hi])
    if rows:
        ifr["Retail"] = rows
    data["international_flat_rate"] = ifr

    # ---- international extra services ----
    intl_extras: dict[str, list[dict]] = {}
    for label in ("International Insurance", "International Registered Mail",
                  "International Return Receipt", "International Certificate of Mailing"):
        try:
            i = find(hs, label, level=4, nth=0)
        except KeyError:
            try:
                i = find(hs, label.replace("International ", ""), level=4, nth=1)
            except KeyError:
                continue
        rows = section_rows(hs, i)
        if rows:
            intl_extras[label] = rows
    data["international_extra_services"] = intl_extras

    # ---- country price groups directory (split across several h2 parts) ----
    countries: list[dict] = []
    for i in [idx for idx, h in enumerate(hs)
              if h[3] == "Country Price Groups" and h[2] == 2]:
        lo, hi = span(hs, i)
        for rows in table_rows(html_cache[lo:hi]):
            for cells in rows:
                stripped = [strip_tags(c) for c in cells]
                if len(stripped) == 10 and stripped[0] and not stripped[0].startswith("Country"):
                    countries.append({
                        "country": stripped[0],
                        "pmei_group": stripped[1], "pmei_max_lbs": stripped[2],
                        "pmei_fre_group": stripped[3],
                        "pmi_group": stripped[4], "pmi_max_lbs": stripped[5],
                        "pmi_frb_group": stripped[6],
                        "fcmi_group": stripped[7], "fcpis_group": stripped[8],
                        "ipa_group": stripped[9],
                    })
    data["country_price_groups"] = countries

    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    summary = {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in data.items()}
    print(f"[notice123] wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(f"[notice123] PM={len(data['priority_mail_retail'])} PME={len(data['priority_mail_express_retail'])} "
          f"GA={len(data['ground_advantage_retail'])} MM={len(data['media_mail_retail'])} "
          f"PMI={len(data['priority_mail_intl_retail'])} PMEI={len(data['priority_mail_express_intl_retail'])} "
          f"countries={len(countries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
