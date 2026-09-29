#!/usr/bin/env python3
"""Build the tracked source-data snapshots for the united_airlines mirror.

Reads the harvested united.com snapshots under scraped_data/ (gitignored,
build-time only) and writes the tracked, deterministic snapshots that
seed_data.py materializes into SQLite at image build time:

  source_data_airports.json   — the mirror's airport universe, every row from
      a real captured /api/airports/lookup response.
  source_data_flights.json    — the frozen real-flight network: every flight
      (number, route, times, aircraft) extracted from captured
      flight-status / trip API payloads.
  source_data_aircraft.json   — real fleet data per equipment type from the
      upstream aircraft pages + captured amenities payloads (seats per
      cabin, configuration, pitch, wifi, engines, wingspan).
  source_data_content.json    — per-page upstream copy (baggage, cabins,
      MileagePlus, check-in, policies, airports, help, deals) extracted from
      the captured SDL CMS payloads, plus the structured fee/program facts
      used by the interactive flows.

Run from sites/united_airlines/:  python3 scripts_dev/build_source_data.py
"""
from __future__ import annotations

import glob
import json
import pathlib
import re
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
sys.path.insert(0, str(HERE))

from sdl_extract import page_blocks, page_title  # noqa: E402

SCRAPED = SITE / 'scraped_data'
SNAPSHOT_DATE = '2026-09-28'

UA_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L']
HUBS = {'ORD', 'DEN', 'IAH', 'EWR', 'SFO', 'LAX', 'GUM', 'IAD'}

# ------------------------------------------------------------------ airports --


def build_airports() -> dict:
    airports = {}
    # 1. the mapairports API dump (real captured payload with coordinates)
    map_path = SCRAPED / 'mapairports.json'
    if map_path.exists():
        import gzip
        raw = map_path.read_bytes()
        if raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        payload = json.loads(raw)
        for row in payload:
            a = row['Airport']
            code = a.get('IATACode')
            if not code or len(code) != 3 or not code.isalpha() or code in airports:
                continue
            city_block = a.get('IATACityCode') or {}
            addr = a.get('Address') or {}
            country = (a.get('IATACountryCode') or {}).get('Name') or \
                      (addr.get('Country') or {}).get('Name') or ''
            state = ((addr.get('StateProvince') or {}).get('StateProvinceCode')
                     or (city_block.get('StateCode') or {}).get('StateProvinceCode')
                     or '')
            if not (city_block.get('Latitude') and city_block.get('Longitude')):
                continue
            airports[code] = {
                'code': code,
                'name': a.get('Name') or '',
                'city': city_block.get('Name') or addr.get('City') or a.get('Name') or '',
                'state': state,
                'country': country,
                'latitude': float(city_block['Latitude']),
                'longitude': float(city_block['Longitude']),
                'hub': code in HUBS,
            }
    # 2. the per-code lookup captures refine names/state
    for path in sorted(glob.glob(str(SCRAPED / 'airport_*.json'))):
        if path.endswith('.meta.json'):
            continue
        try:
            payload = json.load(open(path))
        except Exception:
            continue
        rows = payload.get('data', {}).get('airports') or []
        for row in rows:
            a = row.get('Airport') or {}
            code = a.get('IATACode')
            if not code or len(code) != 3 or not code.isalpha():
                continue
            if code in airports:
                continue
            city_block = a.get('IATACityCode') or {}
            addr = a.get('Address') or {}
            country = (a.get('IATACountryCode') or {}).get('Name') or \
                      (addr.get('Country') or {}).get('Name') or ''
            state = ((addr.get('StateProvince') or {}).get('StateProvinceCode')
                     or (city_block.get('StateCode') or {}).get('StateProvinceCode')
                     or '')
            name = a.get('Name') or ''
            # "Chicago, IL, US (ORD - O'Hare)" -> city label
            m = re.match(r'^(.*?),?\s*([A-Z]{2})?,?\s*([A-Z]{2,3})\s*\(', name)
            airports[code] = {
                'code': code,
                'name': name,
                'city': city_block.get('Name') or addr.get('City') or name,
                'state': state,
                'country': country,
                'latitude': float(city_block.get('Latitude') or 0),
                'longitude': float(city_block.get('Longitude') or 0),
                'hub': code in HUBS,
            }
    # keep only airports with real coordinates
    airports = {k: v for k, v in airports.items()
                if v['latitude'] and v['longitude']}
    # scope the mirror's universe to United's own network: the curated code
    # list (hubs, domestic and international destinations the frozen flight
    # network and deals reference)
    wanted = set((SCRAPED / 'airport_codes.txt').read_text().split())
    airports = {k: v for k, v in airports.items() if k in wanted}
    # region classification for deals/filters
    for v in airports.values():
        if v['country'] == 'United States':
            v['region'] = 'Domestic'
        elif v['country'] in ('Canada', 'Mexico', 'Bahamas', 'Jamaica',
                              'Costa Rica', 'Panama', 'Aruba', 'Barbados',
                              'Belize', 'Guatemala', 'El Salvador', 'Honduras',
                              'Nicaragua', 'Trinidad and Tobago', 'Cayman Islands',
                              'Puerto Rico', 'U.S. Virgin Islands', 'Curacao',
                              'Antigua and Barbuda', 'Saint Maarten', 'Turks and Caicos'):
            v['region'] = 'Latin America & Caribbean'
        elif v['country'] in ('United Kingdom', 'Ireland', 'Germany', 'France',
                              'Italy', 'Spain', 'Netherlands', 'Belgium',
                              'Switzerland', 'Austria', 'Portugal', 'Denmark',
                              'Norway', 'Sweden', 'Finland', 'Iceland',
                              'Poland', 'Czech Republic', 'Hungary', 'Greece',
                              'Croatia', 'Luxembourg'):
            v['region'] = 'Europe'
        elif v['country'] in ('Japan', 'China', 'South Korea', 'Singapore',
                              'Taiwan', 'Thailand', 'Philippines', 'Vietnam',
                              'Hong Kong', 'India', 'Israel', 'United Arab Emirates',
                              'Australia', 'New Zealand'):
            v['region'] = 'Asia Pacific & Middle East'
        else:
            v['region'] = 'International'
    return airports


