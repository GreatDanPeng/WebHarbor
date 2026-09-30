#!/usr/bin/env python3
"""Build asset_inventory.json for the u_s_customs mirror (schema_version 1).

Covers every managed runtime asset (static/images/** and
static/external_cache/**) with path, bytes, sha256 and the exact upstream
https URL the file was fetched from. scripts/check_asset_inventory.py
re-verifies this at image build time: any placeholder, duplicate,
non-image or missing-source file fails the build.

Run: python3.11 build_asset_inventory.py
"""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
manifest_path = ROOT / "scraped_data" / "image_manifest.json"
image_manifest = json.load(open(manifest_path)) if manifest_path.exists() else []
by_file = {m["file"]: m for m in image_manifest}

# form PDF source URLs come from the tracked forms catalog
forms = json.loads((ROOT / "source_data" / "forms.json").read_text())
pdf_urls = {f["file"]: f["pdf_url"] for f in forms if f.get("file")}

# chrome assets (seal, flag, search icon) are the upstream theme files,
# fetched from the same URLs the site chrome renders.
CHROME_SOURCES = {
    "static/images/chrome/CBPwSealwhite_225x69.png":
        "https://www.cbp.gov/profiles/cbpd8_gov/themes/custom/"
        "cbpd8_gov_theme/CBPwSealwhite_225x69.png",
    "static/images/chrome/search.svg":
        "https://www.cbp.gov/profiles/cbpd8_gov/themes/custom/"
        "cbpd8_gov_theme/assets/img/search.svg",
    "static/images/chrome/us_flag_small.png":
        "https://www.cbp.gov/profiles/cbpd8_gov/themes/custom/"
        "cbpd8_gov_theme/assets/img/us_flag_small.png",
}
pdf_urls.update(CHROME_SOURCES)

assets = []
for root in ("static/images", "static/external_cache"):
    base = ROOT / root
    if not base.exists():
        continue
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        data = path.read_bytes()
        rel = str(path.relative_to(ROOT))
        meta = by_file.get(rel, {})
        source = meta.get("url") or pdf_urls.get(rel, "")
        if not source:
            raise SystemExit(f"no upstream source URL recorded for {rel}")
        assets.append({
            "path": rel,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_url": source,
        })

seen_hashes = {}
for a in assets:
    seen_hashes.setdefault(a["sha256"], []).append(a["path"])
dupes = {k: v for k, v in seen_hashes.items() if len(v) > 1}
if dupes:
    for k, v in dupes.items():
        print(f"  DUPLICATE content {k[:12]}: {v}")
    raise SystemExit("duplicate asset content is a build failure")

(ROOT / "asset_inventory.json").write_text(json.dumps({
    "schema_version": 1,
    "site": "u_s_customs",
    "asset_count": len(assets),
    "assets": assets,
}, indent=1))
print(f"[inventory] {len(assets)} managed assets inventoried")
