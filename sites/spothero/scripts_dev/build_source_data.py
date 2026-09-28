#!/usr/bin/env python3
"""Build the tracked source-data snapshots for the spothero mirror.

Converts the raw upstream capture (scraped_data/harvest/, produced by
Playwright against https://spothero.com/ on 2026-09-26) into the three
deterministic JSON snapshots seed_data.py reads:

    source_data_facilities.json   facilities + rates + airport inventory
    source_data_geo.json          cities / destinations / airports / events / stadiums
    source_data_content.json      faqs, static-page copy, promo code

Determinism: every list is sorted before it is written.
"""
from __future__ import annotations

import html as html_mod
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent.parent
SCRAPE = HERE / 'scraped_data' / 'harvest'

OUT_FACILITIES = HERE / 'source_data_facilities.json'
OUT_GEO = HERE / 'source_data_geo.json'
OUT_CONTENT = HERE / 'source_data_content.json'

SNAPSHOT = '2026-09-26'


def read(path):
    return (SCRAPE / path).read_text(encoding='utf-8')


def next_data(html):
    m = re.findall(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, flags=re.S)
    if not m:
        return None
    return json.loads(m[0])['props']['pageProps']


def strip_tags(fragment):
    text = re.sub(r'<script.*?</script>', ' ', fragment, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', text)
    # decode HTML entities so stored text renders verbatim (no double-escape)
    text = html_mod.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def parse_accordion_faqs(html):
    out = []
    parts = re.split(r'data-testid="accordion-faq-question-\d+"[^>]*>', html)
    for part in parts[1:]:
        mq = re.match(r'([^<]+)</div>', part)
        if not mq:
            continue
        q = mq.group(1).strip()
        ma = re.search(
            r'data-testid="accordion-faq-answer-\d+"[^>]*>([\s\S]*?)'
            r'(?=data-testid="accordion-faq-question|</section|$)', part)
        if not ma:
            continue
        paras = re.findall(r'>([^<>]*(?:<[^>]+>[^<>]*)*?)</p>', ma.group(1))
        texts = []
        for p in paras:
            t = re.sub(r'<[^>]+>', '', p).strip()
            t = re.sub(r'\s+', ' ', html_mod.unescape(t))
            if t:
                texts.append(t)
        a = ' '.join(texts).strip()
        if a:
            out.append({'q': html_mod.unescape(q).strip(), 'a': a})
    return out


def parse_ld_faqs(html):
    out = []
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                        html, flags=re.S):
        try:
            d = json.loads(m)
        except Exception:
            continue
        if d.get('@type') == 'FAQPage':
            for q in d.get('mainEntity', []):
                out.append({'q': q['name'], 'a': q['acceptedAnswer']['text']})
    return out


# ---------------------------------------------------------------- facilities

