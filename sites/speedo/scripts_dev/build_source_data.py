#!/usr/bin/env python3
"""Assemble source_data.json from the captured speedo.com scrape data.

Reads scraped_data/{collections.json, details.json, unique_products.json,
content_raw.json, faqs.json, content_html/*.html} plus the recon captures in
scripts_dev/recon/ and writes source_data.json — the tracked single input the
deterministic seed (seed_data.py) materializes into SQLite at build time.

Run from sites/speedo/:  python3 scripts_dev/build_source_data.py
"""
import html as html_mod
import json
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parent
SCRAPED = SITE / "scraped_data"
HTML_DIR = SCRAPED / "content_html"
RECON = HERE / "recon"

UPSTREAM = "https://speedo.com"
CAPTURED = "2026-09-26"

# Real athlete display names + national teams as captured from the upstream
# Team Speedo pages (2026-09-26).
ATHLETE_META = {
    'leon-marchand': ('Léon Marchand', 'France'),
    'adam-peaty': ('Adam Ramsay-Peaty', 'GB'),
    'alice-tai': ('Alice Tai', 'GB'),
    'ariarne-titmus': ('Ariarne Titmus', 'Australia'),
    'aurelie-rivard': ('Aurélie Rivard', 'Canada'),
    'benedetta-pilato': ('Benedetta Pilato', 'Italy'),
    'duncan-scott': ('Duncan Scott', 'GB'),
    'jack-alexy': ('Jack Alexy', 'USA'),
    'kaylee-mckeown': ('Kaylee McKeown', 'Australia'),
    'matt-richards': ('Matt Richards', 'GB'),
    'regan-smith': ('Regan Smith', 'USA'),
    'tatjana-smith': ('Tatjana Smith', 'South Africa'),
}

# Hub pages: hero heading + CTA + featured collection (real upstream copy).
HUB_META = {
    'women': {'heading': 'SECOND SKIN FOR SPRINTERS.', 'cta': 'Shop New Fastskin', 'featured': 'women-new-arrivals'},
    'men': {'heading': 'BUILT FOR SPEED.', 'cta': 'Shop Men', 'featured': 'men-new-arrivals'},
    'kids': {'heading': 'MAKE A SPLASH.', 'cta': 'Shop Kids', 'featured': 'kids-new-arrivals'},
    'goggles': {'heading': 'PRECISION LIKE. NO. OTHER.', 'cta': 'Shop Fastskin Goggles', 'featured': 'goggles-new-arrivals'},
    'accessories': {'heading': 'GEAR UP.', 'cta': 'Shop Accessories', 'featured': 'accessories-all'},
    'speedo-iq': {'heading': 'KNOW MORE THAN EVER BEFORE', 'cta': 'Shop Speedo iQ', 'featured': 'goggles-speedo-iq'},
    'fastskin': {'heading': 'FASTSKIN', 'cta': 'Shop Fastskin', 'featured': 'women-fastskin'},
    'biofuse': {'heading': 'BIOFUSE', 'cta': 'Shop Biofuse', 'featured': 'goggles-biofuse'},
    'vanquisher': {'heading': 'VANQUISHER', 'cta': 'Shop Vanquisher', 'featured': 'goggles-vanquisher'},
    'training': {'heading': 'TRAINING', 'cta': 'Shop Training', 'featured': 'accessories-training-aids'},
    'fitness': {'heading': 'FITNESS', 'cta': 'Shop Fitness', 'featured': 'women-fitness'},
    'recreation': {'heading': 'RECREATION', 'cta': 'Shop Recreation', 'featured': 'women-recreation'},
    'racing': {'heading': 'RACING', 'cta': 'Shop Racing', 'featured': 'women-racing'},
    'outdoor-swim': {'heading': 'OUTDOOR SWIM', 'cta': 'Shop Outdoor Swim', 'featured': 'women-outdoor-swim'},
    'lookout': {'heading': 'LAND TO WATER', 'cta': 'Shop Land to Water', 'featured': 'women-land-to-water'},
    'black-friday': {'heading': 'THE SPEEDO BLACK FRIDAY EVENT', 'cta': 'Shop Sale', 'featured': 'women-sale'},
}

