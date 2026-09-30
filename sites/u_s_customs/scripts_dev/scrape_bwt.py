#!/usr/bin/env python3
"""Phase 6: Border Wait Times API snapshot (bwt.cbp.gov).

The public JSON APIs backing the BWT app:
  /api/bwtmodern/crossingslist   crossing directory
  /api/bwtpublicmod              current wait times (the frozen snapshot)
  /api/bwtwaittimegraph          hourly today/average wait series per crossing

Run: python3.11 scrape_bwt.py
Writes scraped_data/bwt/*.json
"""
import json
import pathlib
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "scraped_data" / "bwt"
OUT.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
ENDPOINTS = {
    "crossingslist": "https://bwt.cbp.gov/api/bwtmodern/crossingslist",
    "waits": "https://bwt.cbp.gov/api/bwtpublicmod",
    "graph": "https://bwt.cbp.gov/api/bwtwaittimegraph",
}


def fetch(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"[retry {i}] {url}: {str(e)[:60]}")
            time.sleep(5 + i * 5)
    raise RuntimeError(f"failed: {url}")


def main():
    for name, url in ENDPOINTS.items():
        out = OUT / f"{name}.json"
        if out.exists():
            data = json.load(open(out))
        else:
            data = fetch(url)
            out.write_text(json.dumps(data, indent=1))
        if isinstance(data, list):
            print(f"[bwt] {name}: {len(data)} records")
        else:
            print(f"[bwt] {name}: keys={list(data)[:5]}")
    # Per-crossing hourly wait-time graphs: /api/bwtwaittimegraph/<port_number>/<date>
    waits = json.load(open(OUT / "waits.json"))
    snapshot_date = waits[0]["date"] if waits else None
    iso_date = None
    if snapshot_date:
        m = __import__("re").match(r"(\d+)/(\d+)/(\d+)", snapshot_date)
        if m:
            iso_date = f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    graphs_dir = OUT / "graphs"
    graphs_dir.mkdir(exist_ok=True)
    ok = fail = 0
    for rec in waits:
        pn = rec["port_number"]
        key = f"{pn}_{rec['crossing_name']}".replace(" ", "_").replace("/", "-")
        out = graphs_dir / f"{key}.json"
        if out.exists():
            ok += 1
            continue
        url = (f"https://bwt.cbp.gov/api/bwtwaittimegraph/{pn}/{iso_date}")
        try:
            data = fetch(url)
            if data and isinstance(data, list) and data[0].get("port_name"):
                out.write_text(json.dumps(data, indent=1))
                ok += 1
            else:
                fail += 1
        except Exception:
            fail += 1
        time.sleep(0.5)
    print(f"[bwt] graphs: {ok} ok, {fail} fail")
    print("[bwt] done")


if __name__ == "__main__":
    main()
