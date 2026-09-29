#!/usr/bin/env python3
"""verify_lib.py — deterministic verifier utilities for usps task
verification.

Philosophy: DETERMINISTIC FIRST. No LLM call is load-bearing; every check is
regex / token / SQLite after-state.

  1. Package identity (fail-closed): task_id matches, ``terminated`` with
     ``agent_done``, non-empty final answer, every recorded URL on the same
     loopback origin AND port as ``start_url``, every referenced screenshot a
     decodable PNG.
  2. Seed identity gate (fail-closed): the initial DB snapshot must BE the
     frozen in-image seed (schema + rows digest + counts). A run graded
     against a pre-mutated database fails here.
  3. Navigation gates (anti knowledge-shortcut): the agent MUST have opened
     the on-site surfaces the task names (postage calculators, tracking,
     Click-N-Ship, pickup scheduler, locations directory, PO Box page, the
     Postal Store, Hold Mail / Change of Address, country listings, claims,
     newsroom, account pages). A correct answer with no matching navigation
     is a memory-recall shortcut = FAIL.
  4. Answer check: affirmative token / phrase / number / money matching
     against ground truth HARDCODED in each ``verify_<n>.py`` (never in
     tasks.jsonl).
  5. DB after-state: read-only tasks require every table row-identical to
     the seed; stateful tasks require the exact allowed row delta and
     nothing else.

Seed reproducibility: the usps seed is rebuilt deterministically inside the
pinned image (PYTHONHASHSEED=0). The reviewer's independent image builds
(webharbor-review:usps from contribution 177b5d26, and webharbor-r2review:usps
from fix commit 77ef7ba8) both reproduce seed md5
af00d6d452e0fdddcf2197357ad9f3b2 (sha256 3d65c1041f03099d1824d73a1f187d33
36502a0eb603301d3e6a498ad6f752bd) — byte-identical to the contributor's dev
container; the r2 fix leaves the seed untouched (the frozen seed identity
gate below is re-verified, not re-frozen: counts/schema-sha/rows-sha are
unchanged) and every reviewer reset produced a byte-identical instance
database. The contract freezes the logical digests (schema + rows + counts)
computed with the exact functions below.

AS-SHIPPED CAVEAT (resolved in r2): r1 found the contribution enabled
CSRFProtect but rendered no ``csrf_token`` input in any of its 19 POST
forms, so every submission failed with "Bad Request — The CSRF token is
missing" in a real browser; the r1 live fixtures were exercised through a
CSRF-disabled review instance of the same tree. The fix commit (77ef7ba8)
embeds ``{{ csrf_token() }}`` in all 19 forms, and the r2 re-review
re-verified every form chain in a real Chromium with CSRF enabled
(18/18 no-token POSTs fail closed with 400; forged cross-session tokens
fail closed). These r2 fixtures are transcribed from real CSRF-enabled
browser walkthroughs of the fixed tree.

Input signature (per task):
  --run_dir DIR        agent trajectory dir: trajectory.json + screenshots/step_NNN.png
  --initial_db PATH    initial-state SQLite DB (default: <run_dir>/initial.db)
  --after_db PATH      after-state  SQLite DB (default: <run_dir>/after.db)
Output: JSON {task_id, pass, reason, evidence[]} to stdout; exit 0 on PASS, 1 on FAIL.
"""
import hashlib
import ipaddress
import json
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

SITE = "usps"
DEFAULT_CONTAINER = os.environ.get("WH_CONTAINER", "wh-usps-review")

# ---------------------------------------------------------------- frozen seed contract
TABLES = ("cart_items", "change_of_address", "claims", "content_pages",
          "country_info", "extra_services", "flat_rate_items",
          "hold_mail_requests", "informed_mail", "news_articles",
          "pickup_requests", "po_box_fees", "po_box_rentals", "post_offices",
          "postmasters", "rates", "saved_tracking", "scan_events",
          "service_infos", "shipments", "store_orders", "store_products",
          "users")
SEED_COUNTS = {"cart_items": 0, "change_of_address": 1, "claims": 1,
               "content_pages": 43, "country_info": 49, "extra_services": 112,
               "flat_rate_items": 58, "hold_mail_requests": 1,
               "informed_mail": 11, "news_articles": 18,
               "pickup_requests": 1, "po_box_fees": 48,
               "po_box_rentals": 1, "post_offices": 6282,
               "postmasters": 206, "rates": 4912, "saved_tracking": 2,
               "scan_events": 62, "service_infos": 8, "shipments": 10,
               "store_orders": 3, "store_products": 44, "users": 4}
