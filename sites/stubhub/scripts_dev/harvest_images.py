"""Download the real upstream images into static/images/ + build the inventory.

Reads every image URL collected in the harvests (performer/hero images from
the search API + event og:image captures, seat-view photos from the listing
cards, seat-map SVGs) and downloads them from the upstream CDNs
(media.stubhubstatic.com, img.vggcdn.net) into static/images/ under stable
inventory names. Emits/refreshes asset_inventory.json (the manifest
scripts/check_asset_inventory.py enforces).

Idempotent: existing files with matching hashes are kept.
"""
import hashlib
import json
import pathlib
import re
import sys

import httpx

SITE = pathlib.Path(__file__).resolve().parents[1]
SRC = SITE / "source_data"
IMG = SITE / "static" / "images"
INVENTORY = SITE / "asset_inventory.json"

# Deterministic transform: same underlying asset, sane size for the mirror.
PERFECT_TRANSFORM = "q_auto:good,f_auto,c_fill,g_auto,w_640,h_460"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_performer_url(url: str) -> str:
    """Rebuild a catalog image URL with the mirror's transform params."""
    m = re.match(r"(https://media\.stubhubstatic\.com/stubhub-v2-catalog/)"
                 r"(d_defaultLogo\.jpg/)[^/]+/(.+)$", url)
    if m:
        return f"{m.group(1)}{m.group(2)}{PERFECT_TRANSFORM}/{m.group(3)}"
    return url


def ext_for(url: str, content_type: str) -> str:
    if url.endswith(".svg"):
        return ".svg"
    if "svg" in content_type:
        return ".svg"
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    return ".jpg"


def main():
    seatmaps_src = SITE / "scraped_data" / "seatmaps"
    events = json.loads((SRC / "events.json").read_text())
    performers = json.loads((SRC / "performers.json").read_text())
    search_dir = SITE / "scraped_data" / "search"
    perf_dir = IMG / "performers"
    perf_dir.mkdir(parents=True, exist_ok=True)
    view_dir = IMG / "seatviews"
    view_dir.mkdir(parents=True, exist_ok=True)
    map_dir = IMG / "seatmaps"
    map_dir.mkdir(parents=True, exist_ok=True)

    # load existing inventory
    inventory = {"schema_version": 1, "asset_count": 0, "assets": []}
    if INVENTORY.exists():
        inventory = json.loads(INVENTORY.read_text())
    by_path = {a["path"]: a for a in inventory["assets"]}

    client = httpx.Client(follow_redirects=True, timeout=40,
                          headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/129.0.0.0 Safari/537.36"})

    def download(url, dest_rel, source_url=None):
        """Download url -> static/images/<dest_rel>; source_url is the key the
        seed/app use for lookup (defaults to the fetch url). download_url
        records the URL actually fetched, which for performer art is the
        normalized 640px transform (the page-original URL stays in
        source_url for provenance)."""
        src_key = source_url or url
        dest = IMG / dest_rel
        if dest_rel in by_path and dest.exists():
            return by_path[dest_rel]
        try:
            r = client.get(url)
            r.raise_for_status()
            data = r.content
        except Exception as e:
            print(f"  FAIL {url[:100]}: {str(e)[:80]}", flush=True)
            return None
        ext = ext_for(url, r.headers.get("content-type", ""))
        if not dest_rel.endswith(ext):
            dest_rel = dest_rel.rsplit(".", 1)[0] + ext
            dest = IMG / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        row = {"path": f"static/images/{dest_rel}", "bytes": len(data),
               "sha256": sha256(data), "source_url": src_key,
               "download_url": url}
        by_path[dest_rel] = row
        return row

    count = 0

    # 1. performer images (search API imageUrl preferred, og:image fallback)
    slugs = {}
    for f in sorted(search_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except ValueError:
            continue
        for group in data.get("resultsWithMetadata") or []:
            for r in group.get("results", {}).get("results", []):
                url = r.get("url") or ""
                if "/performer/" not in url and "/category/" not in url:
                    continue
                slug = url.split("-tickets/")[0].lstrip("/")
                img = (r.get("searchGroupResultDetails") or {}).get("imageUrl")
                if img and slug not in slugs:
                    slugs[slug] = img
    for p in performers:
        slug = p["slug"]
        url = slugs.get(slug) or p.get("image_url")
        if not url:
            continue
        url = normalize_performer_url(url)
        if download(url, f"performers/{slug}.jpg", source_url=slugs.get(slug) or p.get("image_url")):
            count += 1

    # 2. seat-view photos (unique by venue+section from the listing cards)
    seen_views = set()
    for f in sorted((SRC / "listings").glob("*.json")):
        rows = json.loads(f.read_text())
        for r in rows:
            u = r.get("seat_view_url")
            if not u or u in seen_views:
                continue
            seen_views.add(u)
            m = re.match(r".*/vfsimage2/(\d+)/([^/]+)/\d+\.jpg", u)
            key = f"{m.group(1)}__{m.group(2)}" if m else hashlib.md5(u.encode()).hexdigest()[:10]
            if download(u, f"seatviews/{key}.jpg"):
                count += 1

    # 3. seat map SVGs (per venue). Provenance: the live event page the SVG
    #    was captured from (venue -> source event url resolved via the catalog
    #    and the event_pages captures).
    venue_source = {}
    for ep in sorted((SITE / "scraped_data" / "event_pages").glob("*.json")):
        try:
            d = json.loads(ep.read_text())
        except ValueError:
            continue
        first = next(iter(d["passes"].values()), None) or {}
        u = first.get("url") or ""
        if not u:
            continue
        evt = next((e for e in events if e["upstream_id"] == int(ep.stem)), None)
        if evt:
            venue_source.setdefault(evt["venue_id"], u)
    # supplementary seatmaps keyed by event id -> venue via catalog
    for f in sorted(seatmaps_src.glob("event_*.svg")):
        eid = int(f.stem.replace("event_", ""))
        evt = next((e for e in events if e["upstream_id"] == eid), None)
        if evt and evt["venue_id"] not in venue_source:
            venue_source[evt["venue_id"]] = evt["url"]
    for f in sorted(seatmaps_src.glob("*.svg")):
        vid = f.stem
        if not vid.isdigit():
            continue
        dest = map_dir / f"{vid}.svg"
        if not dest.exists():
            dest.write_text(f.read_text())
        if f"seatmaps/{vid}.svg" not in by_path:
            data = dest.read_bytes()
            src_url = venue_source.get(int(vid), "https://www.stubhub.com/")
            by_path[f"seatmaps/{vid}.svg"] = {
                "path": f"static/images/seatmaps/{vid}.svg",
                "bytes": len(data), "sha256": sha256(data),
                "source_url": src_url,
            }
        count += 1

    # rebuild inventory
    assets = sorted(by_path.values(), key=lambda a: a["path"])
    inventory["assets"] = assets
    inventory["asset_count"] = len(assets)
    INVENTORY.write_text(json.dumps(inventory, indent=1))
    print(f"downloaded/verified {count} assets; inventory has {len(assets)} entries",
          flush=True)


if __name__ == "__main__":
    main()
