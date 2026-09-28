"""Build asset_inventory.json + provenance.json for the speedo mirror.

Maps every shipped static asset to its upstream source URL and records
bytes + sha256, following the mta/michaels manifest schema.
"""
import hashlib
import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
STATIC = BASE / "static"
UPSTREAM = "https://speedo.com"

# 1. product + page images: filename -> upstream cdn url
product_urls = json.load(open(BASE / "scraped_data" / "product_image_urls.json"))
content_urls = json.load(open(BASE / "scraped_data" / "content_image_urls.json"))
content_urls = ["https://speedo.com" + u if u.startswith("/") else u for u in content_urls]

by_name = {}
for u in product_urls + content_urls:
    by_name[u.rsplit("/", 1)[-1].split("?")[0]] = u

assets = []
missing = []



# explicitly captured assets (banners, team profile cards, our-story images)
EXPLICIT = {
    "banners/hero-sale-desktop.jpg": "https://speedo.com/cdn/shop/files/promo-fidelity-1-hero-desktop.jpg?width=1600",
    "banners/iq-banner.jpg": "https://speedo.com/cdn/shop/files/iQ-secondary-1000x630-1.jpg?width=1600",
    "banners/biofuse-banner.jpg": "https://speedo.com/cdn/shop/files/Fitness2026-CLP-secondary-1000x630-5.jpg?width=1600",
    "banners/bags-banner.jpg": "https://speedo.com/cdn/shop/files/Club-training-secondary-accessories2.jpg?width=1600",
    "banners/dmc-banner.jpg": "https://speedo.com/cdn/shop/files/Fitness2026-CLP-secondary-1000x630-3.jpg?width=1600",
    "athletes/crop-666x666.jpg": "https://speedo.com/cdn/shop/files/crop-666x666.jpg",
    "pages/Playing_it_straight.jpg": "https://speedo.com/cdn/shop/files/Playing_it_straight.jpg",
    "pages/1946_ad_1_CMYK.jpg": "https://speedo.com/cdn/shop/files/1946_ad_1_CMYK.jpg",
    "pages/MR76MA.jpg": "https://speedo.com/cdn/shop/files/MR76MA.jpg",
    "pages/Winners_1.jpg": "https://speedo.com/cdn/shop/files/Winners_1.jpg",
    "pages/FFRPD5_1.jpg": "https://speedo.com/cdn/shop/files/FFRPD5_1.jpg",
    "pages/268ec2ee-1466-4ccb-8ab9-e64a3bb1767e.jpg": "https://speedo.com/cdn/shop/files/268ec2ee-1466-4ccb-8ab9-e64a3bb1767e.jpg",
    "pages/goggles_90s.jpg": "https://speedo.com/cdn/shop/files/goggles_90s.jpg",
    "pages/asset_5271.jpg": "https://speedo.com/cdn/shop/files/asset_5271.jpg",
}
for name in ["Leon-Marchand", "Adam-Peaty", "Aurelie-Rivard", "Tatjana-Smith", "Regan-Smith",
             "Matt-Richards", "Alice-Tai", "Duncan-Scott", "Kaylee-McKeown", "Benedetta-Pilato",
             "Ariarne-Titmus", "Jack-Alexy"]:
    EXPLICIT[f"athletes/team-speedo-{name.lower()}-profile.jpg"] = (
        f"https://speedo.com/cdn/shop/files/team-speedo-{name}-profile.jpg")

def add(path, source_url):

    full = STATIC / path
    if not full.is_file():
        missing.append(path)
        return
    data = full.read_bytes()
    assets.append({
        "path": f"static/{path}",
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "source_url": source_url,
    })


# products/, pages/, banners/, nav/ — filename-keyed CDN mapping
for sub in ["products", "pages", "banners", "nav"]:
    d = STATIC / "images" / sub
    if not d.is_dir():
        continue
    for f in sorted(d.iterdir()):
        if not f.is_file():
            continue
        url = by_name.get(f.name) or EXPLICIT.get(f"{sub}/{f.name}")
        if url is None:
            missing.append(f"images/{sub}/{f.name}")
            continue
        add(f"images/{sub}/{f.name}", url)

