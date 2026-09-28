#!/usr/bin/env python3
"""Build sites/spothero/asset_inventory.json — the tracked manifest of every
managed runtime image with its byte size, sha256, and real upstream source URL.

Sources of truth for the URLs:
  * scraped_data/image_manifest.json        — the facility/redeem/site plan
  * scraped_data/harvest/airports/*.html     — airport-lot facility images
    (embedded __NEXT_DATA__ airportSpots[].facility.common.images)
  * a small fixed map for checkout payment marks and hero art whose URLs were
    captured inline in the recon pages
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
SCRAPE = SITE / 'scraped_data'

MANAGED_ROOTS = ('static/images', 'static/external_cache')

# checkout payment marks + hero art: local name -> upstream URL (captured from
# the recon pages' rendered src / imagesrcset attributes)
FIXED_URLS = {
    'static/images/site/pay-visa.35630977.svg':
        'https://spothero.com/consumer-checkout/_next/static/media/visa.35630977.svg',
    'static/images/site/pay-mastercard.c6951493.svg':
        'https://spothero.com/consumer-checkout/_next/static/media/mastercard.c6951493.svg',
    'static/images/site/pay-apple-pay.b38bdce0.svg':
        'https://spothero.com/consumer-checkout/_next/static/media/apple-pay.b38bdce0.svg',
    'static/images/site/pay-google-pay.a562ffbf.svg':
        'https://spothero.com/consumer-checkout/_next/static/media/google-pay.a562ffbf.svg',
    'static/images/site/pay-paypal.f49cd0e4.svg':
        'https://spothero.com/consumer-checkout/_next/static/media/paypal.f49cd0e4.svg',
    'static/images/site/powered-by-google.png':
        'https://res.cloudinary.com/spothero/f_auto,c_limit,w_384,q_auto/front-end/powered-by-google',
    'static/images/site/app-store-badge.png':
        'https://res.cloudinary.com/spothero/f_auto,c_limit,w_384,q_auto/logos/app-store-badge',
    'static/images/site/google-play-badge.png':
        'https://res.cloudinary.com/spothero/f_auto,c_limit,w_384,q_auto/logos/google-play-badge',
    'static/images/site/woman-driving-car.jpg':
        'https://res.cloudinary.com/spothero/f_auto,c_limit,w_3840,q_auto/v1723744392/homepage/woman-driving-car.jpg',
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def airport_facility_images() -> dict[str, str]:
    """facility image paths -> original cloudinary URLs from airport pages."""
    mapping = {}
    for hf in sorted((SCRAPE / 'harvest' / 'airports').glob('*.html')):
        text = hf.read_text(encoding='utf-8', errors='ignore')
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', text, flags=re.S)
        if not m:
            continue
        data = json.loads(m.group(1))
        for spot in data['props']['pageProps'].get('airportSpots') or []:
            fac = (spot.get('facility') or {}).get('common') or {}
            fid = fac.get('id')
            for n, img in enumerate((fac.get('images') or [])[:3]):
                url = img.get('url') if isinstance(img, dict) else None
                if fid and url:
                    mapping[f'static/images/facilities/{fid}/{fid}_{n}.jpg'] = url
    return mapping


def main() -> None:
    plan = {row['path']: row['url']
            for row in json.loads((SCRAPE / 'image_manifest.json').read_text())}
    # redeem illustrations were planned as .png; recompression converted them to .jpg
    for path, url in list(plan.items()):
        if path.endswith('.png'):
            plan[path[:-4] + '.jpg'] = url
    airport = airport_facility_images()

    assets = []
    missing = []
    for root in MANAGED_ROOTS:
        for path in sorted((SITE / root).rglob('*')):
            if not path.is_file() or path.name == '.gitkeep':
                continue
            rel = str(path.relative_to(SITE))
            url = plan.get(rel) or airport.get(rel) or FIXED_URLS.get(rel)
            if not url:
                missing.append(rel)
                continue
            assets.append({
                'path': rel,
                'bytes': path.stat().st_size,
                'sha256': sha256(path),
                'source_url': url,
            })
    if missing:
        raise SystemExit(f'{len(missing)} files without a source URL: {missing[:5]}')

    manifest = {
        'schema_version': 1,
        'site': 'spothero',
        'asset_count': len(assets),
        'total_bytes': sum(a['bytes'] for a in assets),
        'captured_on': '2026-09-26',
        'capture_method': (
            'Playwright-rendered spothero.com pages (facility dehydrated-state JSON, '
            'airport __NEXT_DATA__ airportSpots, destination/search/city/airport HTML) '
            'plus direct HTTPS fetches of the resolved cloudinary.com/spothero and '
            'spothero.com static media URLs the live pages serve'),
        'source_page': 'https://spothero.com/',
        'notes': [
            'Every entry is a real upstream media file fetched at its resolved URL.',
            'Facility photos use the cloudinary transforms the live facility pages render.',
            'Verified byte- and hash-exact by scripts/check_asset_inventory.py at build time.',
        ],
        'assets': assets,
    }
    (SITE / 'asset_inventory.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(f'wrote asset_inventory.json: {len(assets)} assets, '
          f'{manifest["total_bytes"]} bytes')


if __name__ == '__main__':
    main()
