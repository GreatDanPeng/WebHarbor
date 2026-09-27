"""Harvest StubHub event pages: listings, seat map SVG, performer links, meta.

Visits each selected event page with a real Chromium (DataDome), extracts the
server-rendered listing cards, the inline seat-map SVG (per venue), performer
links, price filters, and event metadata. The ?quantity=N variant of the same
page yields a different first-10 listing slice, giving deeper inventories
without needing the blocked "Show more" API.

Output: scraped_data/event_pages/<eventId>.json (+ <eventId>.html),
        scraped_data/seatmaps/<venueId>.svg
"""
import json
import pathlib
import re
import sys
import time

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).resolve().parents[1]
SCRAP = SITE / "scraped_data"
OUT = SCRAP / "event_pages"
OUT.mkdir(parents=True, exist_ok=True)
SEATMAPS = SCRAP / "seatmaps"
SEATMAPS.mkdir(parents=True, exist_ok=True)

EXTRACT_JS = """() => {
  const q = (sel) => document.querySelector(sel);
  const qa = (sel) => [...document.querySelectorAll(sel)];
  const out = {};
  out.url = location.href;
  out.title = document.title;
  out.heading = q('h1') ? q('h1').innerText : null;
  // event meta line (date - venue)
  out.eventMeta = qa('h1').map(e => e.parentElement.innerText).join(' | ').slice(0, 300);
  // performer / category links
  out.performerLinks = qa('a[href*="/performer/"], a[href*="/category/"], a[href*="/grouping/"]')
      .map(a => ({t: (a.innerText||'').replace(/\\s+/g,' ').slice(0,60), h: a.getAttribute('href')}));
  // hero image
  const ogImg = q('meta[property="og:image"]');
  out.ogImage = ogImg ? ogImg.content : null;
  // seat map svg
  const svg = qa('svg').find(s => s.innerHTML.includes('STAGE') || (s.innerHTML.match(/<text/g)||[]).length > 5);
  out.seatMapSvg = svg ? svg.outerHTML : null;
  out.seatMapLabels = svg ? svg.querySelectorAll('text').length : 0;
  // filters: price range text
  const bodyText = document.body.innerText;
  const pm = bodyText.match(/\\$([\\d,]+)\\s*\\n?\\$([\\d,]+)\\+/);
  out.priceRangeText = pm ? [pm[1], pm[2]] : null;
  const vm = bodyText.match(/View (\\d+) Listings/);
  out.viewListingsCount = vm ? parseInt(vm[1]) : null;
  const sm = bodyText.match(/Showing (\\d+) of (\\d+)/);
  out.showing = sm ? [parseInt(sm[1]), parseInt(sm[2])] : null;
  // availability banner
  const avail = bodyText.match(/(Only \\d+% of tickets left|Almost sold out|Tickets available|Sold out)/);
  out.availability = avail ? avail[1] : null;
  // listing cards
  out.listings = qa('[data-listing-id]').map(card => ({
    id: card.getAttribute('data-listing-id'),
    label: card.getAttribute('aria-label'),
    price: card.getAttribute('data-price'),
    featureId: card.getAttribute('data-feature-id'),
    img: (card.querySelector('img[data-vfs-image]')||{}).src || null,
    text: card.innerText.replace(/\\n+/g, ' | ').slice(0, 400),
  }));
  // nearby events
  out.nearby = qa('a[href*="/event/"]').map(a => ({t: (a.innerText||'').replace(/\\s+/g,' ').slice(0,60), h: a.getAttribute('href')}));
  return out;
}"""


def harvest_event(pg, event_id, url, quantities=(None,)):
    result = {"eventId": event_id, "url": url, "passes": {}}
    for qty in quantities:
        target = url if qty is None else re.sub(r"[?&]quantity=\d+", "", url) + f"?quantity={qty}"
        try:
            pg.goto(target, wait_until="domcontentloaded", timeout=60000)
            try:
                pg.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            pg.wait_for_timeout(2500)
            data = pg.evaluate(EXTRACT_JS)
        except Exception as e:
            print(f"  {event_id} qty={qty} ERR {str(e)[:120]}", flush=True)
            continue
        key = "any" if qty is None else f"q{qty}"
        result["passes"][key] = data
        n = len(data.get("listings") or [])
        print(f"  {event_id} {key}: {n} listings, showing={data.get('showing')}, svg={len(data.get('seatMapSvg') or '')}", flush=True)
        time.sleep(0.6)
    return result


def save_seatmap(data, venue_id):
    if not data.get("seatMapSvg"):
        return
    path = SEATMAPS / f"{venue_id}.svg"
    if path.exists():
        return
    # pull the svg outerHTML from the page object is not possible post-hoc;
    # extracted below in main() via a second evaluate when needed.


def main():
    events_file = SCRAP / "selected_events.json"
    selected = json.loads(events_file.read_text())
    only_ids = set(sys.argv[1:]) or None
    deep = set()  # eventIds that get quantity passes
    deep_file = SCRAP / "deep_events.json"
    if deep_file.exists():
        deep = {r["eventId"] for r in json.loads(deep_file.read_text())}

    done = {int(p.stem) for p in OUT.glob("*.json")}
    todo = [e for e in selected if e["eventId"] not in done and (not only_ids or str(e["eventId"]) in only_ids)]
    print(f"{len(done)} already harvested, {len(todo)} to go")
    if not todo:
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US",
                                  timezone_id="America/New_York")
        pg = ctx.new_page()
        for ev in todo:
            eid = ev["eventId"]
            quantities = (None, 1, 2, 4) if eid in deep else (None,)
            res = harvest_event(pg, eid, ev["url"], quantities)
            if not res["passes"]:
                continue
            # save seat map svg for the venue from the first pass
            first_pass = next(iter(res["passes"].values()))
            svg_html = first_pass.get("seatMapSvg")
            if svg_html and ev.get("venueId") and not (SEATMAPS / f"{ev['venueId']}.svg").exists():
                (SEATMAPS / f"{ev['venueId']}.svg").write_text(svg_html)
                print(f"  seatmap saved for venue {ev['venueId']} ({len(svg_html)} bytes)", flush=True)
            out = OUT / f"{eid}.json"
            out.write_text(json.dumps(res, indent=1))
            time.sleep(0.6)
        browser.close()
    print("done", flush=True)


if __name__ == "__main__":
    main()
