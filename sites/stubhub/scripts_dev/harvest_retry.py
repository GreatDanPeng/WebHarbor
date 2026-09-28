"""Retry the supplementary captures that hit network/anti-bot failures."""
import json, pathlib, re, sys, time
from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).resolve().parents[1]
SCRAP = SITE / "scraped_data"
sys.path.insert(0, str(SITE / "scripts_dev"))
from harvest_event_pages import EXTRACT_JS, harvest_event  # noqa: E402

DEEP_MARQUEE = [160572545, 160569378, 160611325, 160611244,
                160436504, 160436498, 160436501, 159502859, 159662072]
PERFORMER_PAGES = [
    ("metallica", "https://www.stubhub.com/metallica-tickets/performer/8147"),
    ("seattle-seahawks", "https://www.stubhub.com/seattle-seahawks-tickets/performer/1945"),
    ("seattle-kraken", "https://www.stubhub.com/seattle-kraken-tickets/performer/50668503"),
    ("rush", "https://www.stubhub.com/rush-tickets/performer/5324"),
    ("katseye", "https://www.stubhub.com/katseye-tickets/category/150357413"),
    ("olivia-rodrigo", "https://www.stubhub.com/olivia-rodrigo-tickets/performer/101864867"),
    ("seattle-mariners", "https://www.stubhub.com/seattle-mariners-tickets/performer/1043"),
    ("seattle-sounders-fc", "https://www.stubhub.com/seattle-sounders-fc-tickets/performer/388488"),
    ("tyler-childers", "https://www.stubhub.com/tyler-childers-tickets/performer/1523387"),
    ("gorillaz", "https://www.stubhub.com/gorillaz-tickets/performer/4262"),
    ("oasis", "https://www.stubhub.com/oasis-tickets/performer/2388"),
    ("sting", "https://www.stubhub.com/sting-tickets/performer/2909"),
    ("billy-strings", "https://www.stubhub.com/billy-strings-tickets/performer/1521415"),
    ("the-chicks", "https://www.stubhub.com/the-chicks-tickets/performer/236"),
]

def performer_pass(pg, slug, url):
    try:
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=25000)
        except Exception:
            pass
        pg.wait_for_timeout(3000)
        data = pg.evaluate(EXTRACT_JS)
        bio = pg.evaluate("""() => {
            const paras = [...document.querySelectorAll('p')];
            const bioPara = paras.find(p => p.innerText && p.innerText.length > 300);
            return bioPara ? bioPara.innerText.slice(0, 2500) : null;
        }""")
        if not bio or len(bio) < 200:
            # performers pages put the bio deeper; try any long text block
            bio = pg.evaluate("""() => {
                const txt = document.body.innerText;
                const i = txt.search(/\\n\\n[A-Z].{300,}/s);
                return i > 0 ? txt.slice(i + 2, i + 2500) : null;
            }""")
        followers = pg.evaluate("""() => {
            const m = document.body.innerText.match(/([\\d.,]+[KM]?)\\s*(?:\\n|$)/);
            const mm = document.body.innerText.match(/Follow\\s*\\n\\s*([\\d.,]+[KM]?)/);
            return (mm && mm[1]) || (m && m[1]) || null;
        }""")
        data["bio"] = bio
        data["followers"] = followers
        (SCRAP / "performers" / f"{slug}.json").write_text(json.dumps(data, indent=1))
        print(f"  performer {slug}: bio={len(bio or '')} followers={followers}", flush=True)
        return True
    except Exception as e:
        print(f"  performer {slug} ERR {str(e)[:90]}", flush=True)
        return False

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    marquee = json.loads((SCRAP / "marquee_urls.json").read_text())
    done_pages = {int(p.stem) for p in (SCRAP / "event_pages").glob("*.json")}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(viewport={"width":1440,"height":900}, locale="en-US",
                                  timezone_id="America/New_York")
        pg = ctx.new_page()
        if which in ("all", "events"):
            seatmaps = SCRAP / "seatmaps"
            for eid, url in sorted(marquee.items(), key=lambda kv: int(kv[0])):
                eid = int(eid)
                if eid in done_pages:
                    continue
                for attempt in range(2):
                    res = harvest_event(pg, eid, url, (None, 1, 2, 4) if eid in DEEP_MARQUEE else (None,))
                    if res["passes"]:
                        first = next(iter(res["passes"].values()))
                        if first.get("seatMapSvg"):
                            (seatmaps / f"event_{eid}.svg").write_text(first["seatMapSvg"])
                        (SCRAP / "event_pages" / f"{eid}.json").write_text(json.dumps(res, indent=1))
                        done_pages.add(eid)
                        break
                    time.sleep(4)
                time.sleep(1.2)
        if which in ("all", "performers"):
            for slug, url in PERFORMER_PAGES:
                f = SCRAP / "performers" / f"{slug}.json"
                need = True
                if f.exists():
                    d = json.loads(f.read_text())
                    need = not (d.get("bio") or d.get("eventMeta", "").strip() != d.get("title", "x")[:20])
                if not need:
                    continue
                for attempt in range(2):
                    if performer_pass(pg, slug, url):
                        break
                    time.sleep(4)
                time.sleep(1.2)
        browser.close()
    print("done", flush=True)

if __name__ == "__main__":
    main()