# athletes/: captured from athlete pages (hero + profile cards)
athlete_urls = {
    "adam-ramsay-peaty-hero.jpg": "https://speedo.com/cdn/shop/files/adam-ramsay-peaty.jpg",
    "adam-ramsay-peaty-profile.jpg": "https://speedo.com/cdn/shop/files/Adam_Ramsay_Peaty.jpg",
    "alice-tai-hero.jpg": "https://speedo.com/cdn/shop/files/alice-tai.jpg",
    "alice-tai-profile.jpg": "https://speedo.com/cdn/shop/files/Alice_Tai.jpg",
    "duncan-scott-hero.jpg": "https://speedo.com/cdn/shop/files/duncan-scott.jpg",
    "duncan-scott-profile.jpg": "https://speedo.com/cdn/shop/files/Duncan_Scott.jpg",
    "matt-richards-hero.jpg": "https://speedo.com/cdn/shop/files/matt-richards.jpg",
    "matt-richards-profile.jpg": "https://speedo.com/cdn/shop/files/Matt_Richards.jpg",
    "leon-marchand-hero.jpg": "https://speedo.com/cdn/shop/files/leon-marchand.jpg",
    "leon-marchand-profile.jpg": "https://speedo.com/cdn/shop/files/Leon_Marchand.jpg",
    "caeleb-dressel-hero.jpg": "https://speedo.com/cdn/shop/files/caeleb-dressel.jpg",
    "caeleb-dressel-profile.jpg": "https://speedo.com/cdn/shop/files/Caeleb_Dressel.jpg",
    "kaylee-mckeown-hero.jpg": "https://speedo.com/cdn/shop/files/kaylee-mckeown.jpg",
    "kaylee-mckeown-profile.jpg": "https://speedo.com/cdn/shop/files/Kaylee_McKeown.jpg",
    "ariarne-titmus-hero.jpg": "https://speedo.com/cdn/shop/files/ariarne-titmus.jpg",
    "ariarne-titmus-profile.jpg": "https://speedo.com/cdn/shop/files/Ariarne_Titmus.jpg",
    "meg-harris-hero.jpg": "https://speedo.com/cdn/shop/files/meg-harris.jpg",
    "meg-harris-profile.jpg": "https://speedo.com/cdn/shop/files/Meg_Harris.jpg",
    "mollie-ocallaghan-hero.jpg": "https://speedo.com/cdn/shop/files/mollie-ocallaghan.jpg",
    "mollie-ocallaghan-profile.jpg": "https://speedo.com/cdn/shop/files/Mollie_OCallaghan.jpg",
    "emma-weyant-hero.jpg": "https://speedo.com/cdn/shop/files/emma-weyant.jpg",
    "emma-weyant-profile.jpg": "https://speedo.com/cdn/shop/files/Emma_Weyant.jpg",
    "jack-alexy-hero.jpg": "https://speedo.com/cdn/shop/files/jack-alexy.jpg",
    "jack-alexy-profile.jpg": "https://speedo.com/cdn/shop/files/jack-alexy-crop-666x666.jpg",
    "aurelie-rivard-hero.jpg": "https://speedo.com/cdn/shop/files/aurelie-rivard.jpg",
    "aurelie-rivard-profile.jpg": "https://speedo.com/cdn/shop/files/Aurelie_Rivard.jpg",
    "benedetta-pilato-hero.jpg": "https://speedo.com/cdn/shop/files/benedetta-pilato.jpg",
    "benedetta-pilato-profile.jpg": "https://speedo.com/cdn/shop/files/Benedetta_Pilato.jpg",
    "regan-smith-hero.jpg": "https://speedo.com/cdn/shop/files/regan-smith.jpg",
    "regan-smith-profile.jpg": "https://speedo.com/cdn/shop/files/Regan_Smith.jpg",
    "tatjana-smith-hero.jpg": "https://speedo.com/cdn/shop/files/tatjana-smith.jpg",
    "tatjana-smith-profile.jpg": "https://speedo.com/cdn/shop/files/Tatjana_Smith.jpg",
    "team-speedo-hero-desktop.jpg": "https://speedo.com/cdn/shop/files/team-speedo-hero.jpg",
}
for f in sorted((STATIC / "images" / "athletes").iterdir()):
    if not f.is_file():
        continue
    url = by_name.get(f.name) or athlete_urls.get(f.name) or EXPLICIT.get(f"athletes/{f.name}")
    if url is None:
        missing.append(f"images/athletes/{f.name}")
        continue
    add(f"images/athletes/{f.name}", url)

# icons: logo svg from the upstream theme
add("icons/logo.svg", "https://speedo.com/cdn/shop/t/4/assets/logo.svg")

inv = {
    "schema_version": 1,
    "asset_count": len(assets),
    "assets": assets,
}
(BASE / "asset_inventory.json").write_text(json.dumps(inv, indent=1))
print(f"asset_inventory.json: {len(assets)} assets")
if missing:
    print("MISSING source urls for:")
    for m in missing[:30]:
        print("  -", m)
    print(f"  ({len(missing)} total)")
