#!/usr/bin/env python3
"""Harvest real united.com data through web.archive.org replays.

Everything fetched here is persisted under scraped_data/ so the harvest is
incremental (re-runs skip files that already exist) and byte-identical.

Rate limits: the Internet Archive throttles hard. This script therefore
  - always sleeps between requests,
  - caches every response on disk (never re-fetches an existing file),
  - retries on transient 'Temporarily Offline' pages with backoff.
"""
from __future__ import annotations

import gzip
import hashlib
import urllib.error
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
SCRAPED = SITE / 'scraped_data'
SCRAPED.mkdir(parents=True, exist_ok=True)

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
REQUEST_SLEEP = float(os.environ.get('UA_HARVEST_SLEEP', '4'))
MAX_ATTEMPTS = 6


def _fetch(url: str, timeout: int = 90) -> bytes:
    last_error = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            if data[:2] == b'\x1f\x8b':          # gzip payload (origin sent it compressed)
                data = gzip.decompress(data)
            return data
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 400, 410):
                raise RuntimeError(f'no capture: {url} (HTTP {exc.code})') from exc
            last_error = exc
            wait = 20 * (attempt + 1)
            print(f'  [retry {attempt + 1}] {exc} — sleeping {wait}s', flush=True)
            time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait = 20 * (attempt + 1)
            print(f'  [retry {attempt + 1}] {exc} — sleeping {wait}s', flush=True)
            time.sleep(wait)
    raise RuntimeError(f'fetch failed after {MAX_ATTEMPTS} attempts: {url} ({last_error})')


def replay(upstream_url: str, stamp: str = '2026') -> tuple[bytes, str]:
    """Fetch the latest <=stamp wayback replay of upstream_url."""
    quoted = urllib.parse.quote(upstream_url, safe=':/?&=%')
    fetch_url = f'https://web.archive.org/web/{stamp}id_/{quoted}'
    data = _fetch(fetch_url)
    return data, fetch_url


def harvest(name: str, upstream_url: str, stamp: str = '2026') -> bytes | None:
    """Persist a replay body to scraped_data/<name>; return None if cached."""
    target = SCRAPED / name
    meta_path = SCRAPED / (name + '.meta.json')
    if target.exists() and meta_path.exists():
        return None
    try:
        data, fetch_url = replay(upstream_url, stamp)
    except RuntimeError as exc:
        print(f'  [skip] {name}: {exc}', flush=True)
        return None
    # Wayback error payloads are HTML; APIs return JSON. Do not keep
    # 'Temporarily Offline' or 404-style pages.
    head = data[:120].lstrip().lower()
    if head.startswith(b'<!doctype html') or head.startswith(b'<html'):
        if name.endswith('.json'):
            print(f'  [skip-html] {name} (got HTML for {upstream_url})', flush=True)
            return None
    target.write_bytes(data)
    meta_path.write_text(json.dumps({
        'upstream_url': upstream_url,
        'fetch_url': fetch_url,
        'sha256': hashlib.sha256(data).hexdigest(),
        'bytes': len(data),
    }, indent=1))
    time.sleep(REQUEST_SLEEP)
    return data


def load(name: str) -> bytes:
    return (SCRAPED / name).read_bytes()


def load_json(name: str):
    return json.loads(load(name))