# sha256 over sqlite_master (type, name, tbl_name, sql) of instance_seed/usps.db
# — frozen from the reviewer's independent image build.
SCHEMA_SHA256 = "40e0ed50aaa7c36647aaaf1a04f200f8b2e2fc56be894370ed8d0b7fb2c41a40"
# sha256 over every seed row (table-canonical, ORDER BY all columns).
SEED_ROWS_SHA256 = "dc50a7490ca36e1af857270afb9831ff9ced38feda9bb2933a3a2965b45ad7b5"
DEMO_PASSWORD = "TestPass123!"
NUM_TOKEN_RX = r"[0-9,.]+"


# ---------------------------------------------------------------- trajectory
def load_run(run_dir):
    d = Path(run_dir)
    traj = json.loads((d / "trajectory.json").read_text(encoding="utf-8"))
    if not isinstance(traj, dict):
        raise ValueError("trajectory.json must contain a JSON object")
    traj["_run_dir"] = d
    shots_dir = d / "screenshots"
    traj["_shots"] = {p.name: p for p in sorted(shots_dir.glob("step_*.png"))} if shots_dir.is_dir() else {}
    return traj


def trajectory_urls(traj):
    urls = []
    if traj.get("start_url"):
        urls.append(str(traj["start_url"]))
    for step in traj.get("steps", []):
        for key in ("url", "url_after"):
            if step.get(key):
                urls.append(str(step[key]))
    return urls


def final_answer(traj):
    answer = traj.get("final_answer")
    return "" if answer is None else str(answer)


def _png_ok(path: Path) -> bool:
    try:
        data = path.read_bytes()[:8]
    except OSError:
        return False
    return data == b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------- judge
@dataclass
class Judge:
    task_id: str
    evidence: list = field(default_factory=list)
    failures: list = field(default_factory=list)

    def ok(self, check, note):
        self.evidence.append(f"PASS {check}: {note}")

    def fail(self, check, note):
        self.failures.append(f"FAIL {check}: {note}")
        self.evidence.append(f"FAIL {check}: {note}")


def _is_loopback(hostname) -> bool:
    if not hostname:
        return False
    if hostname == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def check_trajectory_identity(judge, traj, task_id):
    if traj.get("task_id") != task_id:
        judge.fail("task_id", f"expected {task_id!r}, got {traj.get('task_id')!r}")
    else:
        judge.ok("task_id", traj.get("task_id"))
    if not traj.get("terminated") or traj.get("termination_reason") != "agent_done":
        judge.fail("terminated", "trajectory must be terminated with agent_done")
    else:
        judge.ok("terminated", "agent_done")
    if not final_answer(traj).strip():
        judge.fail("final_answer", "empty final answer")
    else:
        judge.ok("final_answer", f"{len(final_answer(traj))} chars")
    start = urlparse(str(traj.get("start_url", "")))
    if not _is_loopback(start.hostname):
        judge.fail("start_url_loopback", f"start_url not loopback: {start}")
    else:
        judge.ok("start_url_loopback", f"{start.hostname}:{start.port}")
    bad = []
    for url in trajectory_urls(traj):
        u = urlparse(url)
        if not _is_loopback(u.hostname) or u.port != start.port:
            bad.append(url)
    if bad:
        judge.fail("urls_same_origin", f"{len(bad)} off-site/other-port URLs: {bad[:3]}")
    else:
        judge.ok("urls_same_origin", f"{len(trajectory_urls(traj))} URLs on {start.netloc}")


def check_screenshots(judge, traj):
    shots = traj.get("_shots", {})
    referenced = set()
    for step in traj.get("steps", []):
        for key in ("screenshot_before", "screenshot_after"):
            if step.get(key):
                referenced.add(step[key])
    if not referenced:
        judge.fail("screenshots_present", "no screenshots referenced")
        return
    bad = [name for name in sorted(referenced)
           if name not in shots or not _png_ok(shots[name])]
    if bad:
        judge.fail("screenshots_decode", f"undecodable/missing: {bad[:3]}")
    else:
        judge.ok("screenshots_decode", f"{len(referenced)} PNGs decode")


def check_visited_path(judge, traj, check, pattern):
    rx = re.compile(pattern, re.IGNORECASE)
    urls = trajectory_urls(traj)
    hit = [u for u in urls if rx.search(u)]
    if not hit:
        judge.fail(check, f"no visited URL matches {pattern!r}")
    else:
        judge.ok(check, hit[0])


def check_visited_any(judge, traj, check, patterns):
    for pattern in patterns:
        rx = re.compile(pattern, re.IGNORECASE)
        if any(rx.search(u) for u in trajectory_urls(traj)):
            judge.ok(check, pattern)
            return
    judge.fail(check, f"no visited URL matches any of {patterns!r}")


# ---------------------------------------------------------------- answers
def _norm(text):
    return re.sub(r"\s+", " ", str(text)).lower()


def check_answer_phrase(judge, answer, check, phrase):
    if _norm(phrase) in _norm(answer):
        judge.ok(check, repr(phrase))
    else:
        judge.fail(check, f"answer lacks {phrase!r}")


