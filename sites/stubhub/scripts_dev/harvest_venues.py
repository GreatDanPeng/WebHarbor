"""Harvest venue info (JSON-LD) for marquee events missing from grid captures.

For each event in marquee_urls.json that is NOT in the grid-derived catalog,
visit the event page and extract the schema.org JSON-LD block: event name,
startDate, venue name + venue URL (venue id), address. Saves to
scraped_data/event_venue/<eid>.json. Skips already-done ids.
"""
import json, pathlib, re, time
from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).resolve().parents[1]
SCRAP = SITE / "scraped_data"
OUT = SCRAP / "event_venue"
OUT.mkdir(exist_ok=True)

LD_JS = """() => {
  const blocks = [...document.querySelectorAll('script[type="application/ld+json"]')];
  for (const b of blocks) {
    try {
      const d = JSON.parse(b.textContent);
      const ev = Array.isArray(d) ? d.find(x => /Event$/.test(x['@type'] || '')) : (/Event$/.test(d['@type'] || '') ? d : null);
      if (ev) {
        const v = ev.location || {};
        const addr = (v.address && (typeof v.address === 'object')) ? v.address : {};
        return {
          type: ev['@type'],
          name: ev.name, startDate: ev.startDate,
          venueName: v.name, venueUrl: v.url,
          street: addr.streetAddress, city: addr.addressLocality,
          state: addr.addressRegion, country: addr.addressCountry,
        };
      }
    } catch (e) {}
  }
  return null;
}"""


def main():
    import glob
    marquee = json.loads((SCRAP / "marquee_urls.json").read_text())
    # catalog ids from grid captures
    grid_ids = set()
    for f in glob.glob(str(SCRAP / "events" / "*.json")):
        for it in json.loads(pathlib.Path(f).read_text()).get("items", []):
            grid_ids.add(it["eventId"])
    done = {int(p.stem) for p in OUT.glob("*.json")}
    todo = [(int(k), v) for k, v in sorted(marquee.items(), key=lambda kv: int(kv[0]))
            if int(k) not in grid_ids and int(k) not in done]
    print(f"{len(done)} done, {len(todo)} to harvest")
    if not todo:
        print("done")
        return
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US",
                                  timezone_id="America/New_York")
        pg = ctx.new_page()
        for eid, url in todo:
            for attempt in range(3):
                try:
                    pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                    try:
                        pg.wait_for_load_state("networkidle", timeout=20000)
                    except Exception:
                        pass
                    pg.wait_for_timeout(2500)
                    ld = pg.evaluate(LD_JS)
                    if ld:
                        (OUT / f"{eid}.json").write_text(json.dumps(ld, indent=1))
                        print(f"  {eid}: {ld['venueName']} | {ld['startDate']}", flush=True)
                        break
                    print(f"  {eid}: no JSON-LD (blocked?)", flush=True)
                except Exception as e:
                    print(f"  {eid} ERR {str(e)[:80]}", flush=True)
                    pg = ctx.new_page()  # fresh page on error
                time.sleep(3)
            time.sleep(1.0)
        browser.close()
    print("done", flush=True)


if __name__ == "__main__":
    main()
