#!/usr/bin/env python3
"""Scrape the official USPS Postmaster Finder (webpmt.usps.gov) directory.

about.usps.com's Postmaster Finder backs its search pages with a JSON API
that lists real Post Offices with their ZIP Codes, states, establishment
and discontinuance dates. This captures:

  * the full Post Office list for a curated set of states (small states
    plus DC), giving country-wide regional coverage
  * ZIP-3-prefix slices for major metro areas
  * postmaster rosters (by-city) for the directory's featured cities

Output: source_data/post_offices.json

Run from sites/usps:  python3 scripts_dev/scrape_pmf.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "source_data" / "post_offices.json"
BASE = "https://webpmt.usps.gov/postmaster-finder"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "application/json",
}

# Full states (smaller rosters keep the capture focused but broad), plus
# metro ZIP-3 slices for the biggest markets.
STATES = ["DELAWARE", "RHODE ISLAND", "VERMONT", "WYOMING", "MONTANA",
          "NEW HAMPSHIRE", "MAINE", "HAWAII", "ALASKA", "WEST VIRGINIA",
          "DISTRICT OF COLUMBIA", "CONNECTICUT", "IDAHO", "NEW MEXICO",
          "SOUTH DAKOTA", "NORTH DAKOTA"]
ZIP3 = [("900", "902"), ("100", "102"), ("606", "608"), ("331", "333"),
        ("733", "734"), ("981", "982"), ("021", "022"), ("191", "192"),
        ("303", "304"), ("852", "853"), ("752", "753"), ("336", "337")]
CITIES = [("BEVERLY HILLS", "CALIFORNIA"), ("NEW YORK", "NEW YORK"),
          ("CHICAGO", "ILLINOIS"), ("MIAMI", "FLORIDA"),
          ("SEATTLE", "WASHINGTON"), ("DENVER", "COLORADO"),
          ("ATLANTA", "GEORGIA"), ("BOSTON", "MASSACHUSETTS"),
          ("SAN FRANCISCO", "CALIFORNIA"), ("PORTLAND", "OREGON"),
          ("AUSTIN", "TEXAS"), ("PHOENIX", "ARIZONA"),
          ("DETROIT", "MICHIGAN"), ("MINNEAPOLIS", "MINNESOTA"),
          ("PHILADELPHIA", "PENNSYLVANIA"), ("NEW ORLEANS", "LOUISIANA"),
          ("CHARLOTTE", "NORTH CAROLINA"), ("SALT LAKE CITY", "UTAH")]


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)
    out = {"states": {}, "zip_slices": {}, "postmasters": {}}
    seen = set()

    def add_zip(rows, bucket):
        kept = 0
        for row in rows:
            key = (row.get("post-office"), row.get("zip"), row.get("state"))
            if key in seen:
                continue
            seen.add(key)
            bucket.append(row)
            kept += 1
        return kept

    total = 0
    for state in STATES:
        r = session.get(f"{BASE}/by-state", params={"state": state}, timeout=60)
        r.raise_for_status()
        rows = r.json().get("postoffices", [])
        bucket = []
        add_zip(rows, bucket)
        out["states"][state] = bucket
        total += len(bucket)
        print(f"[pmf] {state}: {len(rows)} rows, {len(bucket)} new")
        time.sleep(0.4)

    for lo, hi in ZIP3:
        r = session.get(f"{BASE}/by-zip", params={"from": lo, "to": hi}, timeout=60)
        r.raise_for_status()
        data = r.json()
        rows = data.get("postoffices", [])
        bucket = []
        add_zip(rows, bucket)
        out["zip_slices"][f"{lo}-{hi}"] = bucket
        total += len(bucket)
        print(f"[pmf] zip {lo}-{hi}: {len(rows)} rows, {len(bucket)} new")
        time.sleep(0.4)

    for city, state in CITIES:
        r = session.get(f"{BASE}/by-city-v2",
                        params={"city": city, "state": state}, timeout=60)
        r.raise_for_status()
        data = r.json()
        postmasters = []
        for key, entry in (data.get("postoffices") or {}).items():
            po = entry.get("postoffice") or {}
            pms = entry.get("postmasters") or []
            postmasters.append({
                "post_office": po.get("name"),
                "county": po.get("county"),
                "state": po.get("state"),
                "estab": po.get("estab"),
                "discont": po.get("discont"),
                "roster": [{"date": p.get("date"), "name": p.get("name"),
                            "title": p.get("title")} for p in pms][:12],
            })
        out["postmasters"][f"{city}, {state}"] = postmasters
        print(f"[pmf] {city}, {state}: {len(postmasters)} post office rosters")
        time.sleep(0.4)

    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"[pmf] wrote {OUT}: {total} unique post offices, "
          f"{len(out['postmasters'])} postmaster rosters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
