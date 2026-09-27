"""Supplementary harvest: extra grids, marquee event pages, performer bios.

Round 2 of the capture pass:
  1. more grid pages (concerts Seattle pages 3-8; NFL/NBA/NHL/MLB at more
     metros) so the catalog covers marquee events the first pass missed;
  2. deep event pages for the marquee events collected during recon
     (Metallica at Sphere, Seahawks home games, Doja Cat, Rush, ...);
  3. performer pages for the top performers (bios + follower counts).

Output: scraped_data/events/*.json, scraped_data/event_pages/*.json,
        scraped_data/performers/<slug>.json, scraped_data/seatmaps/*.svg
"""
import json
import pathlib
import re
import sys
import time

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).resolve().parents[1]
SCRAP = SITE / "scraped_data"

EXTRA_GRIDS = [
    # (source, page_url, pages, metro or None)
    ("concerts", "https://www.stubhub.com/concert-tickets/category/1", (3, 4, 5, 6, 7), None),
    ("concerts", "https://www.stubhub.com/concert-tickets/category/1", (3, 4), ("chicago", "41.8781", "-87.6298")),
    ("grouping_nfl", "https://www.stubhub.com/nfl-tickets/grouping/121", (0, 1), ("sf", "37.7749", "-122.4194")),
    ("grouping_nfl", "https://www.stubhub.com/nfl-tickets/grouping/121", (0, 1), ("dallas", "32.7767", "-96.797")),
    ("grouping_nfl", "https://www.stubhub.com/nfl-tickets/grouping/121", (0, 1), ("miami", "25.7617", "-80.1918")),
    ("grouping_nfl", "https://www.stubhub.com/nfl-tickets/grouping/121", (0, 1), ("denver", "39.7392", "-104.9903")),
    ("grouping_nfl", "https://www.stubhub.com/nfl-tickets/grouping/121", (0, 1), ("boston", "42.3601", "-71.0589")),
    ("grouping_nba", "https://www.stubhub.com/nba-tickets/grouping/115", (0, 1), ("sf", "37.7749", "-122.4194")),
    ("grouping_nba", "https://www.stubhub.com/nba-tickets/grouping/115", (0, 1), ("chicago", "41.8781", "-87.6298")),
    ("grouping_nhl", "https://www.stubhub.com/nhl-tickets/grouping/144", (0, 1), ("chicago", "41.8781", "-87.6298")),
    ("grouping_mlb", "https://www.stubhub.com/mlb-tickets/grouping/81", (0, 1), ("sf", "37.7749", "-122.4194")),
    ("grouping_mlb", "https://www.stubhub.com/mlb-tickets/grouping/81", (0, 1), ("nyc", "40.7128", "-74.0060")),
]

# Marquee events collected during recon (see scraped_data/marquee_urls.json).
DEEP_MARQUEE = [
    160572545, 160569378, 160611325, 160611244,  # Metallica at Sphere
    160436504, 160436498, 160436501,            # Seahawks home games
    159502859,                                    # Doja Cat Seattle
    159662072,                                    # Rush Seattle
    161041547, 161137440, 161301917, 160913642,   # Olivia Rodrigo / KATSEYE / Phoebe / Teddy
]
SHALLOW_MARQUEE = "all"  # every other marquee URL gets a single pass

# Performer pages to harvest (bio + follower counts).
PERFORMER_PAGES = [
    ("metallica", "https://www.stubhub.com/metallica-tickets/performer/8147"),
    ("seattle-seahawks", "https://www.stubhub.com/seattle-seahawks-tickets/performer/1945"),
    ("seattle-kraken", "https://www.stubhub.com/seattle-kraken-tickets/performer/50668503"),
    ("seattle-mariners", "https://www.stubhub.com/seattle-mariners-tickets/performer/1043"),
    ("seattle-sounders-fc", "https://www.stubhub.com/seattle-sounders-fc-tickets/performer/388488"),
    ("olivia-rodrigo", "https://www.stubhub.com/olivia-rodrigo-tickets/performer/101864867"),
    ("doja-cat", "https://www.stubhub.com/doja-cat-tickets/performer/100309986"),
    ("rush", "https://www.stubhub.com/rush-tickets/performer/5324"),
    ("tyler-childers", "https://www.stubhub.com/tyler-childers-tickets/performer/1523387"),
    ("luke-bryan", "https://www.stubhub.com/luke-bryan-tickets/performer/377761"),
    ("billy-strings", "https://www.stubhub.com/billy-strings-tickets/performer/1521415"),
    ("sting", "https://www.stubhub.com/sting-tickets/performer/2909"),
    ("the-chicks", "https://www.stubhub.com/the-chicks-tickets/performer/236"),
    ("phoebe-bridgers", "https://www.stubhub.com/phoebe-bridgers-tickets/performer/1515068"),
    ("teddy-swims", "https://www.stubhub.com/teddy-swims-tickets/category/101075469"),
    ("katseye", "https://www.stubhub.com/katseye-tickets/category/150357413"),
    ("gorillaz", "https://www.stubhub.com/gorillaz-tickets/performer/4262"),
    ("oasis", "https://www.stubhub.com/oasis-tickets/performer/2388"),
    ("jack-johnson", "https://www.stubhub.com/jack-johnson-tickets/performer/3762"),
    ("washington-huskies-football", "https://www.stubhub.com/washington-huskies-football-tickets/performer/2428"),
    ("washington-state-cougars-football", "https://www.stubhub.com/washington-state-cougars-football-tickets/performer/6887"),
    ("big-thief", "https://www.stubhub.com/big-thief-tickets/performer/1514273"),
    ("malcolm-todd", "https://www.stubhub.com/malcolm-todd-tickets/performer/150111662"),
    ("brett-goldstein", "https://www.stubhub.com/brett-goldstein-tickets/performer/150049347"),
    ("the-neighbourhood", "https://www.stubhub.com/the-neighbourhood-tickets/performer/728195"),
    ("sombr", "https://www.stubhub.com/sombr-tickets/performer/150164108"),
    ("hayley-williams", "https://www.stubhub.com/hayley-williams-tickets/performer/150603547"),
]

