"""Adversarial test matrix for the united_airlines reviewer verifier suite.

Every honest fixture is the reviewer's real live walkthrough (SPECS); every
negative case is an attack on one gate. Zero false positives required: a
verifier may only PASS its honest fixture and must FAIL every attack.

Note on task 2: the award-redemption button was broken in the mirror UI at
review time (hidden method=card input preceded the Redeem submit button —
review finding F-1). The fix at 93a2638f removes the hidden input and puts
name="method" on both submit buttons; the reviewer's r2 live walk of the
real Redeem click (container wh-united-airlines-rereview) lands the award
booking exactly as this contract freezes it: 42,595 miles redeemed,
balance 25,855, award_booking row with total 0.0 and a single -42,595
activity, no award miles/PQP credited back to the traveler.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _support import (PNG, RunBuilder, acquire_seed, make_after_db,  # noqa: E402
                      make_dirty_seed, make_stale_after_db, run_verifier,
                      task_ques, TASKS_FILE)
from fixtures_data import BASE, SPECS  # noqa: E402

TASK_COUNT = 21


@pytest.fixture(scope="session")
def seed_db(tmp_path_factory):
    return acquire_seed()


def build_honest_run(root: Path, task_no: int, answer=None, urls=None) -> Path:
    rb = RunBuilder(root, f"United Airlines--{task_no}")
    from _support import _resolve
    for u in (urls if urls is not None else SPECS[task_no]["urls"]):
        rb.add_step("navigate", _resolve(u))
    return rb.write(answer if answer is not None else SPECS[task_no]["answer"])


# ---------------------------------------------------------------- honest PASS
@pytest.mark.parametrize("task_no", range(TASK_COUNT))
def test_honest_walkthrough_passes(task_no, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"honest_{task_no}", task_no)
    after_db = make_after_db(tmp_path / f"after_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert verdict["pass"], f"honest run must PASS: {verdict['reason']}"


# ---------------------------------------------------------------- no-op FAIL
@pytest.mark.parametrize("task_no", range(TASK_COUNT))
def test_noop_fails(task_no, tmp_path, seed_db):
    """Agent opens the homepage, does nothing, empty answer: every verifier
    must FAIL (no false positives on a blank run)."""
    rb = RunBuilder(tmp_path / f"noop_{task_no}", f"United Airlines--{task_no}")
    rb.add_step("navigate", BASE + "/")
    run_dir = rb.write("")
    after_db = shutil.copyfile(seed_db, tmp_path / f"after_noop_{task_no}.db")
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "no-op run must FAIL"


# ---------------------------------------------------------------- shortcut FAIL
@pytest.mark.parametrize("task_no", [0, 2, 3, 6, 7, 8, 9, 13, 17, 19, 20])
def test_answer_without_navigation_fails(task_no, tmp_path, seed_db):
    """Correct answer text but the agent never opened the task's pages:
    memory-recall shortcut = FAIL."""
    run_dir = RunBuilder(tmp_path / f"shortcut_{task_no}",
                         f"United Airlines--{task_no}").write(SPECS[task_no]["answer"])
    after_db = make_after_db(tmp_path / f"after_sc_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "shortcut run must FAIL"


# ---------------------------------------------------------------- wrong answer FAIL
@pytest.mark.parametrize("task_no, wrong", [
    (0, "The cheapest Economy fare was UA 2790 at $999.99; confirmation ABC123, total $999.99."),
    (4, "UA 2855 departs 09:00 and arrives 12:00 on a Boeing 737 with Gogo Wi-Fi, 2 Polaris rows and 1 Premium Plus row."),
    (5, "UA 178 fares: BE $100, ECO $200, EPU $300, PP $400, BUS $500; cheapest Premium Plus is UA 999."),
    (11, "Bags cost $10 and $20 online, $5 at the airport; weight limits 100 lb and 5 lb."),
    (12, "Max checked size 100 linear inches, Economy 99 lb, Premier 5 lb, 60-lb bag free, carry-on 50x50x50."),
    (14, "Carol has 9 PQF and 3420 PQP; Silver needs 99 PQF and 99,000 PQP or 1,000 PQP; 1K earns 2 miles per dollar."),
    (16, "The 787-9 has 99 seat rows, 50 Polaris, 40 Premium Plus, 30 Economy Plus rows, 999 seats, Gogo Wi-Fi, 1000 mph, wingspan 300 ft, Rolls-Royce engines. The 777-300ER has 88 rows."),
    (17, "Check-in opens 1 hour before and closes 5 minutes before; same-day change is $500; redeposit costs $250; no-show is free; Economy Plus starts at $500."),
    (18, "UA 1197 departs 01:00 arrives 02:00; UA 407 03:00-04:00; UA 1792 05:00-06:00; earliest is UA 407 at 04:00, 9h 99m, Gogo Wi-Fi; Denver is not a United hub."),
])
def test_wrong_answer_fails(task_no, wrong, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"wrong_{task_no}", task_no, answer=wrong)
    after_db = make_after_db(tmp_path / f"after_w_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong-answer run must FAIL"


# ---------------------------------------------------------------- stale DB FAIL
@pytest.mark.parametrize("task_no", [0, 3, 6, 7, 8, 9, 13, 19, 20])
def test_stale_db_fails(task_no, tmp_path, seed_db):
    """Honest trajectory and answer, but the after-DB shows the stateful
    write never happened (stale DB): FAIL."""
    run_dir = build_honest_run(tmp_path / f"stale_{task_no}", task_no)
    after_db = make_stale_after_db(tmp_path / f"after_stale_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "stale-DB run must FAIL"


# ---------------------------------------------------------------- read-only violation FAIL
@pytest.mark.parametrize("task_no", [4, 5, 11, 12, 14, 15, 16, 17, 18])
def test_readonly_violation_fails(task_no, tmp_path, seed_db):
    """Read-only task but the after-DB carries an extra write: FAIL."""
    run_dir = build_honest_run(tmp_path / f"dirty_{task_no}", task_no)
    after_db = tmp_path / f"after_dirty_{task_no}.db"
    shutil.copyfile(seed_db, after_db)
    db = sqlite3.connect(after_db)
    db.execute("INSERT INTO passengers (id,booking_id,first_name,last_name,title,"
               "date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
               "VALUES (77,1,'Sneaky','Write','Mr','1990-01-01','Male','','',0,'')")
    db.commit(); db.close()
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "read-only violation must FAIL"


# ---------------------------------------------------------------- dirty seed FAIL
@pytest.mark.parametrize("task_no", [0, 4, 12])
def test_dirty_seed_fails(task_no, tmp_path, seed_db):
    """Run graded against a pre-mutated initial DB: the seed identity gate
    must fail-closed."""
    run_dir = build_honest_run(tmp_path / f"dseed_{task_no}", task_no)
    dirty = make_dirty_seed(tmp_path / f"dirty_seed_{task_no}.db")
    after_db = make_after_db(tmp_path / f"after_dseed_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, dirty, after_db)
    assert not verdict["pass"], "dirty-seed run must FAIL"


# ---------------------------------------------------------------- package tamper FAIL
def test_wrong_task_id_fails(tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / "tid", 0)
    traj = json.loads((run_dir / "trajectory.json").read_text())
    traj["task_id"] = "United Airlines--20"
    (run_dir / "trajectory.json").write_text(json.dumps(traj))
    after_db = make_after_db(tmp_path / "after_tid.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong task_id must FAIL"


def test_offsite_url_fails(tmp_path, seed_db):
    urls = SPECS[0]["urls"] + ["@@OFFSITE@@"]
    run_dir = build_honest_run(tmp_path / "offsite", 0, urls=urls)
    after_db = make_after_db(tmp_path / "after_offsite.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"], "off-site navigation must FAIL"


def test_cross_port_url_fails(tmp_path, seed_db):
    urls = SPECS[0]["urls"] + ["@@CROSSPORT@@"]
    run_dir = build_honest_run(tmp_path / "xport", 0, urls=urls)
    after_db = make_after_db(tmp_path / "after_xport.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"], "cross-port navigation must FAIL"


def test_unterminated_fails(tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / "unterm", 0)
    traj = json.loads((run_dir / "trajectory.json").read_text())
    traj["terminated"] = False
    traj["termination_reason"] = "error"
    (run_dir / "trajectory.json").write_text(json.dumps(traj))
    after_db = make_after_db(tmp_path / "after_unterm.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"], "unterminated run must FAIL"


def test_bad_screenshot_fails(tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / "badpng", 0)
    shots = sorted((run_dir / "screenshots").glob("step_*.png"))
    shots[0].write_bytes(b"NOT A PNG")
    after_db = make_after_db(tmp_path / "after_badpng.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"], "corrupt screenshot must FAIL"


# ---------------------------------------------------------------- task-specific negatives
def test_t0_wrong_flight_booked_fails(tmp_path, seed_db):
    """Agent books UA 1974 (not the cheapest Economy UA 2790): FAIL."""
    urls = [u.replace("202.95", "226.95") for u in SPECS[0]["urls"]]
    answer = SPECS[0]["answer"].replace("UA 2790", "UA 1974").replace("202.95", "226.95")
    run_dir = build_honest_run(tmp_path / "t0wf", 0, answer=answer, urls=urls)
    after_db = make_after_db(tmp_path / "after_t0wf.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong-flight booking must FAIL"


def test_t2_wrong_miles_fails(tmp_path, seed_db):
    """Award answer with the wrong redeemed-miles figure: FAIL."""
    answer = SPECS[2]["answer"].replace("42,595", "10,000").replace("25,855", "58,450")
    run_dir = build_honest_run(tmp_path / "t2wm", 2, answer=answer)
    after_db = make_after_db(tmp_path / "after_t2wm.db", 2)
    verdict = run_verifier(2, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong redeemed miles must FAIL"


def test_t6_eplus_seat_fails(tmp_path, seed_db):
    """Seat in the Economy Plus band (12A on the 787-8) for a task that asks
    for a standard seat: FAIL."""
    answer = SPECS[6]["answer"].replace("18A", "12A")
    run_dir = build_honest_run(tmp_path / "t6seat", 6, answer=answer)
    after_db = make_after_db(tmp_path / "after_t6seat.db", 6)
    # also write the EPU-band seat into the DB to attack the state check
    db = sqlite3.connect(after_db)
    db.execute("UPDATE passengers SET seat='12A' WHERE id=1")
    db.commit(); db.close()
    verdict = run_verifier(6, run_dir, seed_db, after_db)
    assert not verdict["pass"], "Economy Plus seat must FAIL the standard-seat check"


def test_t8_wrong_change_fails(tmp_path, seed_db):
    """Agent claims moving to UA 2790 (not the latest flight UA 1974): FAIL."""
    answer = SPECS[8]["answer"].replace("1974", "2790").replace("18:17", "16:12").replace("19.84", "0")
    run_dir = build_honest_run(tmp_path / "t8wc", 8, answer=answer)
    after_db = make_after_db(tmp_path / "after_t8wc.db", 8)
    verdict = run_verifier(8, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong-change answer must FAIL"


def test_t8_wrong_original_flight_fails(tmp_path, seed_db):
    """Before/after comparison with the wrong ORIGINAL flight (claims the
    trip started on UA 2790 departing 15:30 instead of UA 2803 at 14:33):
    FAIL."""
    answer = SPECS[8]["answer"].replace("2803", "2790").replace("14:33", "15:30")
    run_dir = build_honest_run(tmp_path / "t8of", 8, answer=answer)
    after_db = make_after_db(tmp_path / "after_t8of.db", 8)
    verdict = run_verifier(8, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong original flight must FAIL"


def test_t12_wrong_3bag_total_fails(tmp_path, seed_db):
    """Calculator run reported with a wrong per-bag/total figure ($35+$45+$35
    = $115 instead of $35+$45+$150 = $230): FAIL."""
    answer = SPECS[12]["answer"].replace("$150", "$35").replace("$230.00", "$115.00")
    run_dir = build_honest_run(tmp_path / "t12bt", 12, answer=answer)
    after_db = make_after_db(tmp_path / "after_t12bt.db", 12)
    verdict = run_verifier(12, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong 3-bag calculator total must FAIL"


def test_t12_no_calculator_run_fails(tmp_path, seed_db):
    """Baggage-rule answer present but the fee-calculator run never happened
    (no calculator navigation, no 3-bag figures): FAIL."""
    answer = SPECS[12]["answer"].rsplit("Pricing three", 1)[0]
    run_dir = build_honest_run(
        tmp_path / "t12nc", 12, answer=answer,
        urls=[u for u in SPECS[12]["urls"] if "fee-calculator" not in u])
    after_db = make_after_db(tmp_path / "after_t12nc.db", 12)
    verdict = run_verifier(12, run_dir, seed_db, after_db)
    assert not verdict["pass"], "missing calculator run must FAIL"


def test_t14_wrong_remaining_fails(tmp_path, seed_db):
    """Claims she only needs 2 more PQF and 640 more PQP (her current
    totals) instead of 10 PQF / 3,360 PQP: FAIL."""
    answer = SPECS[14]["answer"].replace("10 more PQF", "2 more PQF").replace("3,360 more PQP", "640 more PQP")
    run_dir = build_honest_run(tmp_path / "t14rem", 14, answer=answer)
    after_db = make_after_db(tmp_path / "after_t14rem.db", 14)
    verdict = run_verifier(14, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong remaining PQF/PQP must FAIL"


def test_t14_disagreement_claim_fails(tmp_path, seed_db):
    """Claims the two pages state different thresholds (they state the
    same): FAIL."""
    answer = SPECS[14]["answer"].replace(
        "the same thresholds the account page states, so the two pages agree",
        "different thresholds from the account page, so the two pages disagree")
    run_dir = build_honest_run(tmp_path / "t14dis", 14, answer=answer)
    after_db = make_after_db(tmp_path / "after_t14dis.db", 14)
    verdict = run_verifier(14, run_dir, seed_db, after_db)
    assert not verdict["pass"], "false disagreement claim must FAIL"


def test_t16_stale_seat_rows_fails(tmp_path, seed_db):
    """Agent quotes the pre-fix synthesized value (20 seat rows, cruise 561/
    554 mph, wingspan 197 ft 3 in, 115,500 lbf) instead of the re-frozen
    fleet values: FAIL — the r2 contract must not accept stale review-era
    data."""
    answer = SPECS[16]["answer"].replace("rows 37", "rows 20").replace("rows 46", "rows 20") \
        .replace("560 mph", "561 mph").replace("557 mph", "554 mph") \
        .replace("197 ft 4 in", "197 ft 3 in").replace("115,300 lbf", "115,500 lbf")
    run_dir = build_honest_run(tmp_path / "t16stale", 16, answer=answer)
    after_db = make_after_db(tmp_path / "after_t16stale.db", 16)
    verdict = run_verifier(16, run_dir, seed_db, after_db)
    assert not verdict["pass"], "stale fleet values must FAIL"


def test_t17_missing_source_titles_fails(tmp_path, seed_db):
    """All four answers present with correct navigation, but none of the
    source-article titles is reported: FAIL."""
    answer = ("Help Center answers. (1) Online check-in opens 24 hours before departure "
              "and closes 60 minutes before departure. (2) The same-day flight change "
              "fee is up to $75, and standby is free if you are a Premier member. "
              "(3) After canceling an award flight there is no redeposit fee; if you "
              "no-show, a $125 service fee applies. (4) The lowest Economy Plus price "
              "is $29 per flight.")
    run_dir = build_honest_run(tmp_path / "t17notitle", 17, answer=answer)
    after_db = make_after_db(tmp_path / "after_t17notitle.db", 17)
    verdict = run_verifier(17, run_dir, seed_db, after_db)
    assert not verdict["pass"], "missing source-article titles must FAIL"


def test_t10_credit_absent_fails(tmp_path, seed_db):
    """Cancel answer that claims a cash refund for Basic Economy: FAIL."""
    answer = ("Basic Economy tickets cannot be changed. After canceling, I received "
              "a cash refund of $198.08 to my card immediately.")
    run_dir = build_honest_run(tmp_path / "t10cash", 10, answer=answer)
    after_db = make_after_db(tmp_path / "after_t10cash.db", 10)
    verdict = run_verifier(10, run_dir, seed_db, after_db)
    assert not verdict["pass"], "cash-refund claim for Basic Economy must FAIL"


def test_t17_missing_source_articles_fails(tmp_path, seed_db):
    """Answers present but the Help Center articles were never opened: FAIL."""
    answer = SPECS[17]["answer"]
    rb = RunBuilder(tmp_path / "t17nav", "United Airlines--17")
    rb.add_step("navigate", BASE + "/")
    run_dir = rb.write(answer)
    after_db = make_after_db(tmp_path / "after_t17nav.db", 17)
    verdict = run_verifier(17, run_dir, seed_db, after_db)
    assert not verdict["pass"], "missing help-article navigation must FAIL"


# ---------------------------------------------------------------- tasks.jsonl sanity
def test_tasks_jsonl_keys_and_rubrics():
    lines = TASKS_FILE.read_text(encoding="utf-8").splitlines()
    assert len(lines) == TASK_COUNT
    for i, line in enumerate(lines):
        row = json.loads(line)
        assert list(row.keys()) == ["web_name", "id", "ques", "web",
                                    "upstream_url", "verifier_path", "judge_rubric"], \
            f"row {i} keys must be the 5 original keys + verifier_path + judge_rubric"
        assert row["id"] == f"United Airlines--{i}"
        assert row["verifier_path"].startswith("sites/united_airlines/verify/verify_")
        rubric = row["judge_rubric"]
        assert "FACT CHECKPOINTS" in rubric
        assert "answer" not in row, "no answer key may live in tasks.jsonl"
        for banned in ("VRMEZ8", "9ZEK48", "WTV9G8", "RHHYTY", "AKGGFG",
                       "XSZ2SB", "HJSCAX", "VV8N4V", "1759967178"):
            assert banned not in line, f"ground truth {banned} leaked into tasks.jsonl row {i}"


def test_verifier_path_files_exist():
    lines = TASKS_FILE.read_text(encoding="utf-8").splitlines()
    site_root = Path(__file__).resolve().parents[2]
    for i, line in enumerate(lines):
        row = json.loads(line)
        p = site_root / row["verifier_path"].replace("sites/united_airlines/", "")
        assert p.is_file(), f"missing verifier for task {i}: {p}"
