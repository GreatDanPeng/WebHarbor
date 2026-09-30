#!/usr/bin/env python3
"""test_verifiers.py — adversarial contract tests for the virginia_dmv verifier suite.

Guarantees (run with pytest):
  * each honest fixture PASSES its verify_<n>.py. The fixtures are:
      - T5/T11/T14/T15/T16/T18 (and every other task): the position-60
        auditor's own honest task-text-only walks on the independent audit
        container (wh-vadm-audit, ports 49112/50112/51112, seed md5
        e20897642a951494ced5ad6393a78ad7; answers composed strictly from
        the observed page originals — no artifact copied from the
        contributor or reviewer rails);
      - every other task: the r2 reviewer's honest fixtures, verbatim (task
        texts unchanged in r3, so those honest artifacts remain the
        acceptance baseline for them);
  * every adversarial negative FAILS (zero false positives):
      - no-op trajectories (20),
      - answer-only shortcuts with no navigation (20),
      - wrong-answer trajectories (20, fabricated per question point),
      - stale-DB trajectories (all 11 stateful tasks),
      - read-only violations (unexpected DB writes on read-only tasks),
      - tampered packages (wrong task_id / off-site URL / cross-port /
        not-terminated / empty answer / bad PNG / pre-mutated seed),
      - task-specific confusions (renewal-vs-replacement answers, swapped
        preview totals, swapped plate facts, swapped office pages, swapped
        fee-chart rows, swapped REAL-ID/news facts),
      - wrong state rows (wrong renewal term/REAL ID, plate on wrong vehicle,
        appointment not canceled, record request by mail, booked appointment
        with wrong service/office/name, vehicle record ordered by mail).

    r3 sync: the contract adopts the r2 reviewer sync (over-ask answer keys
    and over-gate navigation removed) and re-anchors T5/T11/T14/T15/T16/T18
    to the deepened task texts (honest atomic depth >= 15 with real composite
    actions: finder-filter derivations, wizard bookings, renewal preview,
    certified vehicle-record order, receipt reopens, pager navigation).
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
EV = Path("/data/zhaoyang-user-projects/websyn/wh-virginia-dmv-audit-evidence")
FIXTURES = EV / "runs"
TMP = EV / "verify_runs" / "_pytest_tmp"
PY = sys.executable

TASK_IDS = [f"Virginia DMV--{n}" for n in range(20)]
STATEFUL = [0, 1, 3, 6, 11, 12, 13, 14, 15, 16, 18]
READ_ONLY = [n for n in range(20) if n not in STATEFUL]


def run_verifier(n: int, run_dir: Path):
    proc = subprocess.run(
        [PY, str(VERIFY / f"verify_{n}.py"), "--run_dir", str(run_dir)],
        capture_output=True, text=True, timeout=120)
    try:
        verdict = json.loads(proc.stdout)
    except json.JSONDecodeError:
        verdict = {"pass": False, "reason": proc.stdout[-300:] or proc.stderr[-300:]}
    return verdict


def clone(n: int, tag: str) -> Path:
    dst = TMP / f"task{n}_{tag}"
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


def cross_port(run_dir: Path):
    """Rewrite every step URL onto a different port than the start URL."""
    from urllib.parse import urlparse, urlunsplit
    p = run_dir / "trajectory.json"
    traj = json.loads(p.read_text())
    start = traj["start_url"]
    bad_port = urlparse(start).port + 2000
    def bump(url):
        u = urlparse(url)
        return urlunsplit((u.scheme, f"{u.hostname}:{bad_port}", u.path, u.query, u.fragment))
    for step in traj.get("steps", []):
        step["url"] = bump(step["url"])
        if "url_after" in step:
            step["url_after"] = bump(step["url_after"])
    p.write_text(json.dumps(traj, indent=2))


# ---------------------------------------------------------------- happy path
@pytest.mark.parametrize("n", range(20))
def test_honest_fixture_passes(n):
    verdict = run_verifier(n, FIXTURES / f"task{n}")
    assert verdict["pass"], verdict["reason"]


# ---------------------------------------------------------------- no-op
@pytest.mark.parametrize("n", range(20))
def test_noop_fails(n):
    run_dir = clone(n, "noop")
    set_traj(run_dir, steps=[], final_answer="", terminated=False,
             termination_reason="max_steps")
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]


# ---------------------------------------------------------------- shortcuts
@pytest.mark.parametrize("n", range(20))
def test_answer_only_shortcut_fails(n):
    run_dir = clone(n, "shortcut")
    drop_nav(run_dir)
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]
    assert any("nav_" in e for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- wrong answers
WRONG = {
    0: "License D5540918, expires 2025-09-02, REAL ID compliant. Renewal quotes $5.00 per year; the 8-year standard term previews $40.00; the fee chart lists REAL ID as a $12.00 one-time fee with a $10 minimum; the chart is DMV 301, edition 01/01/2026. With REAL ID added the total charged was $52.00, receipt LIC260929-AAAAAA. New expiration 2034-08-02; card arrives by U.S. mail within 10 business days. The reopened receipt lists $40.00 / $12.00 / $52.00.",
    1: "Camry previews: 1-year $30.75, 2-year $61.50, 3-year $92.25. Two-year fee lines: registration $65.50, internet discount -$4.00, 2-year discount -$5.00. The registration page advertises a $5 two-year and $6 three-year discount. Paid receipt REG260929-BBBBBB; new registration expiration 2027-10-15. The reopened receipt lists $65.50 / -$4.00 / -$5.00 totaling $61.50.",
    2: "Bolt EV previews: 1-year $146.24 (registration $30.75 + EV highway use fee $116.49 + internet discount -$1.00), 2-year $300.00, 3-year $450.00. ID card ID9912346 expires 2027-05-09. The highway use fee page defines a fuel-efficient vehicle as 35 MPG or greater, exempts tractor-trailers and buses, and bases the calculation on the vehicle's color. Registration page discounts: $5 for two years, $6 for three online. Emissions inspections valid five years in Richmond and Norfolk counties. Bolt title T5533-9999, VIN 1G1FY6S00L9999999.",
    3: "Go Hokies plate: $10 annually, personalization No, type codes HOKIE only. Personalized plate fee $5 annually. Revenue sharing: $10.00 of the $25.00 fee is transferred to Virginia Tech after the sale of the first 500 qualifying plates. Total charged $15.00, receipt PLT260929-CCCCCC.",
    4: "173rd Airborne: $25 annually, 8 characters, requirements DD214 only, disabled symbol Yes. AIRBRN available: no. HOOAH available: yes.",
    5: "Alexandria CSC: 2681 Mill Road; tel 703-497-7100; fax 703-317-3565; Mon-Fri 9:00 am-5:00 pm, Sat 9:00 am-12:00 pm; motorcycle skills testing available, in-car road skills testing not available; the Franconia office's fax is 703-922-3876 and it offers E-Z Pass Flex which Alexandria does not. The finder lists 76 DMV Select offices in total; an Alexandria search within DMV Select lists 3 offices, e.g. AAA Alexandria at 2231 Richmond Highway; a Fairfax search lists 5; the finder lists 58 customer service centers.",
    6: "Booked Driver's License Renewal at Richmond Central (2300 West Broad Street), 2026-10-09 at 2:00 PM, confirmation VADM260929-DDDDDD, confirmation lists email bob.c@test.org. Canceled; cancel confirmation: Your appointment has been rescheduled.",
    7: "Appointment VADM9620114A: Driver's License Replacement at Richmond Central, 2026-10-08 at 10:20 AM, status Canceled. Richmond Central: 2300 East Broad Street, tel 804-497-7101, Mon-Fri 9:00 am-5:00 pm, Sat 9:00 am-12:00 pm; does not offer Road Skills Testing: In-car. Nearby: West Henrico. A Richmond search lists 8 offices overall and 3 within DMV Select.",
    8: "Red light: slow down and proceed with caution. Flashing yellow: come to a complete stop. Exam: 10 questions, score 10/10 (50%), passed. Sample feedback: the sky is blue.",
    9: "Retake: wait a full 30 days if under 18 (example: fail Jan 1 -> retake Feb 1); exam twice per business day; part one requires 80 percent of sign questions; part two requires 90 percent; audio version not offered. Exempt out-of-country licenses: Japan, China, Brazil; the road skills test additionally exempts Spain. Vision: 20/50; restriction code B for glasses; minimum learner's permit holding period 9 months; anyone with a license may accompany a permit holder. Safe Driving practice exam: 7/8, 88%, passed.",
    10: "Camry previews: 1-year $30.75, 2-year $61.50, 3-year $92.25; license renewal previews $40.00 at $5.00 per year. Fee chart audit: passenger car $35.75, motorcycle $30.75, pickup $55.75; emissions fee $4.00; late fee $25.00; replacement title $20.00; sales tax 3.15% with a $50.00 minimum; registration page advertises $5/$6 discounts. The fee chart is DMV 301, edition 01/01/2026.",
    11: "Prospective purchaser form: CRD 02, 'Vehicle Information Request'; the catalog lists 430 forms, 25 in Spanish. The translator certification form's number is DTS 37. PPI requested in person only; mailed reports take 30 days. The fee chart charges $5.00 for the inquiry. The Driver Record / Vehicle Record appointment at the Alexandria office on 2026-10-06 is reserved: confirmation VADM260929-EEEEEE, booked time 2:00 PM.",
    12: "Address changed to 4020 University Drive, Fairfax, VA 22030; confirmation 'Your address has been saved.'; receipt ADR260929-EEEEEE added; the receipt copy is a Name Change receipt with total $5.00. You must notify DMV within 60 days of moving; a P.O. box is acceptable; you cannot register to vote; changing out of state upgrades your license. DMV stores two kinds of address: Home and Work.",
    13: "Driving record base $9.00 online, certified copy +$3.00, total $12.00, receipt REC260929-FFFFFF, online view available for 10 days at no extra charge. RAV4: title T8842-1195, VIN 1HGCF1A23XA448119. The reopened receipt lists $9.00 + $3.00 = $12.00. The fee chart shows $10.00 by mail against the $9.00 online price.",
    14: "The standard-term renewal preview totals $40.00 at $5.00 per year. Credential Learner's Permit — Class M; account-page status: Valid; other reasons offered: Lost, Stolen; replacement fee $10.00, total $10.00, receipt REP260929-111111; card arrives within 10 business days; the receipt copy lists $10.00. The replacement page: if expiration is more than one year away you may renew instead; online replacement is blocked only if you are over 18; in person you present form DL 5.",
    15: "New resident: get a Virginia license within 90 days (CDL 60 days); title within 45 days; the safety inspection is optional; emissions counties include Richmond and Norfolk; maintain insurance from the day you first drive; the local sticker comes from DMV; the voter registration note says registration is online only; an out-of-state license never exempts the knowledge exam. A Richmond search lists 8 offices, 3 of them customer service centers. The Vehicle Registration / Title appointment at Richmond Central on 2026-10-05: confirmation VADM260929-777777, booked 2:00 PM.",
    16: "The Camry's record order shows title T9013-4427 and VIN 2T3W1RFV0KW204361. The certified vehicle record charged $12.00 total, receipt REC260929-888888; the receipt copy lists $9.00 + $3.00. Seller steps: sign over the title, keep your plates on the vehicle, tell your bank. Plates: surrender nothing. Refund form FMS-210A. Gift form SUT-1. Notify by phone at (703) 555-0123. Buyer applies with VSA 17B. The PPI report includes only the owner's name. Fees: registration transfer $5.00, replacement registration card $1.00, vehicle record online $9.00, original title $25.00.",
    17: "2025+ limits: $30,000/$60,000/$20,000; 2022-2024: $25,000/$50,000/$25,000. DMV verifies coverage by mail; the verification transaction asks only for your birthdate; if coverage cancels you must do nothing; uninsured owners pay a $500 fee, file SR-22 for one year; the payment plan offers automatic ACH payments. Registration page note: for-hire vehicles require lower insurance limits. The appointments page offers appointments only. A Roanoke search lists the Hampton CSC at 8109 Roanoke Avenue.",
    18: "REAL ID: $20 one-time fee plus license/ID cost (minimum $10 transaction); looks like a license with a gold star in the bottom left; three steps to apply; required to board an international flight. Documents guide DMV 140, brochure DMV 290. Newsroom: Apple Wallet announcement released September 26, 2026; the newest item is the Drive Sober campaign; on the last page the oldest item is 'DMV Unveils New Ad Campaign to Boost Motorcycle Safety Training' from November 21, 2024. The REAL ID appointment at Arlington on 2026-10-06: confirmation VADM260929-999999, booked 2:00 PM.",
    19: "HAZMAT background check + fingerprinting $100.00; TWIC-related reduced fee $50.00 when holding a valid TWIC card expiring within 6 months; TWIC comparability means the HME outlasts the TWIC; minimum age 25 to transport hazardous materials; forms DL 71 and DL 3. CDL $10/year with $50 minimum; missed appointment $25.00; endorsement $2.00/year; commercial learner's permit $5.00. The HAZMAT knowledge exam is available in every language. The wizard offered an afternoon slot at 3:00 PM.",
}


@pytest.mark.parametrize("n", range(20))
def test_wrong_answer_fails(n):
    run_dir = clone(n, "wrong")
    mutate_answer(run_dir, WRONG[n])
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]


# ---------------------------------------------------------------- stale DB (stateful)
@pytest.mark.parametrize("n", STATEFUL)
def test_stale_db_fails(n):
    """Stateful task with NO DB change (agent self-reported but never acted)."""
    run_dir = clone(n, "stale")
    shutil.copyfile(run_dir / "initial.db", run_dir / "after.db")
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]
    assert any(("added" in e or "changed" in e or "removed" in e)
               for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- read-only violations
@pytest.mark.parametrize("n", READ_ONLY)
def test_read_only_violation_fails(n):
    """Read-only task whose DB acquired an unexpected write."""
    run_dir = clone(n, "dirty")
    mutate_db(run_dir, "after.db",
              "INSERT INTO transactions (receipt, user_id, kind, summary, total, "
              "details, created_at) VALUES ('SNEAKY01', 1, 'Sneaky Write', "
              "'unexpected write', '$1.00', '{}', '2026-09-29')")
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]
    assert any("db_read_only" in e for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- tampered packages
def test_tampered_task_id_fails():
    run_dir = clone(2, "tampered_id")
    set_traj(run_dir, task_id="Virginia DMV--0")
    verdict = run_verifier(2, run_dir)
    assert not verdict["pass"]


def test_tampered_offsite_url_fails():
    run_dir = clone(1, "offsite")
    set_traj(run_dir, start_url="https://www.dmv.virginia.gov/")
    verdict = run_verifier(1, run_dir)
    assert not verdict["pass"]


def test_tampered_cross_port_fails():
    run_dir = clone(3, "crossport")
    cross_port(run_dir)
    verdict = run_verifier(3, run_dir)
    assert not verdict["pass"]


def test_tampered_not_terminated_fails():
    run_dir = clone(7, "notterm")
    set_traj(run_dir, terminated=False, termination_reason="max_steps")
    verdict = run_verifier(7, run_dir)
    assert not verdict["pass"]


def test_tampered_empty_answer_fails():
    run_dir = clone(11, "emptyans")
    mutate_answer(run_dir, "")
    verdict = run_verifier(11, run_dir)
    assert not verdict["pass"]


def test_tampered_bad_png_fails():
    run_dir = clone(13, "badpng")
    shots = sorted((run_dir / "screenshots").glob("step_*.png"))
    assert shots, "fixture must contain screenshots"
    shots[0].write_bytes(b"not a png at all")
    verdict = run_verifier(13, run_dir)
    assert not verdict["pass"]
    assert any("screenshots" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_tampered_seed_fails():
    """A pre-mutated initial DB must fail the seed identity gate."""
    run_dir = clone(5, "premutated")
    mutate_db(run_dir, "initial.db",
              "INSERT INTO transactions (receipt, user_id, kind, summary, total, "
              "details, created_at) VALUES ('PRE00001', 1, 'Pre Mutated', "
              "'pre-mutated seed', '$1.00', '{}', '2026-09-29')")
    verdict = run_verifier(5, run_dir)
    assert not verdict["pass"]
    assert any("seed_" in e for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- task confusions
def test_confusion_renewal_answer_on_replacement_fails():
    """T0's renewal answer + T0 navigation on T14's (replacement) verifier."""
    run_dir = clone(14, "confusion")
    src = json.loads((FIXTURES / "task0" / "trajectory.json").read_text())
    (run_dir / "trajectory.json").write_text(json.dumps(src, indent=2))
    verdict = run_verifier(14, run_dir)
    assert not verdict["pass"]


def test_confusion_swapped_preview_totals_fails():
    """T1's answer (Camry previews) on T2's (Bolt EV) package."""
    run_dir = clone(2, "confusion2")
    src = json.loads((FIXTURES / "task1" / "trajectory.json").read_text())
    (run_dir / "trajectory.json").write_text(json.dumps(src, indent=2))
    verdict = run_verifier(2, run_dir)
    assert not verdict["pass"]


def test_confusion_swapped_plate_facts_fails():
    """T3's Go Hokies answer on T4's (173rd Airborne) package."""
    run_dir = clone(4, "confusion3")
    src = json.loads((FIXTURES / "task3" / "trajectory.json").read_text())
    (run_dir / "trajectory.json").write_text(json.dumps(src, indent=2))
    verdict = run_verifier(4, run_dir)
    assert not verdict["pass"]


def test_confusion_swapped_offices_fails():
    """T5's Alexandria answer on T7's (Richmond Central) package."""
    run_dir = clone(7, "confusion4")
    src = json.loads((FIXTURES / "task5" / "trajectory.json").read_text())
    (run_dir / "trajectory.json").write_text(json.dumps(src, indent=2))
    verdict = run_verifier(7, run_dir)
    assert not verdict["pass"]


def test_confusion_t13_record_on_t16_sell_package_fails():
    """T13's driving-record answer + DB on T16's (vehicle-record) verifier."""
    run_dir = clone(16, "confusion5")
    src = json.loads((FIXTURES / "task13" / "trajectory.json").read_text())
    (run_dir / "trajectory.json").write_text(json.dumps(src, indent=2))
    shutil.copyfile(FIXTURES / "task13" / "initial.db", run_dir / "initial.db")
    shutil.copyfile(FIXTURES / "task13" / "after.db", run_dir / "after.db")
    verdict = run_verifier(16, run_dir)
    assert not verdict["pass"]


def test_confusion_swapped_realid_news_fails():
    """T18 with the REAL-ID fee/news facts swapped."""
    run_dir = clone(18, "confusion6")
    wrong18 = ("REAL ID: $20 one-time fee (minimum $10); looks like a license with a "
               "star in the upper right corner; two steps to apply; required to "
               "board a domestic flight or enter a secure federal facility. Documents "
               "guide DMV 141, brochure DMV 299. Newsroom: Apple Wallet announcement "
               "released August 26, 2026, letting you add a Virginia license or ID "
               "to Apple Wallet; the newest item is \"New DMV Select Brings Vehicles "
               "Services to Page County\"; on the last page the oldest item is "
               "\"DMV Unveils New Ad Campaign to Boost Motorcycle Safety Training\", "
               "released November 21, 2024. The REAL ID appointment at Arlington on "
               "2026-10-06: confirmation VADM260929-9DB8D6, booked 8:00 AM.")
    mutate_answer(run_dir, wrong18)
    verdict = run_verifier(18, run_dir)
    assert not verdict["pass"]


# ---------------------------------------------------------------- wrong state rows
def test_wrong_state_renewal_fails():
    """T0 honest answer but the DB shows a 5-year renewal without REAL ID."""
    run_dir = clone(0, "wrongstate")
    mutate_db(run_dir, "after.db",
              "UPDATE user_licenses SET expires='2030-08-02', real_id=0 "
              "WHERE number='D5540917'")
    verdict = run_verifier(0, run_dir)
    assert not verdict["pass"]
    assert any("license_renewed" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_wrong_state_purchase_fails():
    """T3 honest answer but the plate went to the wrong vehicle."""
    run_dir = clone(3, "wrongstate")
    mutate_db(run_dir, "after.db",
              "UPDATE vehicles SET plate_design='virginia-tech-go-hokies' WHERE id=1")
    verdict = run_verifier(3, run_dir)
    assert not verdict["pass"]
    assert any("plate_assigned" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_wrong_state_appointment_not_canceled_fails():
    """T6 honest answer but the appointment is still Confirmed."""
    run_dir = clone(6, "wrongstate")
    mutate_db(run_dir, "after.db",
              "UPDATE appointments SET status='Confirmed' "
              "WHERE confirmation LIKE 'VADM%' AND user_id=2")
    verdict = run_verifier(6, run_dir)
    assert not verdict["pass"]
    assert any("appt_added_canceled" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_wrong_state_record_request_by_mail_fails():
    """T13 honest answer but the record request was mailed, not online."""
    run_dir = clone(13, "wrongstate")
    mutate_db(run_dir, "after.db",
              "UPDATE record_requests SET delivery='mail' WHERE receipt LIKE 'REC%'")
    verdict = run_verifier(13, run_dir)
    assert not verdict["pass"]
    assert any("record_request_added" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_wrong_state_ppi_appointment_wrong_service_fails():
    """T11 honest answer but the booked appointment is the wrong service."""
    run_dir = clone(11, "wrongstate")
    mutate_db(run_dir, "after.db",
              "UPDATE appointments SET service='Driver Record / Vehicle Record -- express' "
              "WHERE confirmation LIKE 'VADM260929%'")
    verdict = run_verifier(11, run_dir)
    assert not verdict["pass"]
    assert any("appt_added" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_wrong_state_title_appointment_wrong_office_fails():
    """T15 honest answer but the booking went to the wrong office."""
    run_dir = clone(15, "wrongstate")
    mutate_db(run_dir, "after.db",
              "UPDATE appointments SET office_slug='virginia-beach' "
              "WHERE confirmation LIKE 'VADM260929%'")
    verdict = run_verifier(15, run_dir)
    assert not verdict["pass"]
    assert any("appt_added" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_wrong_state_realid_appointment_wrong_name_fails():
    """T18 honest answer but the booking is under the wrong name."""
    run_dir = clone(18, "wrongstate")
    mutate_db(run_dir, "after.db",
              "UPDATE appointments SET name='Jamie Reese' "
              "WHERE confirmation LIKE 'VADM260929%'")
    verdict = run_verifier(18, run_dir)
    assert not verdict["pass"]
    assert any("appt_added" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_wrong_state_vehicle_record_by_mail_fails():
    """T16 honest answer but the certified vehicle record was mailed, not online."""
    run_dir = clone(16, "wrongstate")
    mutate_db(run_dir, "after.db",
              "UPDATE record_requests SET delivery='mail' WHERE receipt LIKE 'REC%'")
    verdict = run_verifier(16, run_dir)
    assert not verdict["pass"]
    assert any("record_request_added" in e for e in verdict["evidence"] if e.startswith("FAIL"))