LOGO_HASH = '4b42d128be9a91dcb46dac8a5ad746cc1ab14c2a'


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def parse_price(text):
    if not text:
        return None, None
    reg = re.search(r'Regular price\s+(?:From\s+)?£([\d.]+)', text)
    sal = re.search(r'Sale price\s+(?:From\s+)?£([\d.]+)', text)
    price = float(sal.group(1)) if sal else (float(reg.group(1)) if reg else None)
    compare = float(reg.group(1)) if (sal and reg) else None
    return price, compare


def swatch_rgb(style):
    m = re.search(r'rgb\(([^)]+)\)', style or '')
    if m:
        return '#' + ''.join(f"{int(x):02x}" for x in m.group(1).split(','))
    return '#666666'


def strip_tags(fragment):
    text = html_mod.unescape(re.sub(r'<[^>]+>', ' ', fragment))
    return re.sub(r'\s+', ' ', text).strip().replace('\xa0', ' ').strip()


def strip_tags_inline_safe(fragment):
    """Strip tags without breaking words split across inline tags."""
    text = re.sub(r'<(?:br|/p)[^>]*>', '\n', fragment)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()


CATEGORY_RULES = [
    (r'goggles|optical', 'Goggles'),
    (r'\bmask\b', 'Goggle Mask'),
    (r'jammer', 'Jammer'),
    (r'aquashort', 'Aquashorts'),
    (r'\bbrief\b|briefs', 'Briefs'),
    (r'swim short|swim shorts|board short', 'Swim Shorts'),
    (r'rashguard|rash guard|sun protection top|sun top', 'Rashguard'),
    (r'bikini', 'Bikini'),
    (r'tankini', 'Tankini'),
    (r'two piece|2 piece', 'Two Piece Sets'),
    (r'swimsuit|medalist|thinstrap|muscleback|kneeskin|flyback|leaderback|powerback|recordback|ultraback|crossback|openback|closedback|hyperboom|splice|hydrasuit', 'Swimsuit'),
    (r'legsuit', 'Legsuit'),
    (r'shaping', 'Body Shaping'),
    (r'\bcap\b', 'Cap'),
    (r'rucksack|backpack|duffel|mesh bag|holdall|sack|\bbag\b', 'Bag'),
    (r'\bfin\b|\bfins\b|monofin', 'Fins'),
    (r'towel', 'Towel'),
    (r'kickboard|pullbuoy|pull buoy|hand paddle|paddle|training aid|\bbuoy\b|\bband\b', 'Training Aid'),
    (r'snorkel', 'Snorkel'),
    (r'slide|sandal|footwear|shoe|water shoe', 'Footwear'),
    (r'wetsuit', 'Wetsuit'),
    (r'water bottle|\bbottle\b', 'Water Bottle'),
    (r'ear plug|nose clip|noseclip', 'Swim Care'),
    (r'tshirt|t-shirt|hoodie|jacket|jogger|\btee\b|clothing|sweat', 'Clothing'),
    (r'\btoy\b|\bfloat\b|noodle', 'Swim Toy'),
]


def infer_category(name, collections):
    n = name.lower()
    for pat, cat in CATEGORY_RULES:
        if re.search(pat, n):
            return cat
    for c in collections:
        cl = c.lower()
        if 'one-piece' in cl: return 'Swimsuit'
        if 'bikinis' in cl: return 'Bikini'
        if 'jammers' in cl: return 'Jammer'
        if 'briefs' in cl: return 'Briefs'
        if 'aquashorts' in cl: return 'Aquashorts'
        if 'swim-shorts' in cl: return 'Swim Shorts'
        if 'rashguards' in cl: return 'Rashguard'
        if 'bags' in cl: return 'Bag'
        if 'caps' in cl: return 'Cap'
        if 'fins' in cl: return 'Fins'
        if 'towels' in cl: return 'Towel'
        if 'training-aids' in cl: return 'Training Aid'
        if 'snorkelling' in cl: return 'Snorkel'
        if 'footwear' in cl: return 'Footwear'
        if 'goggles' in cl: return 'Goggles'
        if 'clothing' in cl: return 'Clothing'
        if 'swimwear' in cl: return 'Swimsuit'
    return 'Swimwear'