def check_answer_any(judge, answer, check, phrases):
    for phrase in phrases:
        if _norm(phrase) in _norm(answer):
            judge.ok(check, repr(phrase))
            return
    judge.fail(check, f"answer lacks all of {phrases!r}")


def check_answer_number(judge, answer, check, number):
    want = str(number)
    tokens = re.findall(NUM_TOKEN_RX, answer)
    if any(t.replace(",", "").rstrip(".").lstrip("$") == want for t in tokens):
        judge.ok(check, want)
    else:
        judge.fail(check, f"number {want} not in answer tokens")


def check_answer_money(judge, answer, check, amount):
    """STRICT dollar check for the usps price domain ($0.65 .. $146.20):
    the answer must carry the exact two-decimal form (optionally with a
    leading $), e.g. $1.40 / 1.40. Bare-integer fallbacks are NOT accepted
    (a lone '1' in '1 ounce' must never satisfy a $1.40 check)."""
    want = float(amount)
    pat = rf"(?<![\\d.,])(?:\\$)?{re.escape(f'{want:.2f}')}(?![\\d])"
    if re.search(pat, answer):
        judge.ok(check, f"${want:.2f}")
    else:
        judge.fail(check, f"amount ${want:.2f} not in answer")


def check_attributed_money(judge, answer, check, label, amount):
    """Amount must appear within 60 chars AFTER its service label —
    catches value swaps between services (e.g. Ground Advantage priced
    at Priority Mail's $19.70)."""
    want = float(amount)
    pat = (rf"{re.escape(label)}[^\\d]{{0,60}}?"
           rf"(?<![\\d.,])(?:\\$)?{re.escape(f'{want:.2f}')}(?![\\d])")
    if re.search(pat, answer, re.IGNORECASE):
        judge.ok(check, f"{label} ${want:.2f}")
    else:
        judge.fail(check, f"{label} not attributed ${want:.2f}")


def check_section_phrase(judge, answer, check, marker, phrase,
                         must_not_appear_before=False):
    """Phrase must appear in the answer segment starting at the LAST-ish
    marker occurrence. With must_not_appear_before=True the phrase must NOT
    appear before the marker (catches cross-section swaps, e.g. 007's
    'Arriving Late' status leaked into 003's section)."""
    m = re.search(re.escape(marker), answer)
    if not m:
        judge.fail(check, f"marker {marker!r} not in answer")
        return
    seg = answer[m.start():]
    if _norm(phrase) in _norm(seg):
        if must_not_appear_before and _norm(phrase) in _norm(answer[:m.start()]):
            judge.fail(check, f"{phrase!r} appears before {marker!r} (swap)")
        else:
            judge.ok(check, repr(phrase))
    else:
        judge.fail(check, f"segment after {marker!r} lacks {phrase!r}")


def check_answer_count_at_least(judge, answer, check, options, minimum):
    found = sum(1 for o in options if _norm(o) in _norm(answer))
    if found >= minimum:
        judge.ok(check, f"{found}/{len(options)} item(s)")
    else:
        judge.fail(check, f"only {found}/{minimum} of {options!r} in answer")


def check_answer_absent(judge, answer, check, phrase):
    if _norm(phrase) in _norm(answer):
        judge.fail(check, f"answer must not contain {phrase!r}")
    else:
        judge.ok(check, f"absent: {phrase!r}")


def check_answer_regex(judge, answer, check, pattern):
    if re.search(pattern, answer, re.IGNORECASE):
        judge.ok(check, f"matches {pattern!r}")
    else:
        judge.fail(check, f"answer does not match {pattern!r}")


# ---------------------------------------------------------------- DB after-state
def _connect(path, container):
    p = Path(path)
    if not p.is_file() and container:
        inner = (f"/opt/WebSyn/{SITE}/instance/{SITE}.db"
                 if "after" in p.name else
                 f"/opt/WebSyn/{SITE}/instance_seed/{SITE}.db")
        subprocess.run(["docker", "cp", f"{container}:{inner}", str(p)],
                       check=True, capture_output=True)
    if not p.is_file():
        raise FileNotFoundError(f"database not found: {p}")
    return sqlite3.connect(f"file:{p}?mode=ro", uri=True)


def _table_rows(db, table):
    cols = [r[1] for r in db.execute(f'PRAGMA table_info("{table}")')]
    if not cols:
        return {}
    order = ", ".join(f'"{c}"' for c in cols)
    return {row[0]: list(row) for row in db.execute(f'SELECT * FROM "{table}" ORDER BY {order}')}


def _diff(initial, after, table):
    a = _table_rows(initial, table)
    b = _table_rows(after, table)
    added = [b[k] for k in b if k not in a]
    removed = [a[k] for k in a if k not in b]
    changed = [(a[k], b[k]) for k in a if k in b and a[k] != b[k]]
    return added, removed, changed


