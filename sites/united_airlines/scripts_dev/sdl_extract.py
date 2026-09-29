#!/usr/bin/env python3
"""Turn the harvested united.com SDL CMS payloads into clean page copy.

The upstream CMS (api/sdl/getmodelservicepage) returns 'Atmos' content
models: text passages with embedded HTML bodies, tables, grids of link
cards and accordions. This module converts any of those payloads into an
ordered list of plain blocks:

    {"kind": "heading"|"para"|"list"|"table"|"cards"|"accordion",
     "text": str, "items": [...], "head": [...], "rows": [[...]]}

used by build_source_data.py to freeze source_data_content.json.
"""
from __future__ import annotations

import html
import re

TAG_RE = re.compile(r'<[^>]+>')


def _clean(fragment: str) -> str:
    text = fragment or ''
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'</p>\s*<p>', '\n\n', text)
    text = re.sub(r'</li>\s*<li>', '\n', text)
    text = TAG_RE.sub(' ', text)
    text = html.unescape(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' ?\n ?', '\n', text)
    return text.strip()


def _props(content: dict) -> dict:
    out = {}
    for container in ('properties', 'properties_nt'):
        for prop in content.get(container) or []:
            pair = prop.get('content') or {}
            key, value = pair.get('key'), pair.get('value')
            if key and value:
                out[key] = value
    return out


def _parse_table_html(fragment: str) -> dict | None:
    m = re.search(r'<table[^>]*>(.*?)</table>', fragment, flags=re.S)
    if not m:
        return None
    inner = m.group(1)
    head, rows = [], []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', inner, flags=re.S):
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', tr, flags=re.S)
        cells = [re.sub(r'<div[^>]*>', '\n', c) for c in cells]
        cells = [_clean(c) for c in cells]
        if not cells:
            continue
        if not rows and '<th' in tr:
            head = cells if not head else head
            if all('<th' in tr for _ in [0]) and not rows:
                head = cells
            rows.append(cells)
            continue
        rows.append(cells)
    if not rows:
        return None
    return {'kind': 'table', 'head': head, 'rows': rows}


def _blocks_from_body(body: str, title_tag: str = 'h2') -> list[dict]:
    """Split an HTML body fragment into heading / paragraph / list / table
    blocks."""
    blocks = []
    body = body or ''
    # pull embedded tables out first so they keep their order
    pieces = re.split(r'(<table[^>]*>.*?</table>)', body, flags=re.S)
    for piece in pieces:
        if not piece:
            continue
        if piece.startswith('<table'):
            table = _parse_table_html(piece)
            if table:
                blocks.append(table)
            continue
        for chunk in re.split(r'(<h[1-4][^>]*>.*?</h[1-4]>)', piece, flags=re.S):
            if not chunk:
                continue
            m = re.match(r'<h([1-4])[^>]*>(.*?)</h\1>', chunk, flags=re.S)
            if m:
                level = min(int(m.group(1)), 4)
                blocks.append({'kind': 'heading', 'level': level,
                               'text': _clean(m.group(2))})
            else:
                text = _clean(chunk)
                if not text:
                    continue
                if '\n' in text and re.match(r'^([A-Za-z0-9®™() \-,\']{2,60}\n){2,}$', text):
                    blocks.append({'kind': 'list',
                                   'items': [line.strip() for line in
                                             text.split('\n') if line.strip()]})
                else:
                    blocks.append({'kind': 'para', 'text': text})
    return blocks


def _table_from(content: dict) -> dict | None:
    tables = content.get('tables') or content.get('table')
    if isinstance(tables, dict):
        tables = [tables]
    if not tables:
        return None
    table = tables[0]
    head = []
    for cell in (table.get('head') or {}).get('row', []) if isinstance(table.get('head'), dict) else []:
        head.append(_clean(cell.get('cell', '')) if isinstance(cell, dict) else _clean(str(cell)))
    rows = []
    for row in table.get('rows', []) or []:
        if isinstance(row, dict):
            row = row.get('row', [])
        cells = []
        for cell in row:
            if isinstance(cell, dict):
                cells.append(_clean(cell.get('cell', '')))
            else:
                cells.append(_clean(str(cell)))
        rows.append(cells)
    if not rows:
        return None
    return {'kind': 'table', 'head': head, 'rows': rows}


