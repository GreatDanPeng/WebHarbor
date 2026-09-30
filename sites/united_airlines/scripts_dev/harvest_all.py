#!/usr/bin/env python3
"""Single-queue harvest of every real united.com snapshot we need.

All fetches go through ONE serialized queue with adaptive pacing so the
Internet Archive rate limits stay happy:

  1. SDL CMS page payloads (content copy for every mirror page).
  2. Airport lookup payloads (the mirror's airport universe).
  3. Flight-status API payloads: status (per-flight), trip (per-route),
     amenities, upgradeListExtended.

Every successful fetch is persisted under scraped_data/ with a sidecar
.meta.json (upstream URL + sha256). Re-runs skip anything already fetched.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import harvest  # noqa: E402
from harvest import SCRAPED  # noqa: E402

# ---------------------------------------------------------------- manifest --


def sdl_queue() -> list[tuple[str, str, str]]:
    rows = []
    for line in (SCRAPED / 'sdl_manifest.txt').read_text().splitlines():
        stamp, url = line.split(' ', 1)
        page = urllib.parse.parse_qs(
            urllib.parse.urlsplit(url).query)['page'][0]
        name = 'sdl' + page.replace('/ual/en/us/fly', '').replace('/', '_')
        rows.append((name, url, stamp))
    return rows


def flight_queue() -> list[tuple[str, str, str]]:
    rows = []
    # status (per flight number)
    for line in (SCRAPED / 'flightstatus_manifest.txt').read_text().splitlines():
        if not line.strip():
            continue
        stamp, url = line.split('|', 1)
        fn = url.split('/status/')[1].split('/')[0]
        rows.append((f'flightstatus_{fn}.json', url, stamp))
    # trip (per route, real same-day schedule)
    for line in (SCRAPED / 'flighttrip_manifest.txt').read_text().splitlines():
        if not line.strip():
            continue
        stamp, url = line.split('|', 1)
        part = url.split('/trip/')[1].split('?')[0]
        rows.append((f'flighttrip_{part.replace("/", "_")}.json', url, stamp))
    # amenities (per flight + route, aircraft amenities)
    for line in (SCRAPED / 'amenities_manifest.txt').read_text().splitlines():
        if not line.strip():
            continue
        stamp, url = line.split('|', 1)
        part = url.split('/amenities/')[1].split('?')[0]
        rows.append((f'amenities_{part.replace("/", "_")}.json', url, stamp))
    # upgrade list (per flight)
    for line in (SCRAPED / 'upgradelist_manifest.txt').read_text().splitlines():
        if not line.strip():
            continue
        stamp, url = line.split('|', 1)
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        key = f"{qs['flightNumber'][0]}_{qs['flightDate'][0]}"
        rows.append((f'upgradelist_{key}.json', url, stamp))
    return rows


def airport_queue() -> list[tuple[str, str, str]]:
    rows = []
    for line in (SCRAPED / 'airport_codes.txt').read_text().split():
        code = line.strip()
        url = (f'https://www.united.com/api/airports/lookup/?airport={code}'
               '&allAirports=true&matches=0')
        rows.append((f'airport_{code}.json', url, '2025'))
    return rows


# ------------------------------------------------------------------- runner --

def run(queue: list[tuple[str, str, str]], kind: str) -> None:
    total = len(queue)
    done = 0
    for name, url, stamp in queue:
        target = SCRAPED / name
        if target.exists():
            done += 1
            continue
        print(f'[{kind} {done + 1}/{total}] {name}', flush=True)
        harvest.harvest(name, url, stamp)
        done += 1
    print(f'[{kind}] queue complete: {done}/{total}', flush=True)


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('sdl', 'all'):
        run(sdl_queue(), 'sdl')
    if which in ('flights', 'all'):
        run(flight_queue(), 'flights')
    if which in ('airports', 'all'):
        run(airport_queue(), 'airports')
    if which == 'status':
        print(json.dumps({
            'sdl': len(list(SCRAPED.glob('sdl_*'))),
            'flightstatus': len(list(SCRAPED.glob('flightstatus_*.json'))),
            'flighttrip': len(list(SCRAPED.glob('flighttrip_*.json'))),
            'amenities': len(list(SCRAPED.glob('amenities_*.json'))),
            'upgradelist': len(list(SCRAPED.glob('upgradelist_*.json'))),
            'airports': len(list(SCRAPED.glob('airport_*.json'))),
        }, indent=1))