def build_facilities(featured_prices=None):
    featured_prices = featured_prices or {}
    # price map from searches
    prices = {}
    for fn in sorted((SCRAPE / 'search').glob('*.json')):
        d = json.loads(fn.read_text())
        for c in d['cards']:
            sid = c.get('spot_id')
            if not sid or not c.get('price'):
                continue
            rec = prices.setdefault(sid, {})
            if d['kind'] == 'monthly':
                rec['monthly'] = float(c['price'])
            else:
                rec['daily'] = float(c['price'])
    for fn in sorted((SCRAPE / 'search1h').glob('*.json')):
        d = json.loads(fn.read_text())
        for c in d['cards']:
            sid = c.get('spot_id')
            if not sid or not c.get('price'):
                continue
            prices.setdefault(sid, {})['base'] = float(c['price'])

    facilities = []
    seen_ids = set()
    for fn in sorted((SCRAPE / 'facilities').glob('*.json')):
        d = json.loads(fn.read_text())
        fid = str(d['id'])
        if fid in seen_ids:
            continue
        seen_ids.add(fid)
        common = d.get('fullFacilityData', {}).get('common', {}) or {}
        addr = None
        for a in common.get('addresses') or []:
            if 'search' in (a.get('types') or []):
                addr = a
                break
        if addr is None and common.get('addresses'):
            addr = common['addresses'][0]
        if addr is None:
            addr = d.get('address') or {}
        rating = d.get('rating') or common.get('rating') or {}
        price = prices.get(fid, {})
        base = price.get('base')
        daily = price.get('daily')
        monthly = price.get('monthly')
        # fall back to firstRateInfo (3.5h default window) when search price missing
        fri = d.get('firstRateInfo') or {}
        cost = (fri.get('cost') or {}).get('value')
        feat = featured_prices.get(fid)
        if (base is None or daily is None) and cost:
            est = cost / 100.0
            if base is None:
                base = round(est * 0.8, 2)
            if daily is None:
                daily = round(est * 1.15, 2)
        if (base is None or daily is None) and feat:
            # facility currently sells no transient product in the capture, but
            # upstream still lists it on the destination page at this price
            est = float(feat)
            if base is None:
                base = round(est * 0.8, 2)
            if daily is None:
                daily = round(est * 1.15, 2)
        if base is None or daily is None:
            continue  # not bookable transient in our capture
        increment = round(max(0.0, daily - base) / 7.0, 2)
        images = []
        for n, img in enumerate(d.get('images', [])[:3]):
            images.append(f'facilities/{fid}/{fid}_{n}.jpg')
        restrictions = [r for r in (d.get('restrictions') or []) if r]
        redemption = []
        for step in (d.get('fullFacilityData', {}).get('transient', {})
                     .get('redemption_instructions', {}).get('drive_up') or []):
            ill = (step.get('illustration') or {}).get('url') or ''
            m = re.search(r'/v\d+/([^/?#]+)$', ill)
            if not m:
                redemption.append({'text': step.get('text', ''), 'illustration': None})
                continue
            stem = m.group(1).rsplit('.', 1)[0]
            actual = None
            for ext in ('.png', '.jpg'):
                if (HERE / 'static' / 'images' / 'redeem' / (stem + ext)).exists():
                    actual = stem + ext
                    break
            redemption.append({'text': step.get('text', ''),
                              'illustration': f'redeem/{actual}' if actual else None})
        hours = d.get('hoursOfOperation') or {}
        pt = common.get('parking_types') or []
        facilities.append({
            'id': fid,
            'title': d.get('title') or common.get('title') or '',
            'slug': d.get('slug') or common.get('slug') or '',
            'city': (d.get('city') or common.get('city') or {}).get('name', ''),
            'city_slug': (d.get('city') or common.get('city') or {}).get('slug', ''),
            'state': addr.get('state', ''),
            'street': addr.get('street_address', ''),
            'postal': addr.get('postal_code', ''),
            'lat': addr.get('latitude'),
            'lng': addr.get('longitude'),
            'operator': common.get('operator_display_name', ''),
            'facility_type': common.get('facility_type', 'unknown'),
            'rating_avg': rating.get('average'),
            'rating_count': rating.get('count'),
            'rating_dist': [rating.get('one_star_count'), rating.get('two_star_count'),
                            rating.get('three_star_count'), rating.get('four_star_count'),
                            rating.get('five_star_count')],
            'prompt_counts': [{'name': p.get('name'), 'emoji': p.get('emoji'),
                               'count': p.get('count')}
                              for p in (rating.get('prompt_counts') or
                                        common.get('prompt_counts') or [])],
            'amenities': [a.get('display_name') for a in (d.get('amenities') or [])
                          if a.get('display_name')],
            'restrictions': restrictions,
            'getting_there': d.get('gettingHere') or common.get('navigation_tip') or '',
            'redemption': redemption,
            'always_open': bool(hours.get('always_open')),
            'hours_text': hours.get('text') or [],
            'clearance_inches': common.get('clearance_inches'),
            'monthly_ok': 'monthly' in pt or monthly is not None,
            'cancellable': bool(d.get('cancellationAllowed', True)),
            'event_fee': bool((fri.get('priceBreakdown') or []) and
                              any(p.get('type') == 'event_fee'
                                  for p in fri.get('priceBreakdown', []))),
            'images': images,
            'base_rate': round(base, 2),
            'daily_rate': round(daily, 2),
            'increment_rate': increment,
            'monthly_rate': round(monthly, 2) if monthly is not None else None,
            'airport': None,
        })

    # airport facilities from airport pages
    for fn in sorted((SCRAPE / 'airports').glob('*.html')):
        pp = next_data(read(f'airports/{fn.name}'))
        if not pp or not pp.get('airport'):
            continue
        code = fn.name.split('-')[-2].upper()
        for sp in pp.get('airportSpots') or []:
            common = (sp.get('facility') or {}).get('common') or {}
            fid = str(common.get('id'))
            rate = (sp.get('rates') or [{}])[0]
            quote = rate.get('quote') or {}
            order = (quote.get('order') or [{}])[0]
            rental = next((it for it in order.get('items', [])
                           if it.get('type') == 'rental'), {})
            fac_fee = next((it for it in order.get('items', [])
                            if it.get('type') == 'reservation_fee'), {})
            days = 1
            m = re.search(r'x (\d+) day', rental.get('short_description', ''))
            if m:
                days = int(m.group(1))
            rental_value = (rental.get('price') or {}).get('value')
            if not rental_value:
                continue
            per_day = round(rental_value / 100.0 / days, 2)
            airport_amenities = [a.get('display_name') for a in
                                 (rate.get('airport') or {}).get('amenities') or []
                                 if a.get('display_name')]
            addr = (common.get('addresses') or [{}])[0]
            rating = common.get('rating') or {}
            if fid in seen_ids:
                for f in facilities:
                    if f['id'] == fid:
                        f['airport'] = {
                            'code': code,
                            'daily_rate': per_day,
                            'facility_fee': round((fac_fee.get('price') or {}).get('value', 0) / 100.0, 2),
                            'shuttle': 'Airport Shuttle' in airport_amenities,
                            'distance_m': (sp.get('distance') or {}).get('linear_meters'),
                            'parking_pass': ((rate.get('airport') or {})
                                             .get('parking_pass') or {}).get('display_name'),
                        }
                continue
            seen_ids.add(fid)
            images = [f'facilities/{fid}/{fid}_{n}.jpg'
                      for n in range(min(2, len(common.get('images') or [])))]
            ap = sp.get('facility', {}).get('airport') or {}
            def _ill(step):
                ill = (step.get('illustration') or {}).get('url') or ''
                m = re.search(r'/v\d+/([^/?#]+)$', ill)
                if not m:
                    return None
                stem = m.group(1).rsplit('.', 1)[0]
                for ext in ('.png', '.jpg'):
                    if (HERE / 'static' / 'images' / 'redeem' / (stem + ext)).exists():
                        return f'redeem/{stem + ext}'
                return None

            arrival = [{'text': s.get('text', ''), 'illustration': _ill(s)}
                       for s in (ap.get('redemption_instructions') or {}).get('arrival') or []]
            facilities.append({
                'id': fid,
                'title': common.get('title') or '',
                'slug': common.get('slug') or '',
                'city': common.get('city', {}).get('name', ''),
                'city_slug': common.get('city', {}).get('slug', ''),
                'state': addr.get('state', ''),
                'street': addr.get('street_address', ''),
                'postal': addr.get('postal_code', ''),
                'lat': addr.get('latitude'),
                'lng': addr.get('longitude'),
                'operator': common.get('operator_display_name', ''),
                'facility_type': common.get('facility_type', 'unknown'),
                'rating_avg': rating.get('average'),
                'rating_count': rating.get('count'),
                'rating_dist': [rating.get('one_star_count'), rating.get('two_star_count'),
                                rating.get('three_star_count'), rating.get('four_star_count'),
                                rating.get('five_star_count')],
                'prompt_counts': [{'name': p.get('name'), 'emoji': p.get('emoji'),
                                   'count': p.get('count')}
                                  for p in common.get('prompt_counts') or []],
                'amenities': airport_amenities,
                'restrictions': [r for r in (common.get('restrictions') or []) if r],
                'getting_there': common.get('navigation_tip') or '',
                'redemption': arrival,
                'always_open': True,
                'hours_text': ['This facility is open 24/7.'],
                'clearance_inches': common.get('clearance_inches'),
                'monthly_ok': False,
                'cancellable': True,
                'event_fee': False,
                'images': images,
                'base_rate': per_day,
                'daily_rate': per_day,
                'increment_rate': 0.0,
                'monthly_rate': None,
                'airport': {
                    'code': code,
                    'daily_rate': per_day,
                    'facility_fee': round((fac_fee.get('price') or {}).get('value', 0) / 100.0, 2),
                    'shuttle': 'Airport Shuttle' in airport_amenities,
                    'distance_m': (sp.get('distance') or {}).get('linear_meters'),
                    'parking_pass': ((rate.get('airport') or {})
                                     .get('parking_pass') or {}).get('display_name'),
                },
            })

    facilities.sort(key=lambda f: int(f['id']))
    return facilities


