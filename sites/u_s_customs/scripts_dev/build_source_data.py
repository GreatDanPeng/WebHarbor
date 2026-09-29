#!/usr/bin/env python3
"""Build the tracked source_data/*.json snapshots from scraped_data/.

Every record here originates from the real upstream capture
(www.cbp.gov, bwt.cbp.gov, careers.cbp.gov, usajobs.gov) taken on
2026-09-28; this script only cleans, normalizes and dedupes it. The
deterministic seed (seed_data.py at image build time) reads exactly
these files, in a fixed order, with PYTHONHASHSEED=0.

Run: python3 build_source_data.py   (from scripts_dev/)
Writes ../source_data/*.json
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRAPE = ROOT / "scraped_data"
OUT = ROOT / "source_data"

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}
ABBR = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Sept": 9, "Oct": 10, "Nov": 11,
        "Dec": 12}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


IMG_MAP = {}

def _img_map():
    """url -> local static path for every downloaded upstream image."""
    global IMG_MAP
    if IMG_MAP:
        return IMG_MAP
    mf = SCRAPE / "image_manifest.json"
    if mf.exists():
        for rec in load(mf):
            IMG_MAP[rec["url"]] = "/" + rec["file"]
    return IMG_MAP


def map_images(images):
    """Rewrite upstream image URLs to their mirrored local paths."""
    out = []
    for im in images or []:
        url = re.sub(r"\?itok=[A-Za-z0-9_-]+$", "", im.get("src", ""))
        local = _img_map().get(url) or _img_map().get(im.get("src", ""))
        if local:
            out.append({"src": local, "alt": im.get("alt", ""),
                        "local": True})
        # upstream-only references are dropped: the mirror serves real
        # downloaded media only.
    return out

def dump(name, data):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(data, indent=1, sort_keys=False,
                                       ensure_ascii=False) + "\n",
                            encoding="utf-8")
    print(f"[src] {name}: "
          f"{len(data) if isinstance(data, (list, dict)) else '?'} records")


def parse_date(text):
    """Return ISO date from formats used across the site."""
    if not text:
        return ""
    text = text.strip()
    m = re.match(r"([A-Z][a-z]+)\s+(\d{1,2}),?\s+(20\d\d)", text)
    if m and m.group(1) in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    m = re.match(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+(\d{2})/(\d{2})/(\d{4})", text)
    if m:
        return f"{int(m.group(4)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.match(r"([A-Z][a-z]{2})\w*\s+(\d{1,2})\s*,?\s*20?(\d\d)", text)
    if m and m.group(1) in ABBR:
        return f"20{m.group(3)}-{ABBR[m.group(1)]:02d}-{int(m.group(2)):02d}"
    return ""


# ------------------------------------------------------------------ pages --

PAGES_META = {
    # slug -> (upstream path, category, nav section)
    "home": ("/", "Home", "Home"),
    "travel": ("/travel", "Travel", "Travel"),
    "intl_visitors": ("/travel/international-visitors", "Travel",
                      "For International Visitors"),
    "esta": ("/travel/international-visitors/esta", "Travel",
             "For International Visitors"),
    "know_before_you_visit": ("/travel/international-visitors/know-before-you-visit", "Travel", "For International Visitors"),
    "vwp": ("/travel/international-visitors/visa-waiver-program", "Travel",
            "For International Visitors"),
    "i94": ("/travel/international-visitors/i-94", "Travel",
            "For International Visitors"),
    "ttp": ("/travel/trusted-traveler-programs", "Travel",
            "Trusted Traveler Programs"),
    "global_entry": ("/travel/trusted-traveler-programs/global-entry",
                     "Travel", "Trusted Traveler Programs"),
    "nexus": ("/travel/trusted-traveler-programs/nexus", "Travel",
              "Trusted Traveler Programs"),
    "sentri": ("/travel/trusted-traveler-programs/sentri", "Travel",
               "Trusted Traveler Programs"),
    "fast": ("/travel/trusted-traveler-programs/fast", "Travel",
             "Trusted Traveler Programs"),
    "tsa_precheck": ("/travel/trusted-traveler-programs/tsa-precheck",
                     "Travel", "Trusted Traveler Programs"),
    "us_citizens": ("/travel/us-citizens", "Travel",
                    "For U.S. Citizens/Lawful Permanent Residents"),
    "know_before_you_go": ("/travel/us-citizens/know-before-you-go", "Travel",
                           "For U.S. Citizens/Lawful Permanent Residents"),
    "mpc": ("/travel/us-citizens/mobile-passport-control", "Travel",
            "For U.S. Citizens/Lawful Permanent Residents"),
    "canada_mexico": ("/travel/us-citizens/canada-mexico-travel", "Travel",
                      "For U.S. Citizens/Lawful Permanent Residents"),
    "advisories_wait_times": ("/travel/advisories-wait-times", "Travel",
                              "Advisories and Wait Times"),
    "biometrics": ("/travel/biometrics", "Travel", "Biometrics"),
    "trade": ("/trade", "Trade", "Trade"),
    "basic_import_export": ("/trade/basic-import-export", "Trade",
                            "Basic Import and Export"),
    "importing_car": ("/trade/basic-import-export/importing-car", "Trade",
                      "Basic Import and Export"),
    "internet_purchases": ("/trade/basic-import-export/internet-purchases",
                           "Trade", "Basic Import and Export"),
    "importer_exporter_tips": ("/trade/basic-import-export/importer-exporter-tips",
                               "Trade", "Basic Import and Export"),
    "priority_issues": ("/trade/priority-issues", "Trade",
                        "Priority Trade Issues"),
    "ptl_adcvd": ("/trade/priority-issues/adcvd", "Trade",
                  "Priority Trade Issues"),
    "ptl_ipr": ("/trade/priority-issues/ipr", "Trade",
                "Priority Trade Issues"),
    "ptl_import_safety": ("/trade/priority-issues/import-safety", "Trade",
                          "Priority Trade Issues"),
    "ptl_textiles": ("/trade/priority-issues/textiles", "Trade",
                     "Priority Trade Issues"),
    "ptl_quotas": ("/trade/priority-issues/quotas", "Trade",
                   "Priority Trade Issues"),
    "ptl_revenue": ("/trade/priority-issues/revenue", "Trade",
                    "Priority Trade Issues"),
    "ptl_trade_agreements": ("/trade/priority-issues/trade-agreements",
                              "Trade", "Priority Trade Issues"),
    "ace": ("/trade/automated", "Trade", "ACE"),
    "icp": ("/trade/rulings/informed-compliance-publications", "Trade",
            "Rulings & Legal Decisions"),
    "newsroom": ("/newsroom", "Newsroom", "Newsroom"),
    "announcements": ("/newsroom/announcements", "Newsroom", "Announcements"),
    "forms": ("/newsroom/publications/forms", "Newsroom", "Forms"),
    "contact": ("/about/contact", "About CBP", "Contact Us"),
    "about": ("/about", "About CBP", "About CBP"),
    "ports_entry": ("/border-security/ports-entry", "Border Security",
                    "At Ports of Entry"),
    "ports_landing": ("/contact/ports", "About CBP",
                      "Locate a Port of Entry"),
}


def build_pages():
    """Static page bodies are read from the raw HTML captures: the article
    region is main .field--name-body (everything else on the page is
    duplicated navigation chrome)."""
    from bs4 import BeautifulSoup
    records = []
    for slug, (path, category, nav) in PAGES_META.items():
        f = SCRAPE / "pages" / f"{slug}.json"
        fh = SCRAPE / "pages" / f"{slug}.html"
        if not f.exists():
            print(f"[warn] missing page scrape: {slug}")
            continue
        d = load(f)
        lines = []
        outline = []
        if fh.exists():
            soup = BeautifulSoup(fh.read_text(), "lxml")
            main = soup.select_one("main")
            body_el = main.select(".field--name-body")[0] if main and \
                main.select(".field--name-body") else None
            if body_el is not None:
                for el in body_el.select("h2, h3, h4"):
                    t = " ".join(el.get_text().split())
                    if t:
                        outline.append({"tag": el.name, "text": t})
                # paragraph-ish extraction: block elements become lines
                for el in body_el.find_all(
                        ["p", "li", "h2", "h3", "h4", "td", "th", "caption"]):
                    t = " ".join(el.get_text(" ").split())
                    if t and t not in [l for l in lines]:
                        lines.append(t)
        if not lines:
            # fallback to the scraped text record
            text = d["text"]
            title = d["title"]
            marker = "Skip to body content"
            j = text.rfind(marker)
            search_from = j + len(marker) if j >= 0 else 0
            i = text.find(title, search_from) if title else -1
            body = text[i + len(title):].strip() if i >= 0 else (
                text[search_from:] if j >= 0 else text)
            for stop in ["Related Content", "Last Modified"]:
                k = body.find(stop)
                if k > 200:
                    body = body[:k].rstrip()
            lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
            outline = d["outline"]
        records.append({
            "slug": slug,
            "upstream_path": path,
            "title": d["title"],
            "category": category,
            "nav": nav,
            "lines": lines[:400],
            "outline": outline or d["outline"],
            "links": d["links"][:200],
            "docs": d["docs"],
            "images": map_images(d["images"]),
            "last_modified": d["last_modified"].replace("Last Modified: ", ""),
        })
    dump("pages.json", records)


# -------------------------------------------------------------- border wait --

def _int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def build_bwt():
    raw = load(SCRAPE / "bwt" / "waits.json")
    crossings = []
    for rec in raw:
        def lane_block(block, mode):
            out = {"maximum_lanes": _int(block.get("maximum_lanes")) or 0,
                   "automation_type": block.get(f"{mode}_automation_type", "")}
            for lane_key, lane_name in [
                    ("standard_lanes", "Standard"),
                    ("FAST_lanes", "FAST"),
                    ("NEXUS_SENTRI_lanes", "NEXUS_SENTRI"),
                    ("ready_lanes", "READY")]:
                lane = block.get(lane_key) or {}
                if lane.get("operational_status") or lane.get("delay_minutes"):
                    out[lane_name] = {
                        "status": lane.get("operational_status", ""),
                        "delay": _int(lane.get("delay_minutes")) or 0,
                        "open": _int(lane.get("lanes_open")),
                        "updated": lane.get("update_time", ""),
                    }
                else:
                    out[lane_name] = None
            return out
        cov = lane_block(rec.get("commercial_vehicle_lanes") or {}, "cv")
        pov = lane_block(rec.get("passenger_vehicle_lanes") or {}, "pv")
        ped = lane_block(rec.get("pedestrian_lanes") or {}, "ped")
        crossings.append({
            "port_number": rec["port_number"],
            "port_name": rec["port_name"],
            "crossing_name": rec["crossing_name"],
            "border": "canada" if "Canadian" in rec.get("border", "") else "mexico",
            "hours": rec.get("hours", ""),
            "port_status": rec.get("port_status", ""),
            "date": rec.get("date", ""),
            "time": rec.get("time", ""),
            "construction_notice": rec.get("construction_notice", ""),
            "commercial": cov,
            "passenger": pov,
            "pedestrian": ped,
        })
    crossings.sort(key=lambda c: (c["border"], c["port_name"],
                                  c["crossing_name"]))
    dump("bwt_crossings.json", crossings)

    # per-crossing hourly graphs
    graphs = {}
    gdir = SCRAPE / "bwt" / "graphs"
    if gdir.exists():
        for f in sorted(gdir.glob("*.json")):
            data = load(f)
            if not data:
                continue
            rec = data[0]
            key = f"{rec['port_number']}"
            series = []
            slots = (rec.get("commercial_time_slots") or {}).get("commercial_slot", [])
            for slot in slots:
                series.append({
                    "hour": _int(slot.get("time")),
                    "standard_today": _int(slot.get("standard_lane_today_wait")),
                    "standard_avg": _int(slot.get("standard_lane_average_wait")),
                    "fast_today": _int(slot.get("fast_lane_today_wait")),
                    "fast_avg": _int(slot.get("fast_lane_average_wait")),
                })
            graphs[key] = {"port_number": rec["port_number"],
                           "port_name": rec.get("port_name", ""),
                           "crossing_name": rec.get("crossing_name", ""),
                           "date": rec.get("date", ""),
                           "commercial_hours": series}
    dump("bwt_graphs.json", graphs)


# ------------------------------------------------------------------- ports --

def build_ports():
    index = load(SCRAPE / "ports" / "index.json")
    details = {}
    ddir = SCRAPE / "ports"
    for f in sorted(ddir.glob("port_*.json")):
        d = load(f)
        slug = f.stem.replace("port_", "")
        details[d.get("url", "").rstrip("/").split("/")[-1] or slug] = d
    ports = []
    for p in index:
        href = p.get("href") or ""
        slug = href.rstrip("/").split("/")[-1] if href else ""
        detail = details.get(slug, {})
        m = re.search(r"-\s(\d{3,4})$", p["name"])
        code = m.group(1) if m else (detail.get("port_code") or "")
        ports.append({
            "name": p["name"],
            "slug": slug,
            "state": p["state"],
            "code": code,
            "address": p["address"],
            "field_office": p["field_office"],
            "href": href,
            "phone": detail.get("phone", ""),
            "fax": detail.get("fax", ""),
            "director": detail.get("director", ""),
            "hours": detail.get("hours", ""),
            "directions": detail.get("directions", ""),
            "facilities": detail.get("facilities", ""),
            "last_modified": detail.get("last_modified", ""),
            "has_detail": bool(detail),
        })
    ports.sort(key=lambda p: (p["state"], p["name"]))
    dump("ports.json", ports)


# -------------------------------------------------------------------- news --

def build_news():
    releases = []
    for f in sorted((SCRAPE / "news").glob("release_*.json")):
        d = load(f)
        text = d["text"]
        title = d["title"]
        # The in-content H1 is the LAST occurrence of the title; the
        # article follows it (optionally after a "Release Date" row).
        i = text.rfind(title)
        if i < 0 and len(title) > 40:
            i = text.rfind(title[:40])
        body = text[i + len(title):].strip() if i >= 0 else text
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        date = ""
        if lines and lines[0] == "Release Date" and len(lines) > 1:
            date = parse_date(lines[1])
            lines = lines[2:]
        body = "\n".join(lines)
        if not date:
            date = parse_date(d.get("list_date", ""))
        # main prose: from the dateline ("CITY, State —") to the boilerplate
        m = re.search(r"([A-Z][A-Za-z .'-]+,\s*[A-Z]{2}|WASHINGTON|[A-Z][A-Z .'-]{2,30})"
                      r"\s*\n?\s*[\u2013\u2014-]\s*",
                      body)
        start = m.start() if m else 0
        stop = body.find("U.S. Customs and Border Protection is the unified")
        if stop < 0:
            stop = body.find("# # #")
        if stop < 0:
            stop = len(body)
        prose = " ".join(body[start:stop].split())
        loc = m.group(1).strip() if m else ""
        slug = d.get("href", "").rstrip("/").split("/")[-1]
        category = ("National Media Release"
                    if "/national-media-release/" in d.get("href", "")
                    else "Local Media Release")
        releases.append({
            "slug": slug,
            "title": title,
            "href": d.get("href", ""),
            "date": date,
            "list_date": d.get("list_date", ""),
            "location": loc,
            "category": category,
            "body": prose[:8000],
            "images": map_images(d.get("images", [])),
        })
    releases.sort(key=lambda r: (r["date"] or "0000", r["slug"]), reverse=True)
    dump("releases.json", releases)


def parse_date_to_us(iso):
    if not iso:
        return ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso)
    if m:
        return f"{m.group(2)}/{m.group(3)}/{m.group(1)}"
    return ""

# -------------------------------------------------------------------- forms --

def build_forms():
    forms = load(SCRAPE / "forms" / "forms.json")
    files = {}
    for rec in load(SCRAPE / "form_files.json"):
        files[rec["url"]] = rec
    out = []
    seen_keys = set()
    for f in forms:
        num = f.get("form_number") or ""
        pdf_url = f.get("pdf") or ""
        entry = files.get(pdf_url, {})
        key = num.lower() or "form"
        title = f["title"]
        lang = ""
        m = re.search(r"- ([A-Za-z ]+)$", title)
        if m and m.group(1).strip().lower() not in (
                "protest", "report of diversion", "entry summary",
                "application", "continuation sheet", "crew list",
                "declaration", "bond", "drawback", "petition"):
            lang = m.group(1).strip()
        if lang:
            key = f"{key}-{re.sub(r'[^a-z0-9]+', '-', lang.lower()).strip('-')}"
        base_key, n = key, 2
        while key in seen_keys:
            key = f"{base_key}-{n}"
            n += 1
        seen_keys.add(key)
        out.append({
            "catalog_key": key,
            "form_number": num,
            "name": f.get("name") or title,
            "title": title,
            "date": f.get("date", ""),
            "pdf_url": pdf_url,
            "file": entry.get("file", ""),
            "sha256": entry.get("sha256", ""),
            "bytes": entry.get("bytes", 0),
            "raw": " ".join((f.get("raw") or "").split())[:500],
        })
    out.sort(key=lambda f: (f["form_number"] or "zzz", f["title"]))
    dump("forms.json", out)


# -------------------------------------------------------------------- jobs --

def build_jobs():
    jobs = []
    for f in sorted((SCRAPE / "jobs").glob("*.json")):
        d = load(f)
        org = d.get("org") or ""
        if not org:
            t = (d.get("careers_title") or d["title"]).lower()
            if "border patrol" in t:
                org = "U.S. Border Patrol"
            elif "cbp officer" in t or "field operations" in t:
                org = "Office of Field Operations"
            elif "marine interdiction" in t or "air and marine" in t:
                org = "Air and Marine Operations"
            elif "attorney" in t or "paralegal" in t:
                org = "Office of Chief Counsel"
        cat = ("Law Enforcement"
               if org in ("U.S. Border Patrol", "Office of Field Operations",
                          "Air and Marine Operations",
                          "Office of Professional Responsibility")
               else "Administrative, Professional & Technical")
        jobs.append({
            "control": d["control"],
            "title": d["title"],
            "careers_title": d.get("careers_title", d["title"]),
            "org": org,
            "category": cat,
            "department": d.get("department", ""),
            "series_grade": " ".join((d.get("series_grade") or "").split())[:40],
            "salary": d.get("salary", ""),
            "location": " ".join((d.get("location") or "").split())[:120],
            "closing": d.get("closing", ""),
            "announcement_number": d.get("announcement_number", ""),
            "promotion_potential": d.get("promotion_potential", ""),
            "telework": d.get("telework", ""),
            "drug_test": d.get("drug_test", ""),
            "appointment_type": d.get("appointment_type", ""),
            "work_schedule": d.get("work_schedule", ""),
            "summary": d.get("summary", ""),
            "duties": d.get("duties", ""),
            "requirements": d.get("requirements", ""),
            "qualifications": d.get("qualifications", ""),
            "open_to": d.get("open_to", ""),
            "url": d["url"],
        })
    jobs.sort(key=lambda j: j["control"])
    dump("jobs.json", jobs)


# ----------------------------------------------------------------- careers --

def build_careers():
    paths = []
    for slug, title, desc in [
            ("usbp", "U.S. Border Patrol",
             "Border Patrol Agents are focused 24/7 on securing our international land borders and coastal waters between ports of entry."),
            ("amo", "Air and Marine Operations",
             "AMO uses integrated air and marine capabilities to safeguard the nation."),
            ("ofo", "Office of Field Operations",
             "CBP Officers enforce laws at ports of entry and protect the homeland."),
            ("trade", "Office of Trade",
             "Trade specialists protect the economy and enforce trade laws."),
            ("opr", "Office of Professional Responsibility",
             "OPR ensures integrity and accountability across CBP."),
            ("mission_ops", "Administrative, Professional & Technical",
             "Mission support careers spanning IT, HR, legal, finance and more."),
            ("veterans", "Veterans",
             "CBP honors veterans with hiring preferences and career paths.")]:
        f = SCRAPE / "careers" / f"{slug}.json"
        if not f.exists():
            continue
        d = load(f)
        paths.append({
            "slug": slug,
            "title": title,
            "description": desc,
            "events": d.get("events", []),
            "jobs": [j["title"] for j in d.get("jobs", [])],
            "images": d.get("images", [])[:8],
        })
    dump("career_paths.json", paths)

    events = {}
    for f in sorted((SCRAPE / "careers").glob("*.json")):
        d = load(f)
        for ev in d.get("events", []):
            key = (ev.get("date"), ev.get("event"))
            events.setdefault(key, ev)
    if not events:
        for f in sorted((SCRAPE / "careers").glob("*.json")):
            d = load(f)
            txt = " ".join(d.get("text", "").split())
            for m in re.finditer(
                    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2}), (20\d\d) "
                    r"(.{3,80}?) (In Person Live Event|National Webinar|Online)\b",
                    txt):
                date = f"{m.group(1)} {m.group(2)}, {m.group(3)}"
                events.setdefault((date, m.group(4).strip()),
                                  {"date": date, "event": m.group(4).strip(),
                                   "type": m.group(5)})
    ev_list = []
    for k, v in sorted(events.items()):
        name, loc = k[1], ""
        m = re.match(r"(.+?)\s+([A-Za-z][A-Za-z'.-]*,\s*[A-Z]{2})$", k[1])
        if m:
            name, loc = m.group(1).strip(), m.group(2).strip()
        ev_list.append({"date": k[0], "event": name, "location": loc,
                        "type": v.get("type", "")})
    dump("career_events.json", ev_list)


# ------------------------------------------------------ enrollment centers --

def build_enrollment_centers():
    """Global Entry enrollment centers from the upstream state pages.

    Layout per center (line-based state machine over the rendered text):
        <Center name>
        Address:
        <address lines...>
        Hours of Operation:
        <hours...>
        Contact Information:
        <phone...>
    """
    from bs4 import BeautifulSoup
    state_names = {"texas": "Texas", "california": "California",
                   "new-york": "New York", "florida": "Florida",
                   "arizona": "Arizona", "washington": "Washington"}
    centers = []
    seen = set()
    edir = SCRAPE / "enrollment"
    for f in sorted(edir.glob("ge_*.html")):
        if f.stem == "ge_centers":
            continue
        state = state_names.get(f.stem.replace("ge_", ""), "")
        soup = BeautifulSoup(f.read_text(), "lxml")
        main = soup.select_one("main")
        all_lines = [ln.strip() for ln in main.get_text("\n").splitlines()]
        # start after the state heading (the in-page H1)
        start_idx = 0
        for idx, ln in enumerate(all_lines):
            if ln == state:
                start_idx = idx + 1
        lines = [ln for ln in all_lines[start_idx:] if ln]
        name, addr, hours, contact = "", [], "", []
        mode = "name"
        for ln in lines:
            if ln == "Address:":
                mode = "addr"
            elif ln == "Hours of Operation:":
                mode = "hours"
            elif ln == "Contact Information:":
                mode = "contact"
            elif mode == "name":
                # a new center block begins with its name
                name = ln
            elif mode == "addr":
                addr.append(ln)
            elif mode == "hours":
                hours = ln
                mode = "hours_done"
            elif mode == "hours_done":
                # ignore stray lines until the next label
                pass
            elif mode == "contact":
                contact = ln
                if name and name not in seen:
                    seen.add(name)
                    centers.append({
                        "name": name[:160], "state": state,
                        "address": " ".join(addr)[:240],
                        "hours": hours[:200],
                        "contact": contact[:150]})
                name, addr, hours, contact = "", [], "", ""
                mode = "name"
        if name and contact and name not in seen:
            seen.add(name)
            centers.append({
                "name": name[:160], "state": state,
                "address": " ".join(addr)[:240],
                "hours": hours[:200], "contact": contact[:150]})
    centers.sort(key=lambda c: (c["state"], c["name"]))
    dump("enrollment_centers.json", centers)


# -------------------------------------------------------------- vwp + ttp ---

def build_vwp():
    """VWP country list captured from the official ESTA application site."""
    countries = ["Andorra", "Australia", "Austria", "Belgium", "Brunei",
                 "Chile", "Croatia", "Czech Republic", "Denmark", "Estonia",
                 "Finland", "France", "Germany", "Greece", "Hungary",
                 "Iceland", "Ireland", "Israel", "Italy", "Japan", "Latvia",
                 "Liechtenstein", "Lithuania", "Luxembourg",
                 "Republic of Malta", "Monaco", "Netherlands",
                 "New Zealand", "Norway", "Poland", "Portugal", "Qatar",
                 "San Marino", "Singapore", "Slovakia", "Slovenia",
                 "South Korea", "Spain", "Sweden", "Switzerland",
                 "Taiwan", "United Kingdom"]
    dump("vwp_countries.json", countries)


def build_ttp():
    """Trusted Traveler Program facts, asserted from the scraped pages."""
    programs = [
        {"slug": "global-entry", "name": "Global Entry",
         "fee": 120, "years": 5,
         "audience": "Frequent international travelers (air arrivals)",
         "includes": ["TSA PreCheck"]},
        {"slug": "nexus", "name": "NEXUS", "fee": 50, "years": 5,
         "audience": "Travelers crossing the U.S.-Canada border",
         "includes": ["Global Entry benefits", "TSA PreCheck"]},
        {"slug": "sentri", "name": "SENTRI", "fee": 122.25, "years": 5,
         "audience": "Travelers crossing the U.S.-Mexico border",
         "includes": ["Global Entry benefits", "TSA PreCheck"]},
        {"slug": "fast", "name": "FAST", "fee": 50, "years": 5,
         "audience": "Commercial truck drivers (Canada and Mexico)",
         "includes": []},
        {"slug": "tsa-precheck", "name": "TSA PreCheck", "fee": 78,
         "years": 5, "audience": "Domestic air travelers",
         "includes": []},
    ]
    dump("ttp_programs.json", programs)


def main():
    build_pages()
    build_bwt()
    build_ports()
    build_news()
    build_forms()
    build_jobs()
    build_careers()
    build_vwp()
    build_ttp()
    build_enrollment_centers()
    print("[src] all source_data files built")


if __name__ == "__main__":
    main()
