"""Process raw scraped captures into the tracked source_data/ snapshots.

Reads scraped_data/ (gitignored, build-time raw captures) and writes the
normalized, deterministic inputs that seed_data.py loads:

  source_data/events.json          all catalog events (from grid API captures)
  source_data/performers.json      performers with real ids/images where known
  source_data/venues.json          venues with seatmap/section info
  source_data/listings/<eid>.json  real listing sets for deep-harvested events
  source_data/categories.json      taxonomy tree
  source_data/home_curation.json   popular/recommended curation
  source_data/image_urls.json      every upstream image URL to download
"""
import collections
import glob
import json
import pathlib
import re

SITE = pathlib.Path(__file__).resolve().parents[1]
SCRAP = SITE / "scraped_data"
SRC = SITE / "source_data"
SRC.mkdir(exist_ok=True)
(SRC / "listings").mkdir(exist_ok=True)

MIRROR_DATE = "2026-09-26"

# Taxonomy captured from the live nav (see scraped_data/navlinks_*.json).
TAXONOMY = [
    {"name": "Sports", "slug": "sports", "kind": "top", "upstream_id": 51,
     "children": [
        {"name": "MLB", "slug": "mlb", "kind": "grouping", "upstream_id": 81},
        {"name": "NBA", "slug": "nba", "kind": "grouping", "upstream_id": 115},
        {"name": "NFL", "slug": "nfl", "kind": "grouping", "upstream_id": 121},
        {"name": "NHL", "slug": "nhl", "kind": "grouping", "upstream_id": 144},
        {"name": "MLS", "slug": "mls", "kind": "grouping", "upstream_id": 142},
        {"name": "WWE", "slug": "wwe", "kind": "grouping", "upstream_id": 131},
        {"name": "College Sports", "slug": "college-sports", "kind": "grouping", "upstream_id": 198988},
        {"name": "Tennis", "slug": "tennis", "kind": "category", "upstream_id": 7667},
        {"name": "Golf", "slug": "golf", "kind": "category", "upstream_id": 111},
        {"name": "Rodeo", "slug": "rodeo", "kind": "category", "upstream_id": 6979},
        {"name": "Fight", "slug": "fight", "kind": "category", "upstream_id": 7368},
        {"name": "Rugby", "slug": "rugby", "kind": "category", "upstream_id": 135925},
        {"name": "Horse Racing", "slug": "horse-racing", "kind": "category", "upstream_id": 7851},
        {"name": "Cricket", "slug": "cricket", "kind": "category", "upstream_id": 490473},
        {"name": "Volleyball", "slug": "volleyball", "kind": "category", "upstream_id": 154993},
     ]},
    {"name": "Concerts", "slug": "concerts", "kind": "top", "upstream_id": 1,
     "children": [
        {"name": "Pop", "slug": "pop", "kind": "category", "upstream_id": 1502178},
        {"name": "Rock", "slug": "rock-music", "kind": "category", "upstream_id": 209736},
        {"name": "Rap and Hip-Hop", "slug": "rap-and-hip-hop-music", "kind": "category", "upstream_id": 195739},
        {"name": "Country", "slug": "country", "kind": "category", "upstream_id": 1501250},
        {"name": "Heavy Metal", "slug": "heavy-metal", "kind": "category", "upstream_id": 1502004},
        {"name": "Dance and Electronic", "slug": "dance-and-electronic-music", "kind": "category", "upstream_id": 195489},
        {"name": "Alternative", "slug": "alternative-music", "kind": "category", "upstream_id": 178737},
        {"name": "Folk", "slug": "folk", "kind": "category", "upstream_id": 1502307},
        {"name": "R&B and Soul", "slug": "rb-and-soul-music", "kind": "category", "upstream_id": 195742},
     ]},
    {"name": "Theater", "slug": "theater", "kind": "top", "upstream_id": 2,
     "children": [
        {"name": "Musicals", "slug": "musicals", "kind": "category", "upstream_id": 700188},
        {"name": "Plays", "slug": "plays", "kind": "category", "upstream_id": 700189},
        {"name": "Comedy", "slug": "comedy", "kind": "category", "upstream_id": 209},
        {"name": "Family", "slug": "family", "kind": "category", "upstream_id": 5242},
        {"name": "Classical and Opera", "slug": "classical-music-and-opera", "kind": "category", "upstream_id": 178},
        {"name": "Dance / Ballet", "slug": "dance-ballet", "kind": "category", "upstream_id": 176},
        {"name": "Broadway", "slug": "broadway-shows", "kind": "category", "upstream_id": 138275421},
     ]},
    {"name": "Festivals", "slug": "festivals", "kind": "top", "upstream_id": 490277,
     "children": []},
]