# ------------------------------------------------------------------- flights --

def _hmm(value: str):
    m = re.search(r'(\d{2}:\d{2}):\d{2}$', value or '')
    return m.group(1) if m else None


def build_flights(airports: dict) -> list[dict]:
    flights = {}

    def add(number, origin, dest, dep, arr, equipment_key='', equipment_name='',
            status='', gate='', terminal='', source='', board='', tail=''):
        if not (number and origin and dest and dep and arr):
            return
        if origin not in airports or dest not in airports:
            return
        key = (number, origin, dest)
        row = {
            'number': str(number),
            'origin': origin, 'dest': dest,
            'departure': dep, 'arrival': arr,
            'aircraft_key': equipment_key, 'aircraft_name': equipment_name,
            'status': status, 'gate': gate, 'terminal': terminal,
            'tail': tail,
            'source': source,
        }
        if key not in flights or (equipment_key and not flights[key]['aircraft_key']):
            if key in flights and equipment_key:
                flights[key].update(row)
            else:
                flights[key] = row

    # 1. trip captures — real itineraries incl. every connecting segment
    for path in sorted(glob.glob(str(SCRAPED / 'flighttrip_*.json'))):
        if path.endswith('.meta.json'):
            continue
        try:
            payload = json.loads(open(path, 'rb').read())
        except Exception:
            continue
        for rec in payload if isinstance(payload, list) else []:
            for leg in rec.get('FlightLegs') or []:
                for seg in leg.get('OperationalFlightSegments') or []:
                    eq = seg.get('Equipment') or {}
                    model = eq.get('Model') or {}
                    add(seg.get('FlightNumber'),
                        (seg.get('DepartureAirport') or {}).get('IATACode'),
                        (seg.get('ArrivalAirport') or {}).get('IATACode'),
                        _hmm(seg.get('DepartureDateTime')),
                        _hmm(seg.get('ArrivalDateTime')),
                        equipment_key=model.get('Key') or '',
                        equipment_name=model.get('Description') or '',
                        source='flightstatus/trip')

    # 2. status captures — full per-flight ops records
    for path in sorted(glob.glob(str(SCRAPED / 'flightstatus_*.json'))):
        if path.endswith('.meta.json'):
            continue
        try:
            payload = json.loads(open(path, 'rb').read())
        except Exception:
            continue
        legs = (payload.get('data') or {}).get('flightLegs') or []
        for leg in legs:
            for seg in leg.get('OperationalFlightSegments') or []:
                eq = seg.get('Equipment') or {}
                model = eq.get('Model') or {}
                chars = {c.get('Code'): c.get('Value')
                         for c in seg.get('Characteristic') or []}
                dep_airport = seg.get('DepartureAirport') or {}
                arr_airport = seg.get('ArrivalAirport') or {}
                dep = _hmm(seg.get('DepartureDateTime'))
                arr = _hmm(seg.get('ArrivalDateTime'))
                status = 'On time'
                if chars.get('FltCnclInd') == '1':
                    status = 'Canceled'
                elif chars.get('FltDepDvrtInd') == '1':
                    status = 'Diverted'
                elif chars.get('FltDepRTFLInd') == '1':
                    status = 'Delayed'
                elif chars.get('FltInInd') == '1':
                    status = 'Arrived'
                elif chars.get('FltOffInd') == '1':
                    status = 'Departed'
                gate = ''
                for side, prefix in ((dep_airport, 'dep'), (arr_airport, 'arr')):
                    if isinstance(side.get('Gate'), dict):
                        gate = gate or side['Gate'].get('Name', '')
                add(payload.get('data', {}).get('Flight', {}).get('flightNumber')
                    or seg.get('FlightNumber'),
                    dep_airport.get('IATACode'), arr_airport.get('IATACode'),
                    dep, arr,
                    equipment_key=model.get('Key') or '',
                    equipment_name=model.get('Description') or '',
                    status=status, gate=gate,
                    terminal=(dep_airport.get('Terminal') or {}).get('Name', '')
                    if isinstance(dep_airport.get('Terminal'), dict) else '',
                    source='flightstatus/status')

    # 3. amenities captures — real flights, aircraft and cabin amenities
    for path in sorted(glob.glob(str(SCRAPED / 'amenities_*.json'))):
        if path.endswith('.meta.json'):
            continue
        meta_path = pathlib.Path(str(path) + '.meta.json')
        tail = equipment_code = ''
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            qs = urllib.parse.parse_qs(urllib.parse.urlsplit(
                meta.get('upstream_url', '')).query)
            tail = qs.get('tailNumber', [''])[0]
            equipment_code = qs.get('equipmentCode', [''])[0]
        try:
            payload = json.loads(open(path, 'rb').read())
        except Exception:
            continue
        rows = payload if isinstance(payload, list) else [payload]
        for row in rows:
            eq = row.get('Equipment') or {}
            model = eq.get('Model') or {}
            add(row.get('FlightNumber'),
                (row.get('DepartureAirport') or {}).get('IATACode'),
                (row.get('ArrivalAirport') or {}).get('IATACode'),
                None, None,
                equipment_key=model.get('Key') or equipment_code,
                equipment_name=model.get('Description') or '',
                tail=tail, source='flight/amenities')
    # drop partner-marketed legs (4-digit 7xxx/8xxx codeshares) which United
    # does not operate: the mirror's network is United + United Express.
    out = []
    for f in flights.values():
        if f['number'].isdigit() and int(f['number']) >= 7000:
            continue
        out.append(f)
    return out


