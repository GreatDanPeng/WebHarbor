"""Harvest StubHub grouped-search responses for performer discovery + images.

For each query (performer names from the event catalog + a calibration set),
issues the site's own POST /search/groupedsearch?FormatDate=true call from
inside a real browser session, saving the JSON. This yields real performer
IDs, display names, images, and event counts.

Output: scraped_data/search/<slug>.json
"""
import json
import pathlib
import re
import sys
import time

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).resolve().parents[1]
SCRAP = SITE / "scraped_data"
OUT = SCRAP / "search"
OUT.mkdir(parents=True, exist_ok=True)

CALIBRATION_QUERIES = [
    "seahawks", "metallica", "taylor swift", "doja cat", "olivia rodrigo",
    "sounders", "kraken", "mariners", "nutcracker", "hamilton", "comedy",
    "broadway", "concerts seattle", "lakers", "knicks", "sphere",
]


def main():
    slugs = json.loads((SCRAP / "performer_slugs.json").read_text())
    queries = [s.replace("-", " ") for s in slugs]
    queries = CALIBRATION_QUERIES + queries
    only = sys.argv[1:] or None
    if only:
        queries = [q for q in queries if any(o in q for o in only)]

    done = {p.stem for p in OUT.glob("*.json")}
    print(f"{len(done)} already harvested")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US",
                                  timezone_id="America/New_York")
        pg = ctx.new_page()
        pg.goto("https://www.stubhub.com/", wait_until="domcontentloaded", timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(3000)

        for i, query in enumerate(queries):
            key = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
            if key in done:
                continue
            result = pg.evaluate(
                """async (query) => {
                    const tok = document.querySelector('#x-csrf-token')
                        ? document.querySelector('#x-csrf-token').value : null;
                    const fd = new FormData();
                    fd.append('text', query);
                    fd.append('searchGuid', 'A1B2C3D4-E5F6-4789-9ABC-DEF012345678');
                    fd.append('searchType', '2');
                    const r = await fetch('/search/groupedsearch?FormatDate=true',
                        {method: 'POST', body: fd});
                    const ct = r.headers.get('content-type') || '';
                    const t = await r.text();
                    if (!ct.includes('json')) return {err: 'html'};
                    try { return {data: JSON.parse(t)}; } catch (e) { return {err: 'parse'}; }
                }""",
                query,
            )
            if "err" in result:
                print(f"  {query}: {result['err']}", flush=True)
                if result["err"] == "html":
                    # session may have gone stale; re-establish
                    pg.goto("https://www.stubhub.com/", wait_until="domcontentloaded", timeout=60000)
                    pg.wait_for_timeout(3000)
                continue
            (OUT / f"{key}.json").write_text(json.dumps(result["data"], indent=1))
            if i % 25 == 0:
                print(f"  [{i}/{len(queries)}] {query}", flush=True)
            time.sleep(0.35)
        browser.close()
    print("done", flush=True)


if __name__ == "__main__":
    main()