def sections_of(raw):
    return re.findall(r'<section[^>]*id="shopify-section-[^"]*"[^>]*>(.*?)</section>', raw, re.S)


def page_hero(raw):
    """First meaningful hero image of a page (skip nav/logo images)."""
    for m in re.finditer(r'<img[^>]+src="([^"]+)"[^>]*>', raw):
        src = m.group(1).split('?')[0]
        fname = src.rsplit('/', 1)[-1]
        if 'Vector.svg' in fname or fname.startswith(('Nav_', 'nav-')):
            continue
        if '/cdn/shop/' not in src:
            continue
        if re.match(r'^8[0-9a-eA-E]', fname):   # product shot, not a hero
            continue
        if 'hero' in fname.lower() or 'CLP' in fname or 'hero' in src.lower():
            return f"pages/{fname}", src
    return '', ''


def main():
    colls = json.loads((SCRAPED / "collections.json").read_text())
    details = json.loads((SCRAPED / "details.json").read_text())
    uniq = json.loads((SCRAPED / "unique_products.json").read_text())
    content = json.loads((SCRAPED / "content_raw.json").read_text())
    faqs = json.loads((SCRAPED / "faqs.json").read_text())
    nav_struct = json.loads((RECON / "nav_structure.json").read_text())

    # ---- department per product (priority: goggles > accessories > kids > men > women) ----
    DEPT_PRIORITY = [
        ('goggles', 'goggles'),
        ('accessories', 'accessories'),
        ('speedo-dmc', 'accessories'),
        ('speedo-minions', 'accessories'),
        ('girls', 'kids'), ('boys', 'kids'), ('kids', 'kids'), ('teen', 'kids'),
        ('men-', 'men'),
        ('women', 'women'),
    ]
    dept_of = {}
    for path in uniq:
        member_collections = []
        for slug, blob in colls.items():
            if any(p['norm_path'] == path for p in blob['products']):
                member_collections.append(slug)
        dept = 'accessories'
        for prefix, d in DEPT_PRIORITY:
            if any(slug.startswith(prefix) for slug in member_collections):
                dept = d
                break
        dept_of[path] = dept

    # ---- collections per product (ordered) ----
    prod_collections = defaultdict(list)
    for slug, blob in colls.items():
        for p in blob['products']:
            prod_collections[p['norm_path']].append(slug)

    # ---- colourway groups via sibling union-find ----
    paths = sorted(uniq.keys())
    index = {p: i for i, p in enumerate(paths)}
    parent = list(range(len(paths)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for p, v in details.items():
        for sib in (v.get('colourSiblings') or []):
            if sib['href'] in index:
                union(index[p], index[sib['href']])
    group_members = defaultdict(list)
    for p in paths:
        group_members[find(index[p])].append(p)
    group_of = {}
    for r, members in group_members.items():
        key = re.sub(r'^(?:womens?|mens?|girls?|boys?|adult|unisex)[\s\']?', '', uniq[members[0]]['title'])
        key = re.sub(r'\s+(black|white|navy|blue|red|green|grey|gray|pink|purple|teal|orange|yellow|clear|smoke|mirror|polarised|iridescent|khaki|burgundy|lilac|mint|coral|royal|indigo|jade|olive|sand|cream|multi|colour|color)[\w /]*$', '', key, flags=re.I)
        key = re.sub(r'\s*[-/]\s*\w+$', '', key).strip().lower()
        for m in members:
            group_of[m] = key

    # ---- products ----
    products = []
    for path in paths:
        card = uniq[path]
        det = details.get(path, {})
        slug = path.replace('/products/', '')
        dept = dept_of[path]
        member_collections = prod_collections.get(path, [])
        price, compare = parse_price(det.get('price') or card.get('price'))
        card_badges = set(card.get('badges') or [])
        sizes = det.get('sizes') or []
        # NOTE: the product-page 'Out of stock' span is a hidden template element
        # present on every upstream PDP — the real stock signals are the card
        # 'Sold out' badge and the per-variant 'Variant sold out' labels.
        sold_out = ('Sold out' in card_badges
                    or (bool(sizes) and all(s['soldOut'] for s in sizes)))
        images = []
        for g in (det.get('gallery') or []):
            fname = g.rsplit('/', 1)[-1]
            if LOGO_HASH in fname:
                continue
            images.append(f"products/{fname}")
        if not images and card.get('img'):
            fname = card['img'].rsplit('/', 1)[-1].split('?')[0]
            images.append(f"products/{fname}")
        specs = det.get('specs') or {}
        name = card.get('title') or det.get('h1') or slug
        colour = det.get('colour') or ''
        swatch = ''
        for sib in (det.get('colourSiblings') or []):
            if sib['href'] == path:
                swatch = swatch_rgb(sib.get('swatch'))
        if not swatch:
            swatch = swatch_rgb(colour)
        is_kids = (dept == 'kids' or bool(re.match(r'^(kids|girls|boys|teen)', slug))
                   or any(c.startswith(('girls', 'boys', 'kids')) for c in member_collections))
        products.append({
            'slug': slug,
            'name': name,
            'sku': det.get('sku') or '',
            'department': dept,
            'category': infer_category(name, member_collections),
            'colourway_group': group_of[path],
            'colour': colour,
            'colour_swatch': swatch,
            'price': price or 0.0,
            'compare_at_price': compare or 0.0,
            'is_sale': 'On Sale' in card_badges or any('-sale' in c for c in member_collections),
            'is_new': 'New' in card_badges or any('-new-arrivals' in c for c in member_collections),
            'is_bestseller': any('-bestsellers' in c for c in member_collections),
            'is_exclusive': 'Exclusive' in card_badges or any('-exclusives' in c for c in member_collections),
            'sold_out': sold_out,
            'is_kids': is_kids,
            'description': det.get('description') or '',
            'delivery': det.get('delivery') or '',
            'specs': specs,
            'activity': specs.get('Activity', ''),
            'fabric': specs.get('Fabric', ''),
            'back_shape': specs.get('Back Shape', ''),
            'lens_type': specs.get('Lens Type', ''),
            'collection_line': specs.get('Collection', ''),
            'images': images,
            'sizes': [{'size': s['size'], 'sold_out': s['soldOut']} for s in sizes],
            'collections': member_collections,
            'upstream_url': f"{UPSTREAM}{path}",
        })

    # ---- collections ----
    nav_slugs = set()
    for dept in nav_struct:
        for block in dept['blocks']:
            for link in block['links']:
                h = link['href']
                if h.startswith('/collections/'):
                    nav_slugs.add(h[len('/collections/'):])
    collections = []
    for slug, blob in sorted(colls.items()):
        if slug == 'women-swimsuit-quiz':
            continue
        dept = 'accessories'
        for prefix, d in DEPT_PRIORITY:
            if slug.startswith(prefix):
                dept = d
                break
        collections.append({
            'slug': slug,
            'name': slug.replace('-', ' ').replace('_', ' ').title().replace('Speedo Iq', 'Speedo iQ'),
            'department': dept,
            'in_mega_menu': slug in nav_slugs,
            'products': [p['norm_path'].replace('/products/', '') for p in blob['products']],
        })

    # ---- content pages ----
    pages = {}

    def add_h2h3_page(slug, title, html_path):
        raw = (HTML_DIR / html_path).read_text()
        main = re.search(r'<main[^>]*>(.*?)</main>', raw, re.S)
        seg = main.group(1) if main else raw
        seg = re.sub(r'<script.*?</script>', '', seg, flags=re.S)
        seg = re.sub(r'<style.*?</style>', '', seg, flags=re.S)
        tokens = re.findall(r'<(h2|h3|h4|h5|p|li)[^>]*>(.*?)</\1>', seg, re.S)
        blocks = []
        cur = None
        for tag, inner in tokens:
            text = strip_tags(inner)
            if not text or len(text) < 3:
                continue
            if tag in ('h2', 'h3', 'h4', 'h5'):
                if cur:
                    blocks.append(cur)
                cur = {'heading': text, 'paragraphs': [], 'items': []}
            elif tag == 'li':
                if cur is None:
                    cur = {'heading': '', 'paragraphs': [], 'items': []}
                cur['items'].append(text)
            else:
                if cur is None:
                    cur = {'heading': '', 'paragraphs': [], 'items': []}
                cur['paragraphs'].append(text)
        if cur:
            blocks.append(cur)
        # drop the first block if it only repeats the page title
        if blocks and blocks[0]['heading'].lower().strip() == title.lower():
            blocks = blocks[1:]
        pages[slug] = {'title': title, 'blocks': blocks}

    add_h2h3_page('returns', 'Returns', 'page-returns.html')
    add_h2h3_page('delivery', 'Delivery', 'page-delivery.html')
    add_h2h3_page('speedo-iq', 'Meet Speedo iQ', 'page-speedo-iq.html')
    add_h2h3_page('klarna', 'Pay Later With Klarna', 'page-klarna.html')
    add_h2h3_page('discounts', 'Discounts', 'page-discounts.html')
    add_h2h3_page('terms-conditions', 'Terms & Conditions', 'page-terms-conditions.html')
    add_h2h3_page('privacy-notice', 'Privacy Notice', 'page-privacy-notice.html')
    add_h2h3_page('cookie-policy', 'Cookie Policy', 'page-cookie-policy.html')
    add_h2h3_page('declaration-of-conformity', 'Declaration of Conformity', 'page-declaration-of-conformity.html')
    add_h2h3_page('biofuse', 'Biofuse', 'page-biofuse.html')

    # our story: media-with-text sections (heading + description + image)
    raw = (HTML_DIR / 'page-our-story.html').read_text()
    story_blocks = []
    for sec in sections_of(raw):
        h = re.search(r'<h[123][^>]*>\s*(.*?)\s*</h[123]>', sec, re.S)
        d = re.search(r'class="[^"]*__description[^"]*"[^>]*>\s*(.*?)\s*</div>', sec, re.S)
        img = re.search(r'<img[^>]+src="([^"]+)"', sec)
        if not h:
            continue
        heading = strip_tags(h.group(1))
        if heading.lower() in ('your basket is empty', 'your basket'):
            continue
        block = {'heading': heading, 'paragraphs': [], 'items': []}
        if d:
            block['paragraphs'].append(strip_tags(d.group(1)))
        if img:
            fname = img.group(1).split('?')[0].rsplit('/', 1)[-1]
            if 'Vector' not in fname and not fname.startswith(('Nav_', 'nav-')):
                block['image'] = f"pages/{fname}"
        story_blocks.append(block)
    pages['our-story'] = {'title': 'Our Story', 'blocks': story_blocks}

    # hub pages: hero + heading + featured collection; keep FAQ/text blocks when present
    for slug, meta in HUB_META.items():
        raw = (HTML_DIR / f'page-{slug}.html').read_text()
        hero, _src = page_hero(raw)
        blocks = []
        # capture any h2/h3 + p "questions" style content (e.g. speedo-iq handled above)
        pages[slug] = {
            'title': meta['heading'].title() if slug in ('fastskin', 'biofuse', 'vanquisher',
                                                          'training', 'fitness', 'recreation',
                                                          'racing', 'outdoor-swim', 'lookout') else meta['heading'],
            'hero_image': hero,
            'hero_heading': meta['heading'],
            'cta': meta['cta'],
            'cta_href': f"/collections/{meta['featured']}" if meta['featured'] else '/collections/women-sale',
            'is_hub': True,
            'featured_collection': meta['featured'],
            'blocks': blocks,
        }
    # speedo-iq also gets hub treatment (hero + featured) but keep its FAQ blocks
    raw_iq = (HTML_DIR / 'page-speedo-iq.html').read_text()
    hero_iq, _ = page_hero(raw_iq)
    if not hero_iq or 'Vector' in hero_iq:
        hero_iq = 'pages/This_Is.png'
    pages['speedo-iq'].update({'hero_image': hero_iq or pages['speedo-iq'].get('hero_image', ''),
                               'hero_heading': HUB_META['speedo-iq']['heading'],
                               'cta': HUB_META['speedo-iq']['cta'],
                               'cta_href': f"/collections/{HUB_META['speedo-iq']['featured']}",
                               'is_hub': True,
                               'featured_collection': HUB_META['speedo-iq']['featured']})

    # ---- athletes ----
    athletes = []
    for slug, (name, team) in ATHLETE_META.items():
        raw = (HTML_DIR / f'athlete-{slug}.html').read_text()
        quote_m = re.search(r'<p><em>"([^"]{5,140})"</em></p>', raw)
        paras = []
        hero = portrait = ''
        for sec in sections_of(raw):
            d = re.search(r'class="[^"]*(?:description|rich-text__description)[^"]*"[^>]*>(.*?)</div>', sec, re.S)
            img = re.search(r'<img[^>]+src="([^"]+)"', sec)
            if d:
                text = strip_tags(d.group(1))
                if len(text) > 60 and 'TEAM' not in text[:10]:
                    paras.append(text)
            if img:
                fname = img.group(1).split('?')[0].rsplit('/', 1)[-1]
                if 'hero-desktop' in fname:
                    hero = f"athletes/{fname}"
                elif 'portrait' in fname.lower() and not portrait:
                    portrait = f"athletes/{fname}"
        card = f"athletes/team-speedo-{slug}-profile.jpg"
        card_path = SITE / 'static' / 'images' / card
        if not card_path.exists():
            card = 'athletes/crop-666x666.jpg'   # Jack Alexy's upstream card tile
        athletes.append({
            'slug': slug,
            'name': name,
            'team': team,
            'quote': quote_m.group(1) if quote_m else '',
            'bio': '\n\n'.join(paras),
            'hero_image': hero,
            'portrait_image': portrait,
            'card_image': card,
        })

    # ---- articles ----
    articles = []
    for art in content.get('articles', []):
        raw = (HTML_DIR / f"article-{art['slug']}.html").read_text()
        main = re.search(r'<main[^>]*>(.*?)</main>', raw, re.S)
        seg = main.group(1) if main else raw
        seg = re.sub(r'<script.*?</script>', '', seg, flags=re.S)
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', seg, re.S)
        title = strip_tags(h1.group(1)) if h1 else art['title'].replace(' | Speedo', '').strip()
        dt_m = re.search(r'datetime="([\d]{4})-([\d]{2})-([\d]{2})', raw)
        if dt_m:
            months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                      'August', 'September', 'October', 'November', 'December']
            published = f"{months[int(dt_m.group(2)) - 1]} {int(dt_m.group(3))}, {dt_m.group(1)}"
        else:
            published = ''
        body_html = re.search(r'<div[^>]*class="[^"]*article[^"]*__content[^"]*"[^>]*>(.*?)</div>\s*(?:</article|<section|</div)', seg, re.S)
        if not body_html:
            body_html = re.search(r'<article[^>]*>(.*?)</article>', seg, re.S)
        body = ''
        if body_html:
            body = strip_tags_inline_safe(body_html.group(1))
        else:
            text = art['text']
            if title.upper() in text.upper():
                text = text[text.upper().find(title.upper()) + len(title):]
            body = text.split('Back to blog')[0].strip()
        image = ''
        for im in art.get('images', []):
            f = im['src'].rsplit('/', 1)[-1]
            if f.startswith(('Landscape', 'Speedo_S', 'Speedo_SS')):
                image = f"pages/{f}"
                break
        articles.append({
            'slug': art['slug'],
            'title': title,
            'published': published,
            'summary': body.split('.')[0][:200] + '.' if body else '',
            'body': body,
            'image': image,
        })

    # ---- faqs ----
    faq_rows = [{'question': f['q'], 'answer': f['a']} for f in faqs]

    # ---- discounts ----
    discounts = [
        {'code': 'WELCOME15', 'kind': 'percent', 'value': 15.0, 'min_spend': 0.0,
         'description': '15% off your first order — Speedo community welcome offer (see newsletter signup).'},
    ]

    source = {
        'captured_at': CAPTURED,
        'upstream': UPSTREAM,
        'products': products,
        'collections': collections,
        'nav': nav_struct,
        'pages': pages,
        'athletes': athletes,
        'articles': articles,
        'faqs': faq_rows,
        'discounts': discounts,
    }
    out = SITE / 'source_data.json'
    out.write_text(json.dumps(source, indent=1, ensure_ascii=False))
    print(f"source_data.json written: {len(products)} products, {len(collections)} collections, "
          f"{len(pages)} pages, {len(athletes)} athletes, {len(articles)} articles, {len(faq_rows)} faqs")
    print(f"size: {out.stat().st_size / 1e6:.1f} MB")


if __name__ == '__main__':
    main()