# ---------------------------------------------------------------- geo

CITY_FILES = [
    'chicago-parking', 'nyc-parking', 'san-francisco-parking', 'boston-parking',
    'seattle-parking', 'denver-parking', 'washington-parking', 'philadelphia-parking',
    'los-angeles-parking', 'new-orleans-parking', 'milwaukee-parking',
    'minneapolis-parking', 'nashville-parking', 'austin-parking', 'miami-parking',
]
CITY_LABELS = {
    'chicago-parking': 'Chicago', 'nyc-parking': 'New York',
    'san-francisco-parking': 'San Francisco', 'boston-parking': 'Boston',
    'seattle-parking': 'Seattle', 'denver-parking': 'Denver',
    'washington-parking': 'Washington', 'philadelphia-parking': 'Philadelphia',
    'los-angeles-parking': 'Los Angeles', 'new-orleans-parking': 'New Orleans',
    'milwaukee-parking': 'Milwaukee', 'minneapolis-parking': 'Minneapolis',
    'nashville-parking': 'Nashville', 'austin-parking': 'Austin',
    'miami-parking': 'Miami',
}
CITY_STATES = {
    'chicago-parking': 'IL', 'nyc-parking': 'NY', 'san-francisco-parking': 'CA',
    'boston-parking': 'MA', 'seattle-parking': 'WA', 'denver-parking': 'CO',
    'washington-parking': 'DC', 'philadelphia-parking': 'PA',
    'los-angeles-parking': 'CA', 'new-orleans-parking': 'LA',
    'milwaukee-parking': 'WI', 'minneapolis-parking': 'MN',
    'nashville-parking': 'TN', 'austin-parking': 'TX', 'miami-parking': 'FL',
}