# grid-source -> taxonomy node (upstream id) for events harvested from that grid
SOURCE_NODE = {
    "concerts": ("Concerts", 1), "pop": ("Pop", 1502178), "rock": ("Rock", 209736),
    "hiphop": ("Rap and Hip-Hop", 195739), "country": ("Country", 1501250),
    "metal": ("Heavy Metal", 1502004), "electronic": ("Dance and Electronic", 195489),
    "comedy": ("Comedy", 209), "musicals": ("Musicals", 700188),
    "plays": ("Plays", 700189), "family": ("Family", 5242),
    "classical": ("Classical and Opera", 178),
    "festivals": ("Festivals", 490277),
    "grouping_nfl": ("NFL", 121), "grouping_mlb": ("MLB", 81),
    "grouping_nba": ("NBA", 115), "grouping_nhl": ("NHL", 144),
    "grouping_mls": ("MLS", 142), "grouping_wwe": ("WWE", 131),
    "grouping_college": ("College Sports", 198988),
    "sports_tennis": ("Tennis", 7667), "sports_golf": ("Golf", 111),
    "sports_fight": ("Fight", 7368), "sports_rodeo": ("Rodeo", 6979),
}

FEATURES = {"clear view", "instant download", "aisle seat", "club access",
            "parking included", "wheelchair accessible", "limited view",
            "obstructed view", "standing room only (sro)"}
BADGES = {"best price", "best deal", "fan favorite", "last tickets",
          "sponsored", "viewed", "verified"}


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def parse_event_url(url):
    m = re.match(r"https://www\.stubhub\.com/(.+)/event/(\d+)/?", url)
    return (m.group(1), int(m.group(2))) if m else (None, None)


def performer_from_url(url, city):
    slug, _ = parse_event_url(url)
    if not slug:
        return None, None
    slug = re.sub(r"-\d+-\d+-\d{4}$", "", slug)
    if slug.endswith("-tickets"):
        slug = slug[: -len("-tickets")]
    city_slug = slugify(city or "")
    if city_slug and slug.endswith("-" + city_slug):
        slug = slug[: -(len(city_slug) + 1)]
    name = slug.replace("-", " ").strip()
    return slug, name


def parse_listing(card, evt_slug):
    """Parse one harvested listing card into normalized fields."""
    text = card.get("text") or ""
    parts = [p.strip() for p in text.split("|") if p.strip()]
    label = card.get("label") or ""
    is_sponsored = label.startswith("Sponsored") or "Sponsored" in parts
    # prices: data-price is current; look for original (strikethrough) in text
    price = None
    m = re.search(r"\$([\d,]+)", card.get("price") or "")
    if m:
        price = int(m.group(1).replace(",", ""))
    original = None
    price_tokens = [p for p in parts if re.fullmatch(r"\$[\d,]+", p)]
    if len(price_tokens) >= 2:
        vals = [int(t.replace("$", "").replace(",", "")) for t in price_tokens]
        # strikethrough appears before the current price; current == data-price
        if price in vals:
            others = [v for v in vals if v != price]
            if others and max(others) > price:
                original = max(others)
    # section / row / seats
    section = None
    row = None
    seats = None
    for p in parts:
        m = re.match(r"^Section (.+)$", p)
        if m and section is None:
            section = m.group(1)
            continue
        m = re.match(r"^Row (\S+)(?: · Seats (.+))?$", p)
        if m and row is None:
            row = m.group(1)
            seats = m.group(2)
            continue
        m = re.match(r"^(.+?) Row (\S+)$", p)  # theater style "MAINL Row S"
        if m and section is None:
            section, row = m.group(1), m.group(2)
    if section is None and label:
        m = re.match(r"(?:Sponsored, )?([^,]+),", label)
        if m:
            section = m.group(1)
    # quantity
    qty = None
    for p in parts:
        m = re.match(r"^(\d+) tickets?( together)?$", p)
        if m:
            qty = int(m.group(1))
            break
    if qty is None and label:
        m = re.search(r"(\d+) tickets?", label)
        qty = int(m.group(1)) if m else 2
    # features / badges
    feats, badges = [], []
    for p in parts:
        low = p.lower()
        if low in FEATURES or low in {"2 tickets together", "4 tickets together",
                                      "6 tickets together", "3 tickets together",
                                      "5 tickets together", "8 tickets together"}:
            if low not in {"standing room only (sro)"}:
                feats.append(p)
        elif low in BADGES or re.match(r"^only \d+ left", low) or low in {"last ticket"}:
            badges.append(p)
    # deal rating
    rating = None
    for i, p in enumerate(parts):
        if re.fullmatch(r"\d+\.\d", p) and i + 1 < len(parts) \
                and parts[i + 1] in ("Amazing", "Great", "Good", "Okay"):
            rating = float(p)
    # seat-view image
    img = card.get("img")
    img_clean = re.sub(r"\?.*$", "", img) if img else None
    return {
        "upstream_id": int(card["id"]),
        "section": section, "row": row, "seats": seats,
        "quantity": qty or 2, "price": price, "original_price": original,
        "features": feats, "badges": badges, "deal_rating": rating,
        "seat_view_url": img_clean, "sponsored": is_sponsored,
    }