def extract_blocks(node, blocks: list) -> None:
    """Walk one SDL node (page or nested component) appending blocks."""
    if isinstance(node, dict):
        content = node.get('content')
        if not isinstance(content, dict):
            content = node
        view = (node.get('presentation') or {}).get('view')
        props = _props(content)
        title = props.get('title') or content.get('title')
        body = content.get('body')
        if view == 'AtmosTextPassage' or (body and not view):
            if title:
                blocks.append({'kind': 'heading',
                               'level': 2, 'text': _clean(title)})
            if body:
                blocks.extend(_blocks_from_body(body))
        elif view == 'AtmosAccordion' or 'components' in content:
            if title:
                blocks.append({'kind': 'heading', 'level': 2,
                               'text': _clean(title)})
            for comp in content.get('components') or []:
                inner = comp.get('content', {})
                if isinstance(inner, dict) and inner.get('component_type') \
                        and 'component' in inner:
                    inner = inner['component'].get('content', {})
                    if not isinstance(inner, dict):
                        inner = {}
                # accordion panel: title property + body + maybe a table
                panel_props = _props(inner)
                panel_title = panel_props.get('title')
                panel_body = inner.get('body') or ''
                if panel_title:
                    blocks.append({'kind': 'heading', 'level': 3,
                                   'text': _clean(panel_title)})
                table = _table_from(inner)
                if table:
                    blocks.append(table)
                if panel_body:
                    blocks.extend(_blocks_from_body(panel_body))
                # panels can nest further components
                extract_blocks({'content': inner}, blocks)
        elif view == 'AtmosGrid':
            for item in content.get('grid_items') or []:
                item_content = item.get('content') or {}
                for comp in item_content.get('components') or []:
                    inner = comp.get('content', {})
                    if isinstance(inner, dict) and inner.get('component_type') \
                            and 'component' in inner:
                        inner = inner['component'].get('content', {})
                        if not isinstance(inner, dict):
                            inner = {}
                    if not isinstance(inner, dict):
                        inner = {}
                    iprops = _props(inner)
                    icontent = inner.get('content') if isinstance(inner.get('content'), dict) else inner
                    card_title = iprops.get('title') or _clean(
                        (icontent.get('body') or ''))[:80]
                    link = iprops.get('link') or iprops.get('href')
                    if card_title:
                        blocks.append({'kind': 'card', 'title': _clean(card_title),
                                       'link': link or ''})
                    extract_blocks({'content': icontent}, blocks)
        else:
            table = _table_from(content)
            if table:
                blocks.append(table)
            if body:
                blocks.extend(_blocks_from_body(body))
            for key in ('content', 'components', 'grid_items'):
                child = content.get(key)
                if isinstance(child, (dict, list)):
                    extract_blocks(child if key != 'grid_items'
                                   else {'content': {'components': child}}, blocks)
    elif isinstance(node, list):
        for item in node:
            extract_blocks(item, blocks)


def page_blocks(payload: dict) -> list[dict]:
    blocks: list[dict] = []
    for block in payload.get('content', []):
        extract_blocks(block, blocks)
    # Collapse exact duplicate blocks produced by the double-walk.
    out, seen = [], set()
    for b in blocks:
        key = json_key(b)
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out


def json_key(block) -> str:
    import json
    return json.dumps(block, sort_keys=True, default=str)


def page_title(payload: dict) -> str:
    for block in payload.get('content', []):
        props = _props(block.get('content', {}))
        if props.get('title'):
            return _clean(props['title'])
        body = block.get('content', {}).get('body')
        if body:
            m = re.search(r'<h1[^>]*>(.*?)</h1>', body, flags=re.S)
            if m:
                return _clean(m.group(1))
    return ''