def section_links(html, heading_pat):
    m = re.search(heading_pat, html)
    if not m:
        return []
    start = m.end()
    nxt = re.search(r'<h[23][^>]*>', html[start:])
    body = html[start:start + nxt.start()] if nxt else html[start:start + 40000]
    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{2,60})', body)
    return [{'title': n.strip(), 'href': h} for h, n in links if n.strip()]


def build_cities():
    cities = []
    for slug in CITY_FILES:
        html = read(f'cities/{slug}.html')
        pp = next_data(html) or {}
        c = pp.get('city') or {}
        rates = pp.get('dynamicRates') or {}
        rate_rows = []
        for key, label in (('commuterAvgPrice', 'Commuter Parking'),
                           ('weekendAvgPrice', 'Weekend Parking'),
                           ('eventAvgPrice', 'Event Parking'),
                           ('overnightAvgPrice', 'Overnight Parking')):
            v = rates.get(key)
            if v:
                rate_rows.append({'label': label,
                                  'low': v.get('low'), 'high': v.get('high')})
        airport_links = []
        for h, n in re.findall(r'<a[^>]+href="(https://spothero\.com/airport/[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{2,60})', html):
            if ('International Airport' in n or 'Airport (' in n) and (h, n) not in airport_links:
                airport_links.append({'title': n.strip(), 'href': h})
        m = re.search(r'<h1[^>]*>Find and reserve\s*(?:<[^>]+>\s*)*parking in ([^<]+)<', html)
        display = m.group(1).strip() if m else CITY_LABELS[slug]
        # event parking copy
        i = html.find('Event Parking</h2>')
        ev_copy = ''
        if i > 0:
            ev_copy = strip_tags(html[i:i + 1400])[:700]
        hero = ((pp.get('page') or {}).get('hero_image') or {}).get('url') or ''
        cities.append({
            'slug': slug,
            'name': CITY_LABELS[slug],
            'display_name': display,
            'state': CITY_STATES[slug],
            'lat': c.get('latitude'),
            'lng': c.get('longitude'),
            'timezone': c.get('timezone'),
            'hero_image': hero,
            'phone': c.get('phone_number_friendly'),
            'monthly_phone': c.get('monthly_phone_number_friendly'),
            'rates': rate_rows,
            'popular_destinations': section_links(html, r'Popular Destinations[^<]*</h3>'),
            'neighborhoods': section_links(html, r'Popular Neighborhoods</h3>'),
            'venues': section_links(html, r'Popular Venues</h3>'),
            'categories': section_links(html, rf'{CITY_LABELS[slug]} Destinations</h3>'),
            'airports': airport_links,
            'event_copy': ev_copy,
            'faqs': parse_ld_faqs(html),
        })
    # monthly city pages
    monthly = {}
    for slug in ('chicago-parking', 'nyc-parking'):
        html = read(f'cities/monthly-{slug}.html')
        i = html.find('Featured Monthly Rates')
        rows = []
        if i > 0:
            body = html[i:i + 6000]
            for m in re.finditer(
                    r'>([^<]{3,60}(?:Garage|Valet|Lot|Plaza|Wells|Building)[^<]{0,30})<[\s\S]{0,600}?\$(\d+)<', body):
                rows.append({'facility': m.group(1).strip(), 'rate': int(m.group(2))})
        faqs = parse_accordion_faqs(html)
        monthly[slug] = {'featured': rows, 'faqs': faqs}
    return cities, monthly