def parse_iso_dt(s):
    """2026-10-01T20:30:00 -> epoch ms (local venue time, no tz shift)."""
    import datetime
    if not s:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", s)
    if not m:
        return None
    dt = datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                            int(m.group(4)), int(m.group(5)))
    return int(dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)


STATE_ABBR = {
    "Washington": "WA", "Nevada": "NV", "Connecticut": "CT", "Colorado": "CO",
    "Pennsylvania": "PA", "Maryland": "MD", "North Carolina": "NC",
    "California": "CA", "New York": "NY", "Texas": "TX", "Florida": "FL",
    "Illinois": "IL", "Arizona": "AZ", "Georgia": "GA", "Ohio": "OH",
    "Michigan": "MI", "Massachusetts": "MA", "New Jersey": "NJ",
    "Tennessee": "TN", "Missouri": "MO", "Minnesota": "MN", "Oregon": "OR",
    "Utah": "UT", "Indiana": "IN", "Wisconsin": "WI", "Virginia": "VA",
}

EVENT_TYPE_SOURCE = {
    "MusicEvent": "concerts", "SportsEvent": "sports",
    "TheaterEvent": "theater", "DanceEvent": "dance",
    "ComedyEvent": "comedy", "FestivalEvent": "festivals",
}


def main():
    # ---------------- events + venues + performers from grid captures ----
    events = {}
    for f in sorted(glob.glob(str(SCRAP / "events" / "*.json"))):
        d = json.loads(pathlib.Path(f).read_text())
        fname = pathlib.Path(f).name
        src = fname.split("__")[0]
        node = SOURCE_NODE.get(src)
        metro = None
        m = re.search(r"__(\w+)\.json$", fname)
        if m and m.group(1) != "p":
            metro = m.group(1)
        for it in d.get("items", []):
            eid = it["eventId"]
            e = events.setdefault(eid, {
                "upstream_id": eid, "name": it["name"], "url": it["url"],
                "venue_id": it["venueId"], "venue_name": it["venueName"],
                "city": it.get("venueCity"), "state": it.get("venueStateProvince"),
                "sources": set(), "metros": set(),
            })
            e["sources"].add(src)
            if metro:
                e["metros"].add(metro)
            ms = it.get("eventMetadata", {}).get("common", {}).get("eventStartDateTime")
            if ms:
                e["start_ms"] = ms
            if it.get("isTbd"):
                e["is_tbd"] = True
            hm = (it.get("holidayMessage") or {}).get("message")
            if hm:
                e["holiday_badge"] = hm
            if it.get("isParkingEvent"):
                e["is_parking"] = True
            if not it.get("hasActiveListings"):
                e["no_listings"] = True

    # deep-harvested event pages: performer ids, og images, listings
    listing_sets = {}
    performer_links = {}
    og_images = {}
    availability = {}
    showing_counts = {}
    price_ranges = {}
    pass_titles = {}
    for f in sorted(glob.glob(str(SCRAP / "event_pages" / "*.json"))):
        d = json.loads(pathlib.Path(f).read_text())
        eid = d["eventId"]
        any_pass = d["passes"].get("any") or next(iter(d["passes"].values()), None)
        if not any_pass:
            continue
        for link in any_pass.get("performerLinks") or []:
            m = re.match(r"/(.+)-tickets/(performer|grouping|category)/(\d+)", link["h"] or "")
            if m:
                performer_links[eid] = {"slug": m.group(1), "kind": m.group(2),
                                        "upstream_id": int(m.group(3))}
        if any_pass.get("ogImage"):
            og_images[eid] = any_pass["ogImage"]
        if any_pass.get("availability"):
            availability[eid] = any_pass["availability"]
        if any_pass.get("showing"):
            showing_counts[eid] = any_pass["showing"][1]
        if any_pass.get("priceRangeText"):
            price_ranges[eid] = [int(price_ranges[0]) if False else int(any_pass["priceRangeText"][0].replace(",", "")),
                                 int(any_pass["priceRangeText"][1].replace(",", ""))]
        # listings across passes (dedupe by upstream id)
        all_listings = {}
        for key, p in d["passes"].items():
            for card in p.get("listings") or []:
                parsed = parse_listing(card, None)
                if parsed["upstream_id"] in all_listings:
                    continue
                all_listings[parsed["upstream_id"]] = parsed
        if all_listings:
            listing_sets[eid] = list(all_listings.values())

    # ---------------- marquee events (not covered by grid captures) -------
    # venue info harvested from each event page's schema.org JSON-LD block
    ld_info = {}
    for f in sorted((SCRAP / "event_venue").glob("*.json")):
        ld_info[int(f.stem)] = json.loads(f.read_text())
    marquee_urls = json.loads((SCRAP / "marquee_urls.json").read_text())
    grid_ids = set(events)
    for eid, ld in sorted(ld_info.items()):
        if eid in grid_ids:
            continue
        if eid not in performer_links and eid not in og_images:
            continue  # no usable capture for this event
        src = EVENT_TYPE_SOURCE.get(ld.get("type") or "", "concerts")
        events[eid] = {
            "upstream_id": eid, "name": ld["name"],
            "url": marquee_urls.get(str(eid)) or f"https://www.stubhub.com/event/{eid}/",
            "venue_id": None,  # resolved after venues are known
            "venue_name": ld.get("venueName"), "city": ld.get("city"),
            "state": STATE_ABBR.get(ld.get("state"), ld.get("state")),
            "sources": {src}, "metros": set(),
            "start_ms": parse_iso_dt(ld.get("startDate")),
            "ld_venue_url": ld.get("venueUrl"),
        }

    # ---------------- performers ----------------
    performers = {}
    for eid, e in events.items():
        pslug, pname = performer_from_url(e["url"], e["city"])
        if not pslug:
            continue
        e["performer_slug"] = pslug
        link = performer_links.get(eid)
        if link and link["slug"] == pslug:
            e["performer_upstream_id"] = link["upstream_id"]
            e["performer_kind"] = link["kind"]
        p = performers.setdefault(pslug, {
            "slug": pslug, "name": pname, "event_count": 0,
            "upstream_id": None, "kind": "performer", "image_url": og_images.get(eid)})
        p["event_count"] += 1
        if link and link["slug"] == pslug:
            p["upstream_id"] = link["upstream_id"]
            p["kind"] = link["kind"]
            if eid in og_images:
                p["image_url"] = og_images[eid]
        # events with no listings captured still count for curation

    # merge real bios / follower counts harvested from performer pages
    for f in sorted((SCRAP / "performers").glob("*.json")):
        d = json.loads(f.read_text())
        p = performers.get(f.stem)
        if not p:
            continue
        if d.get("bio"):
            p["bio"] = d["bio"]
        if d.get("followers"):
            p["followers_text"] = d["followers"]

    # mirror-assigned ids for performers lacking a real one (distinct range)
    next_mirror_id = 900000001
    for pslug, p in sorted(performers.items()):
        if not p["upstream_id"]:
            p["upstream_id"] = next_mirror_id
            next_mirror_id += 1

    # ---------------- venues ----------------
    venues = {}
    seatmap_files = {}
    for p in (SCRAP / "seatmaps").glob("*.svg"):
        if p.stem.startswith("event_"):
            continue
        seatmap_files[int(p.stem)] = p.name
    for eid, e in events.items():
        if e["venue_id"] is None:
            continue  # marquee events resolved below
        v = venues.setdefault(e["venue_id"], {
            "upstream_id": e["venue_id"], "name": e["venue_name"],
            "city": e["city"], "state": e["state"], "country": "USA",
            "seatmap": seatmap_files.get(e["venue_id"]),
        })
        if not v.get("city") and e.get("city"):
            v["city"] = e["city"]

    # resolve marquee event venues: prefer a grid venue with the exact same
    # name (consistent single row per venue), else the JSON-LD venue id
    ld_name_to_grid = {}
    for vid, v in venues.items():
        if vid is not None:
            ld_name_to_grid[v["name"]] = vid
    for eid, e in sorted(events.items()):
        if e["venue_id"] is None:
            m = re.search(r"venue/(\d+)", e.get("ld_venue_url") or "")
            ld_vid = int(m.group(1)) if m else None
            vid = ld_name_to_grid.get(e["venue_name"], ld_vid)
            if vid is None:
                continue
            e["venue_id"] = vid
            v = venues.setdefault(vid, {
                "upstream_id": vid, "name": e["venue_name"],
                "city": e["city"], "state": e["state"], "country": "USA",
                "seatmap": seatmap_files.get(vid),
            })

    # seatmaps for venues that still lack one: reuse the SVG embedded in any
    # deep-harvested event page capture at that venue
    for eid, e in sorted(events.items()):
        vid = e.get("venue_id")
        if not vid or venues.get(vid, {}).get("seatmap"):
            continue
        f = SCRAP / "event_pages" / f"{eid}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        for p in d.get("passes", {}).values():
            svg = p.get("seatMapSvg")
            if svg and len(svg) > 2000:
                fname = f"{vid}.svg"
                (SCRAP / "seatmaps" / fname).write_text(svg)
                seatmap_files[vid] = fname
                venues[vid]["seatmap"] = fname
                break
    # section labels per venue from the seatmap SVGs
    for vid, fname in seatmap_files.items():
        svg = (SCRAP / "seatmaps" / fname).read_text()
        labels = []
        for m in re.finditer(r"<text[^>]*>([^<]+)</text>", svg):
            t = m.group(1).strip()
            if t and t not in labels and not t.startswith("STAGE"):
                labels.append(t)
        if vid in venues:
            venues[vid]["sections"] = labels

    # ---------------- write outputs ----------------
    events_out = []
    for eid, e in sorted(events.items()):
        if not e.get("venue_id"):
            continue  # marquee event whose venue could not be resolved
        start = None
        if e.get("start_ms"):
            start = e["start_ms"] // 1000
        rec = {
            "upstream_id": eid, "name": e["name"], "url": e["url"],
            "performer_slug": e.get("performer_slug"),
            "performer_upstream_id": e.get("performer_upstream_id"),
            "performer_kind": e.get("performer_kind", "performer"),
            "venue_id": e["venue_id"],
            "start_epoch": start, "is_tbd": bool(e.get("is_tbd")),
            "holiday_badge": e.get("holiday_badge"),
            "is_parking": bool(e.get("is_parking")),
            "no_listings": bool(e.get("no_listings")),
            "sources": sorted(e["sources"]),
            "metros": sorted(e["metros"]),
            "availability": availability.get(eid),
            "showing_count": showing_counts.get(eid),
            "price_range": price_ranges.get(eid),
        }
        events_out.append(rec)

    performers_out = [performers[k] for k in sorted(performers)]
    venues_out = [venues[k] for k in sorted(venues) if k is not None]

    (SRC / "events.json").write_text(json.dumps(events_out, indent=1))
    (SRC / "performers.json").write_text(json.dumps(performers_out, indent=1))
    (SRC / "venues.json").write_text(json.dumps(venues_out, indent=1))
    (SRC / "categories.json").write_text(json.dumps(TAXONOMY, indent=1))

    for eid, lst in listing_sets.items():
        (SRC / "listings" / f"{eid}.json").write_text(json.dumps(lst, indent=1))

    # ---------------- home curation (from the live home capture) ----------
    home = json.loads((SCRAP / "home.json").read_text())
    popular_slugs, recommended_slugs = [], []
    for link in home.get("links", []):
        h = link.get("h") or ""
        m = re.match(r"/(.+)-tickets/(?:performer|category)/(\d+)", h)
        if m:
            popular_slugs.append({"slug": m.group(1), "upstream_id": int(m.group(2))})
    # recommended: dedup, keep order
    seen = set()
    popular_unique = []
    for p in popular_slugs:
        if p["slug"] not in seen:
            seen.add(p["slug"])
            popular_unique.append(p)
    (SRC / "home_curation.json").write_text(json.dumps(
        {"popular": popular_unique[:12], "recommended": popular_unique[12:32]},
        indent=1))

    # ---------------- image manifest ----------------
    images = {}
    for eid, url in og_images.items():
        images[url] = {"kind": "performer-hero"}
    for eid, lst in listing_sets.items():
        for l in lst:
            if l.get("seat_view_url"):
                images[l["seat_view_url"]] = {"kind": "seat-view"}
    (SRC / "image_urls.json").write_text(json.dumps(
        {u: meta for u, meta in sorted(images.items())}, indent=1))

    print(f"events: {len(events_out)}  performers: {len(performers_out)}  "
          f"venues: {len(venues_out)}  listing sets: {len(listing_sets)}  "
          f"image urls: {len(images)}")
    n_with_listings = sum(len(v) for v in listing_sets.values())
    print(f"total real listings: {n_with_listings}")


if __name__ == "__main__":
    main()