# ------------------------------------------------------------------ aircraft --

def _letters_for_config(config: str) -> list[str]:
    groups = re.split(r'[-–]', config or '')
    letters = []
    for group in groups:
        try:
            count = int(group.strip())
        except ValueError:
            continue
        letters.extend(UA_LETTERS[len(letters):len(letters) + count])
    return letters or UA_LETTERS[:6]


def _norm_aircraft_name(name: str) -> str:
    n = (name or '').lower()
    n = re.sub(r'\([^)]*\)', '', n)
    n = n.replace('dreamliner', '')
    n = re.sub(r'[^a-z0-9]', '', n)
    return n


def build_aircraft() -> dict:
    """Merge the fleet pages (real seat specs per aircraft type) with the
    captured amenities payloads."""
    aircraft = {}

    def row(key, name):
        if key not in aircraft:
            aircraft[key] = {'key': key, 'name': name, 'description': '',
                             'cabin_specs': [], 'specs': {}, 'features': [],
                             'wifi': '', 'power': 'yes', 'seat_config_code': ''}
        return aircraft[key]

    # 1. amenities / status / trip payloads: per-equipment specs
    # (engines, wingspan, wifi, cabin letter codes)
    for path in sorted(glob.glob(str(SCRAPED / 'amenities_*.json')) +
                       sorted(glob.glob(str(SCRAPED / 'flightstatus_*.json'))) +
                       sorted(glob.glob(str(SCRAPED / 'flighttrip_*.json')))):
        if path.endswith('.meta.json'):
            continue
        try:
            payload = json.loads(open(path, 'rb').read())
        except Exception:
            continue
        rows = []
        if isinstance(payload, list):
            for rec in payload:
                for leg in rec.get('FlightLegs') or []:
                    rows.extend(leg.get('OperationalFlightSegments') or [])
        elif isinstance(payload, dict):
            legs = (payload.get('data') or {}).get('flightLegs') or []
            for leg in legs:
                rows.extend(leg.get('OperationalFlightSegments') or [])
        for seg in rows:
            eq = seg.get('Equipment') or {}
            model = eq.get('Model') or {}
            key = model.get('Key') or ''
            if not key or len(key) > 6 or not re.match(r'^[A-Z0-9]+$', key):
                continue
            entry = row(key, model.get('Description') or key)
            amen = eq.get('Amenities') or {}
            if amen.get('WifiPrvdr'):
                entry['wifi'] = amen['WifiPrvdr']
            if amen and not entry['specs']:
                specs = {}
                for label, value in (('engine', amen.get('EngType')),
                                     ('engines', amen.get('EngCnt')),
                                     ('cruise_speed_mph', amen.get('SpdMph')),
                                     ('wingspan', amen.get('WngspnImperial')),
                                     ('thrust', amen.get('ThrstImperial'))):
                    if value:
                        specs[label] = value
                entry['specs'].update(specs)
            cabins = eq.get('Cabins') or []
            if cabins and not entry['cabin_specs']:
                for cabin in cabins:
                    if cabin.get('Name') == 'TotalCabinCapacity':
                        continue
                    entry['cabin_specs'].append({'code': cabin.get('Name'),
                                                 'seats': cabin.get('TotalSeats')})

    # 2. fleet pages: real seat maps and interior specifications
    for path in sorted(glob.glob(str(SCRAPED / 'sdl_company_aircraft_*.html'))):
        try:
            payload = json.load(open(path))
        except Exception:
            continue
        blocks = page_blocks(payload)
        title = ''
        for b in blocks:
            if b['kind'] == 'heading' and b['level'] == 1:
                title = b['text']
                break
        tables = [b for b in blocks if b['kind'] == 'table']
        paras = [b['text'] for b in blocks if b['kind'] == 'para']
        if not tables:
            continue
        table = tables[0]
        head = [c.replace('\n', ' ') for c in (table['head'] or [])]
        # find the header columns per cabin
        def find_row(label):
            for r in table['rows']:
                if r and label.lower() in r[0].lower():
                    return r
            return None
        seats = find_row('Number of seats')
        config = find_row('Seat configuration')
        pitch = find_row('pitch')
        if not (seats and config):
            continue
        cabins = []
        names = (table['head'] or table['rows'][0])[1:]
        for i, name in enumerate(names):
            if i + 1 >= len(seats):
                continue
            try:
                seat_count = int(re.sub(r'\D', '', seats[i + 1]) or 0)
            except ValueError:
                seat_count = 0
            cfg = config[i + 1] if len(config) > i + 1 else '3-3'
            letters = _letters_for_config(cfg)
            abreast = len(letters)
            rows = max((seat_count + abreast - 1) // abreast, 1) if seat_count else 0
            pitch_val = ''
            if pitch and len(pitch) > i + 1:
                cell = pitch[i + 1]
                m = re.search(r"([\d'\"]+ ?\(\d+ ?(?:\.|\d)?\s?(?:cm|m)\)?.*)", cell)
                if m:
                    pitch_val = m.group(1).strip()
                else:
                    m2 = re.search(r'(\d+[\'\"]+.*)', cell)
                    pitch_val = m2.group(1).strip() if m2 else cell.strip()
            cabins.append({
                'name': name.replace('\n', ' ').strip(),
                'seats': seat_count,
                'config': cfg.replace('-', '-'),
                'letters': letters,
                'rows': rows,
                'pitch': pitch_val,
            })
        # map to a canonical equipment key by matching captured ops equipment
        key = None
        for k, entry in aircraft.items():
            if not entry['name']:
                continue
            a, b = _norm_aircraft_name(entry['name']), _norm_aircraft_name(title)
            if a and b and (a.startswith(b) or b.startswith(a)):
                key = k
                break
        if key is None:
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            key = slug[:10].upper()
            row(key, title)
        entry = aircraft[key]
        entry['description'] = ' '.join(
            p for p in paras if 'What you' in p or 'features' in p.lower())[:300]
        entry['cabin_specs_full'] = cabins
        entry['name'] = entry['name'] or title
    return aircraft


# ------------------------------------------------------------------- content --

def build_content() -> dict:
    content = {'snapshot_date': SNAPSHOT_DATE, 'pages': {}}
    for path in sorted(glob.glob(str(SCRAPED / 'sdl_*.html'))):
        try:
            payload = json.load(open(path))
        except Exception:
            continue
        slug = pathlib.Path(path).name.replace('sdl_', '').replace('.html', '')
        blocks = page_blocks(payload)
        if blocks:
            content['pages'][slug] = {'title': page_title(payload) or slug,
                                      'blocks': blocks}
    return content


def main() -> None:
    airports = build_airports()
    flights = build_flights(airports)
    aircraft = build_aircraft()
    content = build_content()
    (SITE / 'source_data_airports.json').write_text(
        json.dumps(airports, indent=1, sort_keys=True) + '\n')
    (SITE / 'source_data_flights.json').write_text(
        json.dumps({'snapshot_date': SNAPSHOT_DATE, 'flights': flights},
                   indent=1) + '\n')
    (SITE / 'source_data_aircraft.json').write_text(
        json.dumps(aircraft, indent=1, sort_keys=True) + '\n')
    (SITE / 'source_data_content.json').write_text(
        json.dumps(content, indent=1) + '\n')
    print(f'[source] airports={len(airports)} flights={len(flights)} '
          f'aircraft={len(aircraft)} pages={len(content["pages"])}')


if __name__ == '__main__':
    main()