ANCHOR_DESTINATIONS = [
    # search anchors captured on the snapshot date whose /destination/ pages
    # were not part of the 31 harvested pages; coordinates are the real
    # upstream search coordinates used for the corresponding searches.
    {'slug': 'times-square-parking', 'title': 'Times Square', 'city': 'New York',
     'city_slug': 'nyc-parking', 'state': 'NY', 'lat': 40.758, 'lng': -73.9855},
    {'slug': 'union-square-parking', 'title': 'Union Square', 'city': 'San Francisco',
     'city_slug': 'san-francisco-parking', 'state': 'CA', 'lat': 37.788, 'lng': -122.4075},
    {'slug': 'downtown-parking', 'title': 'Downtown', 'city': 'Denver',
     'city_slug': 'denver-parking', 'state': 'CO', 'lat': 39.7392, 'lng': -104.9903},
    {'slug': 'national-mall-parking', 'title': 'National Mall', 'city': 'Washington',
     'city_slug': 'washington-parking', 'state': 'DC', 'lat': 38.8895, 'lng': -77.0353},
    {'slug': 'independence-hall-parking', 'title': 'Independence Hall', 'city': 'Philadelphia',
     'city_slug': 'philadelphia-parking', 'state': 'PA', 'lat': 39.9489, 'lng': -75.15},
    {'slug': 'french-quarter-parking', 'title': 'French Quarter', 'city': 'New Orleans',
     'city_slug': 'new-orleans-parking', 'state': 'LA', 'lat': 29.9584, 'lng': -90.0644},
]


def build_destinations():
    destinations = []
    for fn in sorted((SCRAPE / 'destinations').glob('*.html')):
        html = read(f'destinations/{fn.name}')
        pp = next_data(html) or {}
        dest = pp.get('destination') or {}
        if not dest:
            continue
        city_slug = (pp.get('city') or {}).get('relative_url') or (
            (pp.get('city') or {}).get('slug') or '')
        featured = []
        for sp in pp.get('featuredSpots') or []:
            sr = sp.get('selectedRate') or {}
            total = (sr.get('totalPrice') or {}).get('value')
            featured.append({
                'facility_id': str(sp.get('spotId')),
                'title': sp.get('title'),
                'walk_seconds': (sp.get('distance') or {}).get('durationSeconds'),
                'walk_meters': (sp.get('distance') or {}).get('walkingMeters'),
                'rating_avg': (sp.get('rating') or {}).get('average'),
                'rating_count': (sp.get('rating') or {}).get('count'),
                'starting_at': round(total / 100.0, 2) if total else None,
            })
        rates = pp.get('dynamicRates') or {}
        rate_rows = []
        for key, label in (('commuterAvgPrice', 'Commuter Parking'),
                           ('weekendAvgPrice', 'Weekend Parking'),
                           ('eventAvgPrice', 'Event Parking'),
                           ('overnightAvgPrice', 'Overnight Parking')):
            v = rates.get(key)
            if v:
                rate_rows.append({'label': label,
                                  'low': v.get('low'), 'high': v.get('high')})
        body_slices = (pp.get('page') or {}).get('transient_body') or []
        partner_heading = ''
        partner_paras = []
        for sl in body_slices:
            title = (sl.get('primary') or {}).get('content_slice_title') or []
            if title:
                partner_heading = title[0].get('text', '')
            rich = (sl.get('primary') or {}).get('content_slice_rich_text') or []
            partner_paras = [r.get('text', '') for r in rich if r.get('text')]
        destinations.append({
            'slug': dest.get('relative_url'),
            'title': dest.get('title'),
            'city': dest.get('city'),
            'city_slug': city_slug,
            'state': dest.get('state'),
            'street': dest.get('street_address'),
            'postal': dest.get('zipcode'),
            'lat': dest.get('latitude'),
            'lng': dest.get('longitude'),
            'featured': featured,
            'rates': rate_rows,
            'partner_heading': partner_heading,
            'partner_paras': partner_paras,
            'faqs': parse_accordion_faqs(html),
            'popular': [{'title': p.get('title'), 'href': p.get('link')}
                        for p in pp.get('popularDestinations') or []],
            'events': [{'id': e[0], 'title': e[1], 'starts': e[2], 'ends': e[3]}
                       for e in (pp.get('events') or [])],
        })
    have = {d['slug'] for d in destinations}
    for a in ANCHOR_DESTINATIONS:
        if a['slug'] in have:
            continue
        destinations.append({
            'slug': a['slug'], 'title': a['title'], 'city': a['city'],
            'city_slug': a['city_slug'], 'state': a['state'], 'street': '',
            'postal': '', 'lat': a['lat'], 'lng': a['lng'], 'featured': [],
            'rates': [], 'partner_heading': '', 'partner_paras': [],
            'faqs': [], 'popular': [], 'events': [],
        })
    return destinations