def check_read_only(judge, initial_db, after_db):
    """Every table must be row-identical to the seed snapshot."""
    bad = []
    for table in TABLES:
        added, removed, changed = _diff(initial_db, after_db, table)
        if added or removed or changed:
            bad.append(f"{table}(+{len(added)}/-{len(removed)}/~{len(changed)})")
    if bad:
        judge.fail("db_read_only", f"unexpected deltas: {bad}")
    else:
        judge.ok("db_read_only", f"all {len(TABLES)} tables row-identical to seed")


def check_only_tables_changed(judge, initial_db, after_db, allowed):
    bad = []
    for table in TABLES:
        added, removed, changed = _diff(initial_db, after_db, table)
        if (added or removed or changed) and table not in allowed:
            bad.append(table)
    if bad:
        judge.fail("db_tables_changed", f"unexpected writes: {bad}")
    else:
        judge.ok("db_tables_changed", f"only {sorted(allowed)} changed")


def _match(row, template):
    """Row matches template; None in a template slot is a wildcard; a leading
    'rx:' value is a regex on str(field); a set value accepts any member."""
    if len(row) != len(template):
        return False
    for got, want in zip(row, template):
        if want is None:
            continue
        if isinstance(want, (set, frozenset, list)) and not (
                isinstance(want, str) and want.startswith("rx:")):
            if got not in want:
                return False
        elif isinstance(want, str) and want.startswith("rx:"):
            if not re.search(want[3:], str(got)):
                return False
        elif got != want:
            return False
    return True


def check_rows_added(judge, initial_db, after_db, table, templates, check):
    added, _, _ = _diff(initial_db, after_db, table)
    if len(added) != len(templates):
        judge.fail(check, f"expected {len(templates)} added row(s) in {table}, got {len(added)}: {added}")
        return
    for tpl in templates:
        if not any(_match(row, tpl) for row in added):
            judge.fail(check, f"no added row in {table} matches {tpl}")
            return
    judge.ok(check, f"{len(templates)} row(s) added to {table}")


def check_rows_changed(judge, initial_db, after_db, table, templates, check):
    _, _, changed = _diff(initial_db, after_db, table)
    if len(changed) != len(templates):
        judge.fail(check, f"expected {len(templates)} changed row(s) in {table}, got {len(changed)}")
        return
    for tpl in templates:
        if not any(_match(new, tpl) for _, new in changed):
            judge.fail(check, f"no changed row in {table} matches {tpl}")
            return
    judge.ok(check, f"{len(templates)} row(s) changed in {table}")


# ---------------------------------------------------------------- seed contract
def check_seed_contract(judge, seed_db):
    counts = {t: seed_db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in TABLES}
    if counts != SEED_COUNTS:
        judge.fail("seed_counts", f"counts differ: {counts}")
    else:
        judge.ok("seed_counts", f"{sum(counts.values())} rows across {len(TABLES)} tables")
    schema_rows = list(seed_db.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"))
    digest = hashlib.sha256(json.dumps(schema_rows, default=str).encode()).hexdigest()
    if digest != SCHEMA_SHA256:
        judge.fail("seed_schema", f"schema digest {digest}")
    else:
        judge.ok("seed_schema", digest[:16])
    rows_src = []
    for t in TABLES:
        cols = [r[1] for r in seed_db.execute(f'PRAGMA table_info("{t}")')]
        order = ", ".join(f'"{c}"' for c in cols)
        for row in seed_db.execute(f'SELECT * FROM "{t}" ORDER BY {order}'):
            rows_src.append([t, list(row)])
    rdigest = hashlib.sha256(json.dumps(rows_src, default=str).encode()).hexdigest()
    if rdigest != SEED_ROWS_SHA256:
        judge.fail("seed_rows", f"rows digest {rdigest}")
    else:
        judge.ok("seed_rows", rdigest[:16])


# ---------------------------------------------------------------- runner
def run_verifier(task_id, run_checks):
    from argparse import ArgumentParser
    parser = ArgumentParser(description=f"Deterministic verifier for {task_id}")
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--initial_db", default=None)
    parser.add_argument("--after_db", default=None)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    traj = load_run(run_dir)
    initial = _connect(args.initial_db or run_dir / "initial.db", args.container)
    after = _connect(args.after_db or run_dir / "after.db", args.container)

    judge = Judge(task_id=task_id)
    run_checks(judge, traj, initial, after)

    passed = not judge.failures
    reason = ("all deterministic checks passed" if passed
              else "; ".join(judge.failures[:6]))
    print(json.dumps({
        "task_id": task_id,
        "pass": passed,
        "reason": reason,
        "evidence": judge.evidence,
    }, indent=1))
    return 0 if passed else 1
