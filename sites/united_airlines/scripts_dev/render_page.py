#!/usr/bin/env python3
"""Render a wayback replay of a united.com page and dump text + image URLs.

Used to study the upstream layout and to enumerate the real image CDN paths
for the asset harvest. Run with python3.11 (playwright is only installed for
3.11 on this host):  python3.11 scripts_dev/render_page.py <url> <out>
"""
import json
import sys
import time

from playwright.sync_api import sync_playwright

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')


def main() -> None:
    url, out = sys.argv[1], sys.argv[2]
    wait_ms = int(sys.argv[3]) if len(sys.argv) > 3 else 12000
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 900},
                                user_agent=UA)
        page.goto(url, timeout=90000)
        time.sleep(wait_ms / 1000)
        text = page.inner_text('body')
        images = page.eval_on_selector_all(
            'img', "els => els.map(e => ({src: e.currentSrc || e.src, alt: e.alt}))")
        links = page.eval_on_selector_all(
            'a', "els => els.map(e => ({href: e.href, text: (e.innerText||'').trim()}))")
        bg = page.evaluate("""
            () => {
              const urls = [];
              for (const sheet of document.styleSheets) {
                try {
                  for (const rule of sheet.cssRules) {
                    const m = (rule.style && rule.style.backgroundImage || '').match(/url\\(["']?([^"')]+)["']?\\)/);
                    if (m) urls.push(m[1]);
                  }
                } catch (e) {}
              }
              return urls;
            }""")
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump({'url': url, 'text': text, 'images': images,
                       'links': links, 'css_bg': bg}, fh, indent=1)
        browser.close()
    print('saved', out)


if __name__ == '__main__':
    main()