def build_airports():
    airports = []
    for fn in sorted((SCRAPE / 'airports').glob('*.html')):
        pp = next_data(read(f'airports/{fn.name}'))
        if not pp or not pp.get('airport'):
            continue
        ap = pp['airport']
        code = fn.name.split('-')[-2].upper()
        spots = []
        for sp in pp.get('airportSpots') or []:
            common = (sp.get('facility') or {}).get('common') or {}
            rate = (sp.get('rates') or [{}])[0]
            quote = rate.get('quote') or {}
            order = (quote.get('order') or [{}])[0]
            rental = next((it for it in order.get('items', [])
                           if it.get('type') == 'rental'), {})
            m = re.search(r'x (\d+) day', rental.get('short_description', ''))
            days = int(m.group(1)) if m else 1
            rv = (rental.get('price') or {}).get('value')
            spots.append({
                'facility_id': str(common.get('id')),
                'title': common.get('title'),
                'per_day': round(rv / 100.0 / days, 2) if rv else None,
                'distance_m': (sp.get('distance') or {}).get('linear_meters'),
            })
        airports.append({
            'code': code,
            'title': ap.get('title'),
            'info_title': ap.get('destination_info_title'),
            'city': ap.get('city'),
            'state': ap.get('state'),
            'street': ap.get('street_address'),
            'postal': ap.get('zipcode'),
            'lat': ap.get('latitude'),
            'lng': ap.get('longitude'),
            'url_slug': fn.name[:-5],
            'search_request': pp.get('searchRequest'),
            'spots': spots,
            'faqs': parse_accordion_faqs(read(f'airports/{fn.name}')),
        })
    return airports


def build_events():
    venues = []

    def extract_venue(html):
        for s in re.findall(r'<script[^>]*>(.*?)</script>', html, flags=re.S):
            if '"parking_window"' in s and '"search_url"' in s:
                i = s.find('"events":[')
                if i < 0:
                    return None
                depth = 0
                j = i - 1
                while j >= 0:
                    if s[j] == '}':
                        depth += 1
                    elif s[j] == '{':
                        if depth == 0:
                            break
                        depth -= 1
                    j -= 1
                obj_start = j
                depth = 0
                k = obj_start
                instr = False
                esc = False
                while k < len(s):
                    ch = s[k]
                    if esc:
                        esc = False
                    elif ch == '\\':
                        esc = True
                    elif ch == '"':
                        instr = not instr
                    elif not instr:
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                            if depth == 0:
                                break
                    k += 1
                try:
                    return json.loads(s[obj_start:k + 1])
                except Exception:
                    return None
        return None

    for fn in sorted((SCRAPE / 'events').glob('venue-*.html')):
        d = extract_venue(read(f'events/{fn.name}'))
        if not d:
            continue
        evs = []
        for e in d.get('events') or []:
            if not e.get('search_url'):
                continue
            evs.append({
                'id': e['id'],
                'title': e['title'],
                'starts': e.get('starts'),
                'ends': e.get('ends'),
                'window_starts': (e.get('parking_window') or {}).get('starts'),
                'window_ends': (e.get('parking_window') or {}).get('ends'),
                'description': e.get('description'),
                'seo_url': e.get('search_url'),
            })
        venues.append({
            'title': d.get('title'),
            'city': d.get('city'),
            'state': d.get('state'),
            'street': d.get('street_address'),
            'slug': d.get('relative_url'),
            'lat': d.get('latitude'),
            'lng': d.get('longitude'),
            'events': evs,
        })
    return venues


