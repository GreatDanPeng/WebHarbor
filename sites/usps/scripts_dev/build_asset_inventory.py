#!/usr/bin/env python3
"""Build sites/usps/asset_inventory.json from the downloaded image manifest.

Every managed asset (static/images/**) gets a row with its byte size,
SHA-256 digest and the upstream URL it was fetched from. The output is
the exact contract scripts/check_asset_inventory.py verifies at build
time: complete coverage of static/images + static/external_cache, no
duplicates, valid framing headers.

Run from sites/usps:  python3 scripts_dev/build_asset_inventory.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
MANIFEST = SITE / "scraped_data" / "image_manifest.json"
OUT = SITE / "asset_inventory.json"

# Upstream URLs for images grabbed outside download_images.py (the two
# service hero images fetched while fixing the service cards).
EXTRA = {
    "static/images/pages/pme-hero-image-generic.jpg":
        "https://www.usps.com/assets/images/ship/mail-ship/pme-hero-image-generic.jpg",
    "static/images/pages/shipping-for-biz.jpg":
        "https://www.usps.com/assets/images/ship/ground-adv/shipping-for-biz.jpg",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    seen = set()
    for entry in manifest:
        rel = entry["path"]
        if rel in seen:
            continue
        path = SITE / rel
        if not path.is_file():
            print(f"[inventory] missing file: {rel}", file=sys.stderr)
            continue
        seen.add(rel)
        rows.append({"path": rel, "bytes": path.stat().st_size,
                     "sha256": sha256(path),
                     "source_url": entry["url"]})
    for rel, url in EXTRA.items():
        if rel in seen:
            continue
        path = SITE / rel
        if path.is_file():
            rows.append({"path": rel, "bytes": path.stat().st_size,
                         "sha256": sha256(path), "source_url": url})
            seen.add(rel)

    # managed roots must be covered exactly: catch anything on disk that the
    # manifest missed
    for root in ("static/images", "static/external_cache"):
        base = SITE / root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.name == ".gitkeep":
                continue
            rel = str(path.relative_to(SITE))
            if rel not in seen:
                print(f"[inventory] untracked file on disk: {rel}",
                      file=sys.stderr)
                sys.exit(1)

    rows.sort(key=lambda r: r["path"])
    OUT.write_text(json.dumps({
        "schema_version": 1,
        "site": "usps",
        "asset_count": len(rows),
        "assets": rows,
    }, indent=1) + "\n", encoding="utf-8")
    print(f"[inventory] wrote {OUT.name}: {len(rows)} assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
