"""Adversarial test matrix for the u_s_customs reviewer verifier suite.

Every honest fixture is the reviewer's real live walkthrough (SPECS); every
negative case is an attack on one gate. Zero false positives required: a
verifier may only PASS its honest fixture and must FAIL every attack.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import (PNG, RunBuilder, acquire_seed, make_after_db,  # noqa: E402
                      run_verifier, task_ques)
from fixtures_data import BASE, SPECS  # noqa: E402


@pytest.fixture(scope="session")
def seed_db(tmp_path_factory):
    return acquire_seed()


@pytest.fixture()
def dirs(tmp_path):
    return tmp_path


def build_honest_run(root: Path, task_no: int, answer=None, paths=None) -> Path:
    rb = RunBuilder(root, f"CBP.gov--{task_no}")
    for pth in (paths if paths is not None else SPECS[task_no]["paths"]):
        rb.add_step("navigate", BASE + pth)
    return rb.write(answer if answer is not None else SPECS[task_no]["answer"])


# ---------------------------------------------------------------- honest PASS
@pytest.mark.parametrize("task_no", range(21))
def test_honest_walkthrough_passes(task_no, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"honest_{task_no}", task_no)
    after_db = make_after_db(tmp_path / f"after_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert verdict["pass"], f"honest run must PASS: {verdict['reason']}"


# ---------------------------------------------------------------- no-op FAIL
@pytest.mark.parametrize("task_no", range(21))
def test_noop_fails(task_no, tmp_path, seed_db):
    """Correct answer + correct DB but ZERO navigation: knowledge shortcut."""
    rb = RunBuilder(tmp_path / f"noop_{task_no}", f"CBP.gov--{task_no}")
    rb.add_step("navigate", BASE + "/")  # stays on home, opens nothing
    run_dir = rb.write(SPECS[task_no]["answer"])
    after_db = make_after_db(tmp_path / f"after_noop_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "no-op shortcut must FAIL"


# ---------------------------------------------------------------- wrong answers
WRONG_ANSWERS = {
    0: "The longest delay is San Ysidro with 999 minutes and 42 lanes open.",
    2: "San Ysidro standard delay is 42 minutes; port code 9999.",
    4: "There are 30 VWP countries and stays of 30 days; Germany is not listed.",
    7: "The man was John Doe, 99, from Miami; 12 pounds seized at LAX by the FBI.",
    9: "There are 90 forms; form 7501 is titled Customs Declaration dated Jan 1 2020.",
    12: "There are 5 priority trade issues, all named Revenue.",
    13: "The BPA salary is $30,000 - $40,000 with a $5,000 incentive.",
    15: "Dana saved the Blaine crossing with 999-minute delays.",
    16: "Global Entry costs $50 for 3 years and NEXUS costs $999.",
    19: "The advisory discusses Form 1234 (Cargo Manifest); 100 Canadian crossings.",
    20: "The Global Entry search returns 9 sections; the San Ysidro form is 9999.",
}


@pytest.mark.parametrize("task_no, wrong", sorted(WRONG_ANSWERS.items()))
def test_wrong_answer_fails(task_no, wrong, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"wrong_{task_no}", task_no, answer=wrong)
    after_db = make_after_db(tmp_path / f"after_wrong_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong answer must FAIL"


# ---------------------------------------------------- stale DB (missing mutation)
@pytest.mark.parametrize("task_no", [3, 6, 10, 17])
def test_stateful_without_mutation_fails(task_no, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"stale_{task_no}", task_no)
    after_db = shutil.copyfile(seed_db, tmp_path / f"after_stale_{task_no}.db")
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "stateful task with unmutated DB must FAIL"


# ---------------------------------------------------- read-only violation
def test_readonly_violation_fails(tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / "dirty_0", 0)
    after_db = shutil.copyfile(seed_db, tmp_path / "after_dirty_0.db")
    db = sqlite3.connect(after_db)
    db.execute("INSERT INTO saved_forms (user_id, form_id, created_at) "
               "VALUES (1, 61, '2026-09-28')")
    db.commit()
    db.close()
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"], "read-only task with injected row must FAIL"


def test_extra_table_write_on_stateful_fails(tmp_path, seed_db):
    """T6 honest schedule + a sneaky extra write elsewhere -> FAIL."""
    run_dir = build_honest_run(tmp_path / "sneaky_6", 6)
    after_db = make_after_db(tmp_path / "after_sneaky_6.db", 6)
    db = sqlite3.connect(after_db)
    db.execute("INSERT INTO saved_forms (user_id, form_id, created_at) "
               "VALUES (1, 61, '2026-09-28')")
    db.commit()
    db.close()
    verdict = run_verifier(6, run_dir, seed_db, after_db)
    assert not verdict["pass"], "unexpected extra table write must FAIL"


# ---------------------------------------------------------------- package tampering
def test_wrong_task_id_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "tamper_id", "CBP.gov--0")
    for pth in SPECS[0]["paths"]:
        rb.add_step("navigate", BASE + pth)
    run_dir = rb.write(SPECS[0]["answer"], task_id="CBP.gov--20")
    after_db = make_after_db(tmp_path / "after_tamper_id.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_offsite_url_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "tamper_offsite", "CBP.gov--0")
    rb.add_step("navigate", BASE + "/bwt?border=mexico&sort=delay")
    rb.add_step("navigate", "https://www.cbp.gov/bwt")  # off-site detour
    rb.add_step("navigate", BASE + "/bwt/crossing/250601")
    rb.add_step("navigate", BASE + "/bwt/crossing/250602")
    run_dir = rb.write(SPECS[0]["answer"])
    after_db = make_after_db(tmp_path / "after_tamper_off.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_other_port_url_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "tamper_port", "CBP.gov--0")
    rb.add_step("navigate", BASE + "/bwt?border=mexico&sort=delay")
    rb.add_step("navigate", "http://localhost:47105/bwt/crossing/250601")
    rb.add_step("navigate", BASE + "/bwt/crossing/250601")
    rb.add_step("navigate", BASE + "/bwt/crossing/250602")
    run_dir = rb.write(SPECS[0]["answer"])
    after_db = make_after_db(tmp_path / "after_tamper_port.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_not_terminated_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "tamper_term", "CBP.gov--0")
    for pth in SPECS[0]["paths"]:
        rb.add_step("navigate", BASE + pth)
    run_dir = rb.write(SPECS[0]["answer"], terminated=False, reason="max_steps")
    after_db = make_after_db(tmp_path / "after_tamper_term.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_empty_answer_fails(tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / "tamper_empty", 0, answer="   ")
    after_db = make_after_db(tmp_path / "after_tamper_empty.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_corrupt_screenshot_fails(tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / "tamper_shot", 0)
    # overwrite one referenced screenshot with non-PNG bytes
    shots = sorted((run_dir / "screenshots").glob("step_*.png"))
    shots[1].write_bytes(b"not a png at all")
    after_db = make_after_db(tmp_path / "after_tamper_shot.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_missing_trajectory_fails(tmp_path, seed_db):
    run_dir = tmp_path / "tamper_no_traj"
    (run_dir / "screenshots").mkdir(parents=True)
    after_db = make_after_db(tmp_path / "after_tamper_no.db", 0)
    with pytest.raises(AssertionError):
        run_verifier(0, run_dir, seed_db, after_db)


# ---------------------------------------------------------------- seed gate
def test_pre_mutated_seed_fails(tmp_path, seed_db):
    """Grading against a pre-mutated initial DB (answer pre-written in the
    'seed') must fail-closed at the seed identity gate."""
    dirty_seed = shutil.copyfile(seed_db, tmp_path / "dirty_seed.db")
    db = sqlite3.connect(dirty_seed)
    db.execute("INSERT INTO esta_applications (application_number, user_id, "
               "family_name, first_name, birth_date, gender, citizenship, "
               "passport_number, passport_issue_country, passport_expiry, "
               "email, phone, address_city, address_country, travel_purpose, "
               "destination_address, status, fee_usd, created_at, expires_on) "
               "VALUES ('ESTA-FAKE0001', NULL, 'Doe', 'Jane', '1990-01-01', "
               "'Female', 'Germany', 'DE1', 'Germany', '2030-01-01', "
               "'j@x.com', '+1', 'Berlin', 'Germany', 'Tourism', 'x', "
               "'Authorization Approved', 40.27, '2026-09-28', '2028-09-28')")
    db.commit()
    db.close()
    run_dir = build_honest_run(tmp_path / "premut_4", 4)
    after_db = shutil.copyfile(dirty_seed, tmp_path / "after_premut_4.db")
    verdict = run_verifier(4, run_dir, dirty_seed, after_db)
    assert not verdict["pass"], "pre-mutated seed must fail-closed"


# ------------------------------------------------- T15: wrong-crossing answer
def test_t15_wrong_crossing_answer_fails(tmp_path, seed_db):
    """F-6 fixed: Dana's saved crossing is now 250601 Otay Mesa - Passenger
    with live 185/120 delays. Reporting the OLD seed state (the first Otay
    Mesa record, all lanes Update Pending) as the saved crossing is a
    factually wrong answer -> FAIL."""
    run_dir = build_honest_run(
        tmp_path / "t15_wrong", 15,
        answer=("Saved crossing Otay Mesa - : standard passenger delay Update "
                "Pending, Ready Lane delay Update Pending. Saved job Border "
                "Patrol Agent: salary $51,632 - $92,912, closing 09/30/2026. "
                "Trusted Traveler application GE-77554402 (Global Entry), status "
                "Interview Scheduled, interview 2026-10-14 at 10:00 a.m. at "
                "Los Angeles International Airport (LAX); the enrollment "
                "center's hours are 7:30 a.m. - 9:30 p.m., contact phone "
                "(310) 642-1425."))
    after_db = make_after_db(tmp_path / "after_t15_wrong.db", 15)
    verdict = run_verifier(15, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong-crossing T15 answer must FAIL"


# ------------------------------------------------- tasks.jsonl contract shape
def test_tasks_jsonl_contract(tmp_path, seed_db):
    """The 7-key rows must carry the contribution's 5-key prefix byte-identical
    (frozen against 78dae408) and contain no answer key."""
    import subprocess
    here = Path(__file__).resolve()
    repo = here.parents[4]  # .../orch/review/build/u_s_customs
    cur = (repo / "sites/u_s_customs/tasks.jsonl").read_text(encoding="utf-8").splitlines()
    orig = subprocess.run(["git", "show", "78dae408:sites/u_s_customs/tasks.jsonl"],
                          capture_output=True, text=True, cwd=repo).stdout.splitlines()
    assert len(cur) == len(orig) == 21
    for new, old in zip(cur, orig):
        row = json.loads(new)
        assert sorted(row.keys()) == ["id", "judge_rubric", "ques", "upstream_url",
                                      "verifier_path", "web", "web_name"], row["id"]
        assert "answer" not in row
        # The integrate branch performs the sanctioned port re-base
        # (registration slot 162): the 5-key prefix must stay byte-identical
        # EXCEPT the web field's port (40100 -> 40162).
        import re as _re
        def _rebased(line):
            return _re.sub(r"http://localhost:40\d+/",
                           "http://localhost:PORT/", line)
        assert _rebased(new).startswith(_rebased(old).rstrip()[:-1]), f"5-key prefix drift on {row['id']}"
        assert row["verifier_path"] == f"sites/u_s_customs/verify/verify_{int(row['id'].split('--')[1])}.py"
        rubric = row["judge_rubric"]
        assert rubric.startswith("FACT CHECKPOINTS")
        # rubric is English pure rules: ASCII-letter-dominant, no CJK leakage
        letters = [c for c in rubric if c.isalpha()]
        assert letters and all(ord(c) < 0x3000 for c in letters)