def build_stadiums():
    html = read('static/stadium_list.html')
    leagues = []
    # split by league headings
    parts = re.split(r'<h2[^>]*>(NFL Stadiums|MLB Stadiums|NBA Arenas|NHL Arenas)</h2>', html)
    for i in range(1, len(parts), 2):
        league = parts[i]
        body = parts[i + 1]
        rows = []
        # rows: <tr> <td>name</td> <td>team</td> <td><a href=...>Book Now</a></td> </tr>
        for m in re.finditer(
                r'<tr[^>]*>\s*<td[^>]*>\s*(?:<[^>]+>\s*)*([^<]{2,60}?)\s*(?:<[^>]+>\s*)*</td>\s*'
                r'<td[^>]*>\s*(?:<[^>]+>\s*)*([^<]{2,60}?)\s*(?:<[^>]+>\s*)*</td>\s*'
                r'<td[^>]*>[\s\S]*?href="(https://spothero\.com/destination/[^"]+)"',
                body):
            rows.append({'name': m.group(1).strip(), 'team': m.group(2).strip(),
                         'href': m.group(3)})
        leagues.append({'league': league, 'stadiums': rows})
    return leagues


# ---------------------------------------------------------------- content

STATIC_PAGE_FILES = {
    'about': 'about.html',
    'about/parking-guarantee': 'guarantee.html',
    'about/promo-code': 'promo_code.html',
    'contact': 'contact.html',
    'press': 'press.html',
    'careers': 'careers.html',
    'legal/terms-of-use': 'terms.html',
    'legal/privacy-policy': 'privacy.html',
    'get-spothero-app': 'app.html',
    'solutions/commuter-benefits': 'commuter.html',
    'business': 'business.html',
    'sell-parking/operators': 'sell_operators.html',
    'sell-parking/property-managers': 'sell_pm.html',
    'sell-parking/independent-sellers': 'sell_sellers.html',
    'sell-parking/airport-parking': 'sell_airports.html',
    'sell-parking/event-parking-partnerships': 'sell_events.html',
}

STATIC_DROP = {'100M+', 'Book Parking', 'Sell Parking', 'Company/Legal', 'Cars Parked',
               '4.9 /5 iOS App Store', '15 Years in Business', 'App Store Rating',
               'Cookie Preference Center', 'SpotHero © 2026. All Rights Reserved.',
               'About', 'How it Works', 'About SpotHero', 'Parking Guarantee',
               'Contact Us', 'SpotHero for Business', 'Get the App',
               'Log In or Sign Up', 'My Reservations', 'Log Out'}


