#!/usr/bin/env python3
"""test_verifiers.py — adversarial contract tests for the usps verifier suite.

Guarantees (run with pytest):
  * each honest fixture (transcribed from the auditor's real Playwright
    walkthroughs of the audit container wh-usps-audit, seed sha256
    3d65c1041f03099d1824d73a1f187d3336502a0eb603301d3e6a498ad6f752bd) PASSES
    its verify_<n>.py;
  * every adversarial negative FAILS (no false positives):
      - no-op trajectories (21),
      - answer-only shortcuts with no navigation (per read-only task),
      - stateful shortcuts (correct answer, no wizard flow navigation),
      - wrong-answer trajectories (per task),
      - stale-DB trajectories (stateful tasks missing their writes),
      - read-only violations (unexpected DB writes on read-only tasks),
      - tampered packages (wrong task_id / off-site URL / cross-port /
        not-terminated / empty answer / bad PNG / pre-mutated seed),
      - task-specific confusions (T1 service-price swap, T3 status swap,
        T15 Japan price-group swap, T7 wrong confirmation);
      - audit-deepening negatives: every NEW question point (ordinal-57
        deepening) has a fabricated-value wrong-answer trajectory that
        must fail on the new anchor.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

VERIFY = Path(__file__).resolve().parent
EV = Path("/data/zhaoyang-user-projects/websyn/wh-usps-audit-evidence")
FIXTURES = EV / "runs"
TMP = EV / "verify_runs" / "_pytest_tmp"
PY = sys.executable

# audit deepening: T4 now also saves a tracking number (saved_tracking),
# so it moved from read-only to stateful.
READ_ONLY = [0, 1, 2, 3, 8, 9, 12, 15, 16, 18, 19, 20]
STATEFUL = [4, 5, 6, 7, 10, 11, 13, 14, 17]


def run_verifier(n: int, run_dir: Path):
    proc = subprocess.run(
        [PY, str(VERIFY / f"verify_{n}.py"), "--run_dir", str(run_dir)],
        capture_output=True, text=True, timeout=180)
    try:
        verdict = json.loads(proc.stdout)
    except json.JSONDecodeError:
        verdict = {"pass": False, "reason": proc.stdout[-300:] or proc.stderr[-300:]}
    return verdict


def clone(n: int, tag: str) -> Path:
    dst = TMP / f"{n}_{tag}"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(FIXTURES / f"task{n}", dst)
    return dst


def set_traj(run_dir: Path, **changes):
    p = run_dir / "trajectory.json"
    traj = json.loads(p.read_text())
    traj.update(changes)
    p.write_text(json.dumps(traj, indent=2))


def mutate_answer(run_dir: Path, new_answer: str):
    set_traj(run_dir, final_answer=new_answer)


def mutate_db(run_dir: Path, which: str, sql: str):
    db = sqlite3.connect(run_dir / which)
    db.execute(sql)
    db.commit()
    db.close()


def drop_nav(run_dir: Path):
    """Strip all step URLs down to the bare start page (no tool navigation)."""
    p = run_dir / "trajectory.json"
    traj = json.loads(p.read_text())
    start = traj["start_url"]
    for step in traj.get("steps", []):
        step["url"] = start
        step["url_after"] = start
    p.write_text(json.dumps(traj, indent=2))


# ---------------------------------------------------------------- happy path
@pytest.mark.parametrize("n", range(21))
def test_honest_fixture_passes(n):
    verdict = run_verifier(n, FIXTURES / f"task{n}")
    assert verdict["pass"], verdict["reason"]


# ---------------------------------------------------------------- no-op
@pytest.mark.parametrize("n", range(21))
def test_noop_fails(n):
    run_dir = clone(n, "noop")
    set_traj(run_dir, steps=[], final_answer="", terminated=False,
             termination_reason="max_steps")
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]


# ---------------------------------------------------------------- shortcuts
@pytest.mark.parametrize("n", READ_ONLY)
def test_answer_only_shortcut_fails(n):
    run_dir = clone(n, "shortcut")
    drop_nav(run_dir)
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]
    assert any("nav_" in e for e in verdict["evidence"] if e.startswith("FAIL"))


@pytest.mark.parametrize("n", STATEFUL)
def test_stateful_shortcut_fails(n):
    run_dir = clone(n, "shortcut")
    drop_nav(run_dir)
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]


# ---------------------------------------------------------------- wrong answers
WRONG = {
    0: "A 3-ounce letter costs $1.58, 2 ounces $1.29, metered 1 ounce $0.92, "
       "and a postcard $0.71; the 3-ounce letter costs $0.87 more than the "
       "postcard.",
    1: "For an 8-pound Zone 4 package: USPS Ground Advantage $19.70, Priority "
       "Mail $17.65, Priority Mail Express $92.55, Media Mail $8.13. "
       "Priority Mail is cheapest. Media Mail is allowed for candles. A "
       "2-pound box costs $12.10 by Priority Mail. The Priority Mail page "
       "lists its Flat Rate Envelope at $10.90 with $50 of insurance, and "
       "Ground Advantage delivers in 5-9 days.",
    2: "Priority Mail 30 lb Zone 8 costs $137.20; the Large Flat Rate Box is "
       "$30.75 and the Small is $12.10; Priority Mail by weight is cheaper. "
       "Media Mail at 70 pounds costs $49.99; its maximum weight is 60 lbs "
       "and video games qualify; the store charges $12.00 for the Medium "
       "Flat Rate Box.",
    3: "9405500000000000000003 is Delivered on October 3 with 6 events. "
       "9405500000000000000007 is In Transit, On Time with a Weather Delay "
       "exception. 9405500000000000000005 is Delivered and needs no "
       "signature; 9405500000000000000008 is Out for Delivery by Priority "
       "Mail. The glossary says In Transit means the item is at the local "
       "Post Office.",
    4: "The in-transit package is 9405500000000000000010, status Out for "
       "Delivery, expected October 2; the pickup is PKG-338275. I saved it "
       "as Candle restock. Informed Delivery shows 5 mailpieces; today's "
       "bill came from ComEd; 2 pieces are older than today from Cascade "
       "Freight. Bob's claim is Approved for $210.00 and his delivery "
       "arrived 2026-09-25 8:00 am.",
    5: "The Priority Mail base price was $16.10; the total paid was $28.90; "
       "the tracking number is 9405512345678901234567 and expected delivery "
       "is October 5, 2026.",
    6: "Ground Advantage showed $23.25 and Priority Mail $18.40; I chose "
       "Priority Mail and paid $23.25; tracking 9405599999999999999999.",
    7: "The pickup confirmation number is PKG-9999999 for October 15, 2026, "
       "at 45 Beacon St, Boston, MA 02111; the serving Post Office is "
       "Cambridge.",
    8: "The 90210 search lists 3 locations; Beverly Hills is at 450 N Roxbury "
       "Dr, hours 8:30 am - 5:30 pm, established 1914, postmaster Agnes "
       "Richmond, phone 555-1212, open Sundays. Its reservation page offers "
       "12-month periods only. The name search returns 5 results; the "
       "other one is in TX 73301, established 1850. ZIP 90230 is "
       "Hollywood, open 7:00 am - 3:00 pm.",
    9: "The DE kiosk search shows 35 locations; the first three are Bear DE "
       "19701, Bethany Beach DE 19930, Bethel DE 19931; Bear is open "
       "weekdays 8:00 am - 5:00 pm, Saturday Closed, lobby 9 hours; no PO "
       "Boxes. Bridgeville opens at 10:00 am. DE has 60 locations total "
       "and 25 with Po Box Rental.",
    10: "The 6-month fees are $80 for Size 1, $40 for Size 2 and $20 for Size "
        "5; Size 7 is $20 for 3 months and $30 for 6 months. Boston is "
        "open 8:00 am - 4:00 pm; I reserved box 1234 paying $40.00. The "
        "02138 office is Beacon Hill, open 10:00 am - 6:00 pm.",
    11: "The Breast Cancer Research sheet costs $13.20 with SKU 661304; the "
        "Diwali 2026 stamps cost $13.20 and the Flag 2026 sheet $12.00; the "
        "cart lines were $13.20, $26.40 and $12.00 with order total "
        "$51.60; the order number is 12345.",
    12: "The newest Christmas stamps are the Madonna and Child at $13.20; "
        "Breast Cancer Research costs $13.20 with SKU 661304; the most "
        "expensive is Barbie at $36.00; the Christmas Cookies SKU is "
        "680104; Diwali costs $12.00 and Hanukkah $14.00; All Stamps lists "
        "21 products and New Releases 15; the top collectible is the Stamp "
        "Yearbook at $99.00 SKU 992620, and Barbie is $9.00 SKU 582505.",
    13: "Carol's active hold is HLD-111111 from October 1 to October 5, pickup "
        "at the Post Office; her PO Box is 1234 until March 15, 2027. "
        "Today's Informed Delivery piece is from Cascade Freight, category "
        "Promotion. The Change of Address fee is $2.25. My new request was "
        "confirmed HLD-222222; USPS can hold mail for up to 45 days.",
    14: "The identity validation fee is $1.25; the Premium Forwarding "
        "Service reships mail monthly via Media Mail; my confirmation is "
        "XYZ-123 and the move type is Individual.",
    15: "Japan prohibits fresh fruit, live plants, and lottery tickets; "
        "customs form PS Form 2976-R is required; Japan's PMI price group "
        "is 3; the 4-lb prices are PMI $60.00 and PMEI $95.00; Germany is "
        "group 15 and Canada group 9.",
    16: "2 pounds to Canada: FCPIS $24.90, PMI $39.00; to Germany FCPIS "
        "$28.40 and PMI $64.00 at 2 lbs, and at 4 lbs PMI $74.00 and PMEI "
        "$104.00; Germany restricts only firearms and its PMI maximum is "
        "44 lbs; Canada is group 9 with a 33 lbs maximum.",
    17: "Claim number CLM-0000000 for $300.00; the Claim Status page shows "
        "Approved.",
    18: "A 1-pound Zone 4 package costs $10.50 by Priority Mail, $15.00 at "
        "Zone 8, and a 2-pound package $12.25. Insurance for $200.01-$300 "
        "is $6.05; Certified Mail is $4.65; Return Receipt is $5.15; "
        "Signature Confirmation is $4.35; Registered Mail $18.00; COD "
        "$19.99; the total is $17.20; claims are due within 30 days. The "
        "Priority Mail Flat Rate Envelope is $10.90 with $50 insurance and "
        "the Express envelope $30.00.",
    19: "The most recent release is about Winter Wreath stamps dated September "
        "18, 2026, type Media Advisory; the holiday release was published "
        "October 2, 2026 and recommends shipping by December 10. The "
        "Wreath image shows a holiday tree and the Diwali image a lamp "
        "from October 1. The newsroom lists 12 releases and Service "
        "Alerts lists 6, titled Storm Warnings, about flooding.",
    20: "Media Mail ships in 5-10 days, maximum 50 lbs, and allows video "
        "games; the Using Media Mail list names 6 categories; letters start "
        "at $0.90. The prohibited list has 11 items including Aerosols and "
        "Fresh Fruit; Media Mail at Zone 4 costs $4.99 for 1 lb, $6.50 for "
        "5 lbs, $15.00 for 20 lbs, $39.99 for 50 lbs and $60.00 for "
        "70 lbs.",
}


@pytest.mark.parametrize("n", range(21))
def test_wrong_answer_fails(n):
    run_dir = clone(n, "wrong")
    mutate_answer(run_dir, WRONG[n])
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]


# ---------------------------------------------------------------- stale DB / read-only violations
@pytest.mark.parametrize("n", STATEFUL)
def test_stale_db_fails(n):
    """Stateful task with NO DB change (agent never submitted the flow)."""
    run_dir = clone(n, "stale")
    shutil.copyfile(run_dir / "initial.db", run_dir / "after.db")
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]
    assert any("db_" in e or "cns_" in e or "_added" in e
               for e in verdict["evidence"] if e.startswith("FAIL"))


@pytest.mark.parametrize("n", [0, 3, 12, 19])
def test_read_only_violation_fails(n):
    """Read-only task whose DB acquired an unexpected write."""
    run_dir = clone(n, "dirty")
    mutate_db(run_dir, "after.db",
              "INSERT INTO users (email, username, display_name, "
              "password_hash, created_at) VALUES "
              "('sneaky@test.com','sneaky','Sneaky','x','2026-09-28')")
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]
    assert any("db_read_only" in e for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- tampered packages
def test_wrong_task_id_fails():
    run_dir = clone(0, "wrongid")
    set_traj(run_dir, task_id="USPS.com--1")
    verdict = run_verifier(0, run_dir)
    assert not verdict["pass"]
    assert any("task_id" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_offsite_url_fails():
    run_dir = clone(0, "offsite")
    traj = json.loads((run_dir / "trajectory.json").read_text())
    traj["steps"][0]["url"] = "https://www.usps.com/"
    (run_dir / "trajectory.json").write_text(json.dumps(traj))
    verdict = run_verifier(0, run_dir)
    assert not verdict["pass"]
    assert any("urls_same_origin" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_cross_port_url_fails():
    run_dir = clone(0, "crossport")
    traj = json.loads((run_dir / "trajectory.json").read_text())
    traj["steps"][0]["url"] = traj["start_url"].replace(":50110", ":51110")
    traj["steps"][0]["url_after"] = traj["steps"][0]["url"]
    (run_dir / "trajectory.json").write_text(json.dumps(traj))
    verdict = run_verifier(0, run_dir)
    assert not verdict["pass"]
    assert any("urls_same_origin" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_not_terminated_fails():
    run_dir = clone(1, "notterm")
    set_traj(run_dir, terminated=False, termination_reason="max_steps")
    verdict = run_verifier(1, run_dir)
    assert not verdict["pass"]
    assert any("terminated" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_empty_answer_fails():
    run_dir = clone(2, "emptyans")
    set_traj(run_dir, final_answer="")
    verdict = run_verifier(2, run_dir)
    assert not verdict["pass"]
    assert any("final_answer" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_bad_png_fails():
    run_dir = clone(3, "badpng")
    shot = run_dir / "screenshots" / "step_000.png"
    shot.write_bytes(b"not a png")
    verdict = run_verifier(3, run_dir)
    assert not verdict["pass"]
    assert any("screenshots" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_premutated_seed_fails():
    """Initial DB tampered before the run — seed identity gate must trip."""
    run_dir = clone(4, "dirtyseed")
    mutate_db(run_dir, "initial.db",
              "INSERT INTO users (email, username, display_name, "
              "password_hash, created_at) VALUES "
              "('pre@test.com','pre','Pre','x','2026-09-28')")
    verdict = run_verifier(4, run_dir)
    assert not verdict["pass"]
    assert any("seed_" in e for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- task-specific confusions
def test_t1_service_price_swap_fails():
    run_dir = clone(1, "swap")
    mutate_answer(run_dir, WRONG[1])
    verdict = run_verifier(1, run_dir)
    assert not verdict["pass"]
    assert any("ga_8lb_z4" in e or "pm_8lb_z4" in e
               for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t3_status_swap_fails():
    run_dir = clone(3, "swap")
    mutate_answer(
        run_dir,
        "9405500000000000000003: In Transit, Arriving Late, expected "
        "September 30, 2026, latest scan 'Processing Exception' at DENVER, "
        "CO 2026-09-26 12:00, 4 events. 9405500000000000000007: In Transit "
        "with the exception event 'In Transit to Next Facility' at Denver, "
        "CO on 2026-09-20 07:00.")
    verdict = run_verifier(3, run_dir)
    assert not verdict["pass"]
    assert any("t7_exception" in e or "t3_status" in e
               for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t15_wrong_price_group_fails():
    run_dir = clone(15, "group")
    mutate_answer(
        run_dir,
        "Japan prohibits ammunition, firearms, and hoverboards; the customs "
        "form is PS Form 2976-B in 2976-E; Japan's PMI price group is 3; "
        "the 4-pound prices are PMI $78.50 and PMEI $108.45.")
    verdict = run_verifier(15, run_dir)
    assert not verdict["pass"]
    assert any("pmi_group" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t7_wrong_confirmation_fails():
    run_dir = clone(7, "conf")
    mutate_answer(
        run_dir,
        "Pickup confirmation number PKG-338275, scheduled for September 30, "
        "2026 at 88 State St, Boston, MA 02110.")
    verdict = run_verifier(7, run_dir)
    assert not verdict["pass"]
    assert any("confirmation" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t10_wrong_box_number_fails():
    run_dir = clone(10, "box")
    mutate_answer(
        run_dir,
        "The 6-month market-dominant fees are $65.00 for Size 2 and $40.00 "
        "for Size 5. I reserved a Size 2 box for 6 months at the Boston Post "
        "Office and was assigned box number 1234, paying $65.00.")
    verdict = run_verifier(10, run_dir)
    assert not verdict["pass"]
    assert any("box_number" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t17_wrong_claim_status_fails():
    run_dir = clone(17, "status")
    mutate_answer(
        run_dir,
        "Damage claim filed for shipment 9405500000000000000004. Claim "
        "number CLM-D7D8EDA, claim amount $280.00. The Claim Status page "
        "shows the claim as Approved.")
    verdict = run_verifier(17, run_dir)
    assert not verdict["pass"]
    assert any("claim_status" in e for e in verdict["evidence"] if e.startswith("FAIL"))
