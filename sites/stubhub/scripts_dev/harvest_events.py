"""Harvest StubHub event grids via the site's own GetFilteredEvents API.

Drives a real Chromium (DataDome requires a real browser session), visits each
category/grouping page once to learn its exact grid-request params, then
re-issues that request with pagination (pageIndex=0..N) in-page to pull the
structured event JSON the live site serves.

Output: scraped_data/events/<source>__p<idx>.json (raw API responses,
gitignored build-time captures).
"""
import json
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).resolve().parents[1]
OUT = SITE / "scraped_data" / "events"
OUT.mkdir(parents=True, exist_ok=True)

# (source_name, page_url) — top categories + subcategories + league groupings.
TARGETS = [
    ("concerts", "https://www.stubhub.com/concert-tickets/category/1"),
    ("sports_tennis", "https://www.stubhub.com/tennis-tickets/category/7667"),
    ("sports_golf", "https://www.stubhub.com/golf-tickets/category/111"),
    ("sports_fight", "https://www.stubhub.com/fight-tickets/category/7368"),
    ("sports_rodeo", "https://www.stubhub.com/rodeo-tickets/category/6979"),
    ("grouping_nfl", "https://www.stubhub.com/nfl-tickets/grouping/121"),
    ("grouping_mlb", "https://www.stubhub.com/mlb-tickets/grouping/81"),
    ("grouping_nba", "https://www.stubhub.com/nba-tickets/grouping/115"),
    ("grouping_nhl", "https://www.stubhub.com/nhl-tickets/grouping/144"),
    ("grouping_mls", "https://www.stubhub.com/mls-tickets/grouping/142"),
    ("grouping_wwe", "https://www.stubhub.com/wwe-tickets/grouping/131"),
    ("grouping_college", "https://www.stubhub.com/college-sports-tickets/grouping/198988"),
    ("pop", "https://www.stubhub.com/pop-tickets/category/1502178"),
    ("rock", "https://www.stubhub.com/rock-music-tickets/category/209736"),
    ("hiphop", "https://www.stubhub.com/rap-and-hip-hop-music-tickets/category/195739"),
    ("country", "https://www.stubhub.com/country-tickets/category/1501250"),
    ("metal", "https://www.stubhub.com/heavy-metal-tickets/category/1502004"),
    ("electronic", "https://www.stubhub.com/dance-and-electronic-music-tickets/category/195489"),
    ("comedy", "https://www.stubhub.com/comedy-tickets/category/209"),
    ("musicals", "https://www.stubhub.com/musicals-tickets/category/700188"),
    ("plays", "https://www.stubhub.com/plays-tickets/category/700189"),
    ("family", "https://www.stubhub.com/family-tickets/category/5242"),
    ("classical", "https://www.stubhub.com/classical-music-and-opera-tickets/category/178"),
    ("festivals", "https://www.stubhub.com/music-festival-tickets/category/490277"),
]

# Extra metros: (metro_name, lat, lon). The live site geo-locates to the
# Seattle area from our egress IP; these add breadth like a user switching
# the location picker. radiusTo is in meters (~60 miles).
EXTRA_METROS = [
    ("nyc", "40.7128", "-74.0060"),
    ("la", "34.0522", "-118.2437"),
    ("vegas", "36.1699", "-115.1398"),
]
METRO_SOURCES = ["concerts", "comedy", "grouping_nfl", "grouping_nba"]

MAX_PAGES = 3  # pageIndex 0..2 => up to ~60 events per grid


def harvest_grid(pg, name, base_url, grid_url, metro=None):
    """Re-issue the captured grid request across pages, saving each response."""
    tok = pg.evaluate("document.querySelector('#x-csrf-token') ? document.querySelector('#x-csrf-token').value : null")
    if not tok:
        print(f"  !! no csrf token for {name}")
        return 0
    total = 0
    for page_idx in range(MAX_PAGES):
        url = grid_url
        if "pageIndex=" in url:
            url = url.replace("pageIndex=0", f"pageIndex={page_idx}")
        if metro:
            lat, lon = metro[1], metro[2]
            import re
            url = re.sub(r"lat=[-0-9.]+", f"lat={lat}", url)
            url = re.sub(r"lon=[-0-9.]+", f"lon={lon}", url)
            url = re.sub(r"location=[-0-9.%2C]+", f"location={lat}%2C{lon}", url)
            url = re.sub(r"radiusTo=\d+", "radiusTo=100000", url)
        result = pg.evaluate(
            """async ({url, tok}) => {
                const r = await fetch(url, {method: 'POST',
                    headers: {'content-type': 'application/json', 'x-csrf-token': tok}});
                const ct = r.headers.get('content-type') || '';
                const t = await r.text();
                if (!ct.includes('json')) return {err: 'html', head: t.slice(0, 80)};
                try { return {data: JSON.parse(t)}; } catch (e) { return {err: 'parse'}; }
            }""",
            {"url": url, "tok": tok},
        )
        if "err" in result:
            print(f"  !! {name} p{page_idx}: {result}")
            break
        data = result["data"]
        items = data.get("items") or []
        suffix = f"__{metro[0]}" if metro else ""
        out = OUT / f"{name}{suffix}__p{page_idx}.json"
        out.write_text(json.dumps(data, indent=1))
        total += len(items)
        remaining = data.get("remaining", 0)
        print(f"  {name}{suffix} p{page_idx}: {len(items)} items (total {data.get('totalCount')}, remaining {remaining})")
        if not items or remaining <= 0:
            break
        time.sleep(0.8)
    return total


def main():
    only = sys.argv[1:] or None
    grand = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US",
                                  timezone_id="America/New_York")
        pg = ctx.new_page()
        for name, url in TARGETS:
            if only and name not in only:
                continue
            captured = {}

            def on_request(req, _name=name):
                if "method=GetFilteredEvents" in req.url and _name not in captured:
                    captured[_name] = req.url

            pg.on("request", on_request)
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    pg.wait_for_load_state("networkidle", timeout=30000)
                except Exception:
                    pass
                pg.wait_for_timeout(3500)
            except Exception as e:
                print(f"{name}: page ERR {str(e)[:120]}")
                continue
            finally:
                pg.remove_listener("request", on_request)
            if name not in captured:
                print(f"{name}: no grid request captured")
                continue
            grid_url = captured[name]
            grand += harvest_grid(pg, name, url, grid_url)
            for metro in EXTRA_METROS:
                if name in METRO_SOURCES:
                    grand += harvest_grid(pg, name, url, grid_url, metro=metro)
        browser.close()
    print(f"TOTAL events harvested: {grand}")


if __name__ == "__main__":
    main()