def build_static_pages():
    pages = {}
    for slug, fn in STATIC_PAGE_FILES.items():
        html = read(f'static/{fn}')
        i = html.find('<body')
        chunk = html[i:] if i > 0 else html
        chunk = re.sub(r'<script.*?</script>', ' ', chunk, flags=re.S)
        chunk = re.sub(r'<style.*?</style>', ' ', chunk, flags=re.S)
        chunk = re.sub(r'<nav.*?</nav>', ' ', chunk, flags=re.S)
        chunk = re.sub(r'<header.*?</header>', ' ', chunk, flags=re.S)
        chunk = re.sub(r'<footer.*?</footer>', ' ', chunk, flags=re.S)
        m = re.search(r'Book Parking\s*</h4>|Cookie Preference', chunk)
        if m:
            chunk = chunk[:m.start()]
        out = []
        for tag, text in re.findall(r'<(h1|h2|h3|h4|p|li)[^>]*>([^<]+)', chunk):
            t = re.sub(r'\s+', ' ', html_mod.unescape(text)).strip()
            if len(t) < 2 or t in STATIC_DROP:
                continue
            out.append({'tag': tag, 'text': t})
        dedup = []
        for s in out:
            if dedup and dedup[-1]['text'] == s['text']:
                continue
            dedup.append(s)
        pages[slug] = dedup
    promo = pages.get('about/promo-code', [])
    if promo:
        promo.append({'tag': 'p',
                      'text': '*Offer restrictions: Enter promo code at checkout. '
                              'One-time use only. Valid only in the SpotHero app. Valid '
                              'for first-time reservations for up to $5 off. Excludes '
                              'monthly reservations and SpotHero for Business '
                              'reservations.'})
    return pages


def build_content():
    faqs = parse_accordion_faqs(read('static/faq.html'))
    # faq categories from h2 headings order
    html = read('static/faq.html')
    h2s = re.findall(r'<h2[^>]*>([^<]+)</h2>', html)
    categories = [h.strip() for h in h2s if h.strip() and h.strip() != 'How SpotHero Works'
                  and h.strip() != 'Frequently Asked Questions']
    # assign categories by walking the DOM order
    parts = re.split(r'<h2[^>]*>([^<]+)</h2>', html)
    cat_map = []
    for i in range(1, len(parts), 2):
        cat_map.append((parts[i].strip(), parts[i + 1]))
    cat_faqs = []
    for cat, body in cat_map:
        if cat in ('How SpotHero Works', 'Frequently Asked Questions'):
            continue
        for f in parse_accordion_faqs(body):
            cat_faqs.append({'category': cat, 'q': f['q'], 'a': f['a']})
    # keep any FAQ not captured (order preserved)
    if len(cat_faqs) < len(faqs):
        seen = {(f['category'], f['q']) for f in cat_faqs}
        for f in faqs:
            if ('General', f['q']) not in seen:
                cat_faqs.append({'category': 'General', 'q': f['q'], 'a': f['a']})

    pages = build_static_pages()
    promo = {
        'code': 'FIRSTSPOT10',
        'pct': 10,
        'headline': 'Get 10% off Your First Reservation with Code FIRSTSPOT10',
        'restrictions': ('*Offer restrictions: Enter promo code at checkout. One-time use only. '
                         'Valid only in the SpotHero app. Valid for first-time reservations for '
                         'up to $5 off. Excludes monthly reservations and SpotHero for Business '
                         'reservations.'),
    }
    return {'faqs': cat_faqs, 'promo': promo, 'pages': pages}


def main():
    # destinations first: their featured rows carry the "starting at" price
    # upstream displays for facilities that sell no transient product in the
    # capture — that price is the only quote basis for those facilities
    destinations = build_destinations()
    featured_prices = {}
    for d in destinations:
        for row in d.get('featured') or []:
            featured_prices.setdefault(str(row['facility_id']), row.get('starting_at'))
    facilities = build_facilities(featured_prices)
    cities, monthly = build_cities()
    airports = build_airports()
    venues = build_events()
    stadiums = build_stadiums()
    content = build_content()

    OUT_FACILITIES.write_text(json.dumps(facilities, indent=1, sort_keys=True), encoding='utf-8')
    geo = {'cities': cities, 'monthly_cities': monthly, 'destinations': destinations,
           'airports': airports, 'venues': venues, 'stadiums': stadiums}
    OUT_GEO.write_text(json.dumps(geo, indent=1, sort_keys=True), encoding='utf-8')
    OUT_CONTENT.write_text(json.dumps(content, indent=1, sort_keys=True), encoding='utf-8')

    n_airport = sum(1 for f in facilities if f['airport'])
    print(f'facilities: {len(facilities)} ({n_airport} airport)')
    print(f'cities: {len(cities)}, destinations: {len(destinations)}, '
          f'airports: {len(airports)}, venues: {len(venues)}, '
          f'events: {sum(len(v["events"]) for v in venues)}')
    print(f'faqs: {len(content["faqs"])}')
    n_imgs = sum(len(f['images']) for f in facilities)
    print(f'facility image refs: {n_imgs}')


if __name__ == '__main__':
    main()
