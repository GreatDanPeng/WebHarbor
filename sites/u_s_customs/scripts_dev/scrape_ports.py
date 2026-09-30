#!/usr/bin/env python3
"""Phase 3: ports of entry scrape — state directory pages + port details.

Run: python3.11 scrape_ports.py
Writes scraped_data/ports/{state_<ST>.json, port_<slug>.json, index.json}

State tables list every port (name, address, field office). Port detail pages
are fetched for the land-border states plus selected major seaports/airports
so the mirror's port-lookup feature carries real addresses, phone numbers,
hours and facilities.
"""
import json
import pathlib
import random
import re
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "scraped_data" / "ports"
OUT.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
BASE = "https://www.cbp.gov"

STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
          "GU", "MP", "PR", "VI"]

# States whose ports get full detail pages (land borders + major gateways).
DETAIL_STATES = {"AK", "AZ", "CA", "ID", "ME", "MI", "MN", "MT", "ND",
                 "NH", "NM", "NY", "TX", "VT", "WA", "FL", "IL", "MA", "GA", "LA"}


def parse_state_page(html, state):
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main")
    ports = []
    table = main.select_one("table")
    if not table:
        return ports
    for row in table.select("tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) < 3:
            continue
        # header row carries "Port Name"
        if "Port Name" in cells[0].get_text():
            continue
        link = cells[0].select_one("a[href]")
        name = " ".join(cells[0].get_text().split())
        address = " ".join(cells[1].get_text().split())
        office = " ".join(cells[2].get_text().split())
        fo_link = cells[2].select_one("a[href]")
        ports.append({
            "state": state,
            "name": name,
            "href": link.get("href") if link else None,
            "address": address,
            "field_office": office,
            "field_office_href": fo_link.get("href") if fo_link else None,
        })
    return ports


def parse_port_detail(html, url):
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main")
    for t in main.select("script,style,noscript"):
        t.decompose()
    h1 = main.select_one("h1")
    text = "\n".join(ln.strip() for ln in main.get_text("\n").splitlines()
                     if ln.strip())
    # cut the two sidebar navigation repeats
    body_start = text.find("Skip to body content")
    body_start = text.find("Skip to body content", body_start + 5) if body_start >= 0 else 0
    body = text[body_start:] if body_start > 0 else text
    # fields
    def grab(label, maxlen=400):
        m = re.search(rf"{label}\s*\n(.+)", body)
        if m:
            return " ".join(m.group(1).split())[:maxlen]
        return ""
    port_code = grab("Port Code", 20)
    phone = ""
    m = re.search(r"Phone Contact:\s*Phone\s*(\+?[\d\-\s\(\)\.]+)", body)
    if m:
        phone = " ".join(m.group(1).split())[:30]
    fax = ""
    m = re.search(r"Fax Number:\s*Fax\s*([\d\-\s\(\)]+)", body)
    if m:
        fax = " ".join(m.group(1).split())[:30]
    director = grab("Port Director", 60)
    hours = ""
    m = re.search(r"Office Hours\s*\n(.*?)(?:Directions to Port Office|Facilities and Crossings|$)",
                  body, re.S)
    if m:
        hours = " ".join(m.group(1).split())[:500]
    directions = ""
    m = re.search(r"Directions to Port Office\s*\n(.*?)(?:Facilities and Crossings|Last Modified|$)",
                  body, re.S)
    if m:
        directions = " ".join(m.group(1).split())[:900]
    facilities = ""
    m = re.search(r"Facilities and Crossings\s*\n(.*?)(?:Last Modified|$)", body, re.S)
    if m:
        facilities = " ".join(m.group(1).split())[:1200]
    last_mod = ""
    m = re.search(r"Last Modified:\s*([^\n]+)", body)
    if m:
        last_mod = m.group(1).strip()[:40]
    return {"url": url, "title": " ".join(h1.get_text().split()) if h1 else "",
            "port_code": port_code, "phone": phone, "fax": fax,
            "director": director, "hours": hours,
            "directions": directions, "facilities": facilities,
            "last_modified": last_mod, "body": body[:4000]}


def main():
    all_ports = []
    details_todo = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=UA,
                                  viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        for st in STATES:
            out = OUT / f"state_{st}.json"
            if out.exists():
                data = json.load(open(out))
                all_ports.extend(data["ports"])
                continue
            url = f"{BASE}/about/contact/ports/{st}"
            ok = False
            for attempt in range(4):
                try:
                    r = page.goto(url, wait_until="domcontentloaded",
                                  timeout=45000)
                    page.wait_for_timeout(1500)
                    html = page.content()
                    if (r.status if r else 0) == 200:
                        ports = parse_state_page(html, st)
                        out.write_text(json.dumps({"url": url, "ports": ports},
                                                  indent=1))
                        all_ports.extend(ports)
                        print(f"[state {st}] {len(ports)} ports")
                        ok = True
                        break
                except Exception as e:
                    print(f"[retry {st}.{attempt}] {str(e)[:60]}")
                time.sleep(4 + attempt * 3)
            if not ok:
                print(f"[FAIL state] {st}")
            time.sleep(random.uniform(0.8, 1.6))
        print(f"[ports] {len(all_ports)} ports indexed")
        # detail pages
        for p_ in all_ports:
            if p_["state"] in DETAIL_STATES and p_["href"]:
                details_todo.append(p_)
        print(f"[ports] {len(details_todo)} detail pages to fetch")
        done = 0
        for p_ in details_todo:
            slug = p_["href"].rstrip("/").split("/")[-1]
            out = OUT / f"port_{slug}.json"
            if out.exists():
                done += 1
                continue
            url = BASE + p_["href"]
            for attempt in range(4):
                try:
                    r = page.goto(url, wait_until="domcontentloaded",
                                  timeout=45000)
                    page.wait_for_timeout(1400)
                    html = page.content()
                    if (r.status if r else 0) == 200 and len(html) > 40000:
                        rec = parse_port_detail(html, url)
                        rec["state"] = p_["state"]
                        rec["name"] = p_["name"]
                        out.write_text(json.dumps(rec, indent=1))
                        done += 1
                        if done % 20 == 0:
                            print(f"[detail] {done}/{len(details_todo)}")
                        break
                except Exception as e:
                    print(f"[retry {slug[:25]}.{attempt}] {str(e)[:60]}")
                time.sleep(4 + attempt * 3)
            time.sleep(random.uniform(0.7, 1.4))
        browser.close()
    (OUT / "index.json").write_text(json.dumps(all_ports, indent=1))
    print(f"[ports] done: {len(all_ports)} ports, {done} details")


if __name__ == "__main__":
    main()
