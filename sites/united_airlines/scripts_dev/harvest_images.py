#!/usr/bin/env python3
"""Harvest the real united.com images for the mirror.

Every image the mirror serves comes from the real united.com media CDN
(media.united.com / www.united.com), fetched through the Internet Archive's
web.archive.org replays. The curated manifest (scraped_data/image_manifest.json,
built from the captured SDL CMS payloads + homepage JS bundles) is filtered to
the images the mirror actually renders; each file is stored under
static/images/<category>/ and recorded in asset_inventory.json with its true
source URL, byte size and SHA-256.

Run after the data harvest:  python3 scripts_dev/harvest_images.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import harvest  # noqa: E402
from harvest import SCRAPED  # noqa: E402

SITE = SCRAPED.parent
STATIC = SITE / 'static' / 'images'

# (storage category, filename pattern, max picks) — patterns match the real
# upstream media.united.com URL/file names captured in the SDL payloads.
WANT = [
    ('home', '0562_100daySummer_HP_Takeover_Desktop', 1),
    ('home', 'logos-united-logo-rebrand-large', 1),
    ('home', 'STAR-ALLI', 1),
    ('cabins/basic-economy', 'basic-economy-HERO-desktop', 1),
    ('cabins/basic-economy', '3col-woman-on-plane-phone', 1),
    ('cabins/united-economy', 'JS_ECONOMY_2023_1617', 1),
    ('cabins/united-economy', 'ual-ca-economy-window', 1),
    ('cabins/economy-plus', 'economy-plus-3', 1),
    ('cabins/economy-plus', 'js-economy-plus-02-2023-3886-rs-v-3-3x', 1),
    ('cabins/premium-plus', 'image-premium-plus-mw-3x', 1),
    ('cabins/premium-plus', 'united-premium-plus-image-2x', 1),
    ('cabins/premium-plus', '10-14-24-premium-plus-image', 1),
    ('cabins/united-first-business', 'first-class.png', 1),
    ('cabins/united-first-business', 'business-class.png', 1),
    ('cabins/united-first-business', 'map-united-first-2x', 1),
    ('cabins/united-first-business', 'map-united-business-2x', 1),
    ('cabins/united-polaris', 'United_DotCom_091024_Polaris_716x400', 1),
    ('cabins/united-polaris', 'polaris-upp-230425-sle-0392-rs-3x', 1),
    ('cabins/united-polaris', 'image-polaris-lounge-on-the-ground-3x', 1),
    ('cabins/united-polaris', 'onboard-experience-united-polaris-DESKTOP-image', 1),
    ('cabins/united-polaris', 'source_POLARIS_UPP_230425_SLE0905_rs_v3', 1),
    ('fleet', 'SeatMap', 30),
    ('lounges', 'couple-in-lounge', 1),
    ('lounges', 'iad-polaris-1-copy-3x', 1),
    ('lounges', 'image-houston-intercontinental-polaris-lounge-iah-3x', 1),
    ('deals', '3408x1068_GLTW', 3),
    ('deals', 'LAX-Sept23_1940x720', 1),
    ('deals', '2653_IAH_1940x611', 1),
    ('deals', 'surfer-3x.png', 1),
    ('deals', 'Crop_Earn_Page_Featured_Deals_Tile', 1),
    ('deals', 'brand-tile-large-style-2-3x', 1),
    ('mileageplus', 'premier-silver.svg', 1),
    ('mileageplus', 'premier-gold.svg', 1),
    ('mileageplus', 'image-million-miler-3x', 1),
    ('mileageplus', 'miles-pooling.svg', 1),
    ('mileageplus', 'whats-new-pluspoints-4098x1290', 1),
    ('mileageplus', '2283_PremierProgramUpdate-DT-hero_4098x1290', 1),
    ('mileageplus', '251026_MPS_ACQ-Bonus_Earn-page_Desktop_800x450', 1),
    ('mileageplus', 'mp-air-awards-mobile.webp', 1),
    ('mileageplus', 'blue-mp-shopping-3x', 1),
    ('wifi', 'united-premium-plus-United-Wi-Fi-1071x600', 1),
    ('wifi', 'starlink-internet-desktop-brand-tile-4098x750', 1),
    ('wifi', 'viaSat-updated_v2_1136x639-2x', 1),
    ('wifi', 'Panasonic_world_2272x1278', 1),
    ('food', 'Tortellini-En-Brodo-Desktop-Round', 1),
    ('food', 'Lasagna-Cauliflower-Bolognese', 1),
    ('food', 'Steak-Egg-Cheese-Potato-Burrito', 1),
    ('food', 'Bagel-Dots', 1),
    ('food', 'SnackBoxes_20241015_Wayne-Slezak0236_Takeoff', 1),
    ('food', 'Albanese-True-to-Fruit', 1),
    ('food', 'Just-Enough-Chardonnay', 1),
    ('baggage', 'carry-on-bag-286x340', 1),
    ('baggage', 'g-oversized-bag-3x', 1),
    ('baggage', 'luggage-cart.svg', 1),
    ('airport', 'expedited-TSA-mobile-816x369', 1),
    ('airport', 'expedited-sentri-mobile-816x366', 1),
    ('airport', 'expedited-clear-mobile-816x366', 1),
    ('airport', 'expedited-onestop-MOBILE-816x366', 1),
    ('airport', 'expedited-NEXUS-mobile-816x366', 1),
    ('airport', 'boarding-process-image-3x.webp', 1),
    ('app', 'on-the-united-app-1668-963', 1),
    ('app', 'on-our-website-1668-963', 1),
]


def _slugify(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]+', '-', name).strip('-')


def collect_urls() -> list[tuple[str, str]]:
    manifest = json.loads((SCRAPED / 'image_manifest.json').read_text())
    all_urls = sorted(manifest.get('all_urls') or
                      {u for rows in manifest['categories'].values() for u in rows}
                      | {manifest['home_hero']})
    picks: list[tuple[str, str]] = []
    for category, pattern, limit in WANT:
        matched = [u for u in all_urls if re.search(re.escape(pattern), u, re.I)]
        seen_any = False
        for url in matched[:limit]:
            picks.append((category, url))
            seen_any = True
        if not seen_any:
            print(f'  [warn] no match for {category}: {pattern}')
    seen, out = set(), []
    for cat, url in picks:
        if url in seen:
            continue
        seen.add(url)
        out.append((cat, url))
    return out


def _looks_like_image(data: bytes, name: str) -> bool:
    if name.casefold().endswith('.svg'):
        return b'<svg' in data[:600] or b'<?xml' in data[:200]
    if data[:2] == b'\xff\xd8':
        return True
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return True
    return False


def harvest_images() -> None:
    picks = collect_urls()
    print(f'[images] {len(picks)} curated upstream images')
    inventory = {'schema_version': 1, 'site': 'united_airlines',
                 'asset_count': 0, 'total_bytes': 0,
                 'captured_on': '2026-09-28',
                 'capture_method': ('Internet Archive web.archive.org replays of '
                                    'the real united.com media CDN (media.united.com)'),
                 'source_page': 'https://www.united.com/',
                 'notes': ('Every file is the real upstream image bytes: the '
                           'per-file source_url is the united.com media CDN URL '
                           'whose web.archive.org replay produced these bytes.'),
                 'assets': []}
    ok = fail = 0
    for cat, url in picks:
        category = cat.replace('/', '_')
        name = _slugify(url.rsplit('/', 1)[-1])
        target = STATIC / category / name
        if target.exists():
            data = target.read_bytes()
        else:
            try:
                data, _ = harvest.replay(url, '2025')
            except RuntimeError as exc:
                print(f'  [missing] {name}: {exc}', flush=True)
                fail += 1
                continue
            if not _looks_like_image(data, name):
                print(f'  [bad] {name}: not an image ({data[:12]!r})', flush=True)
                fail += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            time.sleep(harvest.REQUEST_SLEEP)
        inventory['assets'].append({
            'path': f'static/images/{category}/{name}',
            'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(),
            'source_url': url,
        })
        ok += 1
        print(f'  [ok] {category}/{name} ({len(data)} bytes)', flush=True)
    inventory['asset_count'] = len(inventory['assets'])
    inventory['total_bytes'] = sum(a['bytes'] for a in inventory['assets'])
    (SITE / 'asset_inventory.json').write_text(
        json.dumps(inventory, indent=1, sort_keys=True) + '\n')
    print(f'[images] ok={ok} fail={fail} inventory={inventory["asset_count"]} assets')


if __name__ == '__main__':
    harvest_images()
