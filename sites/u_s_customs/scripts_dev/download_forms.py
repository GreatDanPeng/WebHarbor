#!/usr/bin/env python3
"""Phase 9: download the CBP form PDFs from the forms catalog.

Every PDF listed on https://www.cbp.gov/newsroom/publications/forms is
fetched from its upstream URL — through an in-page fetch executed by a real
headless Chromium on a cbp.gov page, because the CDN blocks plain HTTP
clients — into static/external_cache/forms/ with a sha256 manifest at
scraped_data/form_files.json.

Run: python3.11 download_forms.py
"""
import base64
import hashlib
import json
import pathlib
import re
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "static" / "external_cache" / "forms"
PDF_DIR.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CBP = "https://www.cbp.gov"

FETCH_JS = """async (url) => {
    const r = await fetch(url);
    const buf = await r.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let bin = '';
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
        bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return {status: r.status, b64: btoa(bin), len: bytes.length};
}"""


def main():
    forms = json.load(open(ROOT / "scraped_data" / "forms" / "forms.json"))
    manifest = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=UA)
        page = ctx.new_page()
        page.goto(CBP + "/newsroom/publications/forms",
                  wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2000)
        for f in forms:
            url = f.get("pdf")
            if not url:
                continue
            if url.startswith("/"):
                url = CBP + url
            tail = url.split("?")[0].rstrip("/").split("/")[-1]
            tail = re.sub(r"%[0-9A-Fa-f]{2}", "_", tail)
            name = re.sub(r"[^A-Za-z0-9._-]", "_", tail)
            if not name.lower().endswith(".pdf"):
                name += ".pdf"
            path = PDF_DIR / name
            if path.exists():
                data = path.read_bytes()
            else:
                data = None
                for attempt in range(3):
                    try:
                        res = page.evaluate(FETCH_JS, url)
                        if res and res.get("status") == 200:
                            data = base64.b64decode(res["b64"])
                            if not data.startswith(b"%PDF"):
                                data = None
                            break
                        print(f"[{res.get('status') if res else '?'}] {url[-60:]}")
                    except Exception as ex:
                        print(f"[retry {attempt}] {str(ex)[:60]}")
                    time.sleep(2 + attempt * 3)
                if not data:
                    print(f"[FAIL] {url}")
                    continue
                path.write_bytes(data)
                time.sleep(0.3)
            sha = hashlib.sha256(data).hexdigest()
            manifest.append({"form_number": f.get("form_number"),
                             "file": f"static/external_cache/forms/{name}",
                             "url": url, "sha256": sha, "bytes": len(data)})
        browser.close()
    (ROOT / "scraped_data" / "form_files.json").write_text(
        json.dumps(manifest, indent=1))
    print(f"[forms] {len(manifest)} PDFs on disk")


if __name__ == "__main__":
    main()