sys.path.insert(0, str(SITE / "scripts_dev"))
from harvest_event_pages import EXTRACT_JS, harvest_event  # noqa: E402


def grid_pass(pg, name, base_url, grid_url, page_idx, metro, retries=2):
    url = grid_url.replace("pageIndex=0", f"pageIndex={page_idx}")
    if metro:
        _, lat, lon = metro
        url = re.sub(r"lat=[-0-9.]+", f"lat={lat}", url)
        url = re.sub(r"lon=[-0-9.]+", f"lon={lon}", url)
        url = re.sub(r"location=[-0-9.%2C]+", f"location={lat}%2C{lon}", url)
        url = re.sub(r"radiusTo=\d+", "radiusTo=100000", url)
    for attempt in range(retries + 1):
        try:
            tok = pg.evaluate("document.querySelector('#x-csrf-token') ? document.querySelector('#x-csrf-token').value : null")
            if not tok:
                raise RuntimeError("no csrf token")
            result = pg.evaluate(
                """async ({url, tok}) => {
                    const r = await fetch(url, {method: 'POST',
                        headers: {'content-type': 'application/json', 'x-csrf-token': tok}});
                    const ct = r.headers.get('content-type') || '';
                    const t = await r.text();
                    if (!ct.includes('json')) return {err: 'html'};
                    try { return {data: JSON.parse(t)}; } catch (e) { return {err: 'parse'}; }
                }""", {"url": url, "tok": tok})
        except Exception as e:
            print(f"  {name} p{page_idx} attempt{attempt}: {str(e)[:80]}", flush=True)
            try:
                pg.goto(base_url, wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_timeout(3500)
            except Exception:
                pass
            continue
        if "err" in result:
            print(f"  {name} p{page_idx}: {result['err']}", flush=True)
            return
        data = result["data"]
        suffix = f"__{metro[0]}" if metro else ""
        out = SCRAP / "events" / f"{name}{suffix}__p{page_idx}.json"
        out.write_text(json.dumps(data, indent=1))
        print(f"  {name}{suffix} p{page_idx}: {len(data.get('items') or [])} items", flush=True)
        return


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    marquee = json.loads((SCRAP / "marquee_urls.json").read_text())
    done_pages = {int(p.stem) for p in (SCRAP / "event_pages").glob("*.json")}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US",
                                  timezone_id="America/New_York")
        page = ctx.new_page()

        if which in ("all", "grids"):
            for name, url, pages, metro in EXTRA_GRIDS:
                captured = {}
                def on_request(req, _name=name):
                    if "method=GetFilteredEvents" in req.url and _name not in captured:
                        captured[_name] = req.url
                page.on("request", on_request)
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=25000)
                    except Exception:
                        pass
                    page.wait_for_timeout(2500)
                except Exception as e:
                    print(f"{name}: page ERR {str(e)[:100]}", flush=True)
                    continue
                finally:
                    page.remove_listener("request", on_request)
                if name not in captured:
                    print(f"{name}: no grid request", flush=True)
                    continue
                for pi in pages:
                    grid_pass(page, name, url, captured[name], pi, metro)
                    time.sleep(0.5)

        if which in ("all", "events"):
            seatmaps = SCRAP / "seatmaps"
            for eid, url in sorted(marquee.items(), key=lambda kv: int(kv[0])):
                eid = int(eid)
                if eid in done_pages:
                    continue
                quantities = (None, 1, 2, 4) if eid in DEEP_MARQUEE else (None,)
                res = harvest_event(page, eid, url, quantities)
                if not res["passes"]:
                    continue
                first = next(iter(res["passes"].values()))
                svg = first.get("seatMapSvg")
                m = re.search(r"venue/(\d+)", first.get("url") or "") or re.search(r"venue/(\d+)", url)
                # venue id unknown here; store svg keyed by event for later mapping
                if svg:
                    (seatmaps / f"event_{eid}.svg").write_text(svg)
                out = SCRAP / "event_pages" / f"{eid}.json"
                out.write_text(json.dumps(res, indent=1))
                time.sleep(0.5)

        if which in ("all", "performers"):
            pout = SCRAP / "performers"
            pout.mkdir(exist_ok=True)
            for slug, url in PERFORMER_PAGES:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=25000)
                    except Exception:
                        pass
                    page.wait_for_timeout(2500)
                    data = page.evaluate(EXTRACT_JS)
                    bio = page.evaluate("""() => {
                        const paras = [...document.querySelectorAll('p')];
                        const bioPara = paras.find(p => p.innerText && p.innerText.length > 400);
                        return bioPara ? bioPara.innerText.slice(0, 2500) : null;
                    }""")
                    followers = page.evaluate("""() => {
                        const m = document.body.innerText.match(/([\\d,]+[KM]?)\\s*\\n?\\s*\\d[\\d,]* people viewed/);
                        return m ? m[1] : null;
                    }""")
                    data["bio"] = bio
                    data["followers"] = followers
                    (pout / f"{slug}.json").write_text(json.dumps(data, indent=1))
                    print(f"  performer {slug}: bio={len(bio or '')}", flush=True)
                except Exception as e:
                    print(f"  performer {slug} ERR {str(e)[:100]}", flush=True)
                time.sleep(0.5)

        browser.close()
    print("done", flush=True)


if __name__ == "__main__":
    main()
