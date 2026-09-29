#!/usr/bin/env python3
"""test_verifiers.py — adversarial contract tests for the verizon verifiers
(r3 re-review contract sync, orch/review/verizon on top of 77d56c1b).

Reviewer-track suite for the r3 round: the nine deepened tasks'
verifiers are the contributor's re-anchored ones (validated by the
reviewer's own two independent honest-walk rounds on an independent
container); the eleven unchanged verifiers are byte-identical to the
frozen r2 contract 77d56c1b. Every fixture here is the reviewer's OWN
honest walk (runs_r1 of wh-verizon-r3-rereview-evidence, reproduced
identically in runs_r2); every other case is adversarial and MUST FAIL
the corresponding verifier (zero false positives):

  A. honest fixtures ......... 20 reviewer strict-caliber walks -> PASS
  B. no-op runs .............. zero steps + canned answer -> FAIL
  C. answer-only shortcuts ... the fixture's own CORRECT final answer,
                               zero navigation -> FAIL
  D. wrong answers ........... honest navigation, every anchored fact
                               near-neighbor falsified -> FAIL
  E. stale/dirty DB .......... pre-mutated initial DB / dirty seed ->
                               FAIL
  F. read-only violations .... honest read-only walk + injected
                               appointment row -> FAIL
  G. tampered packages ....... wrong task_id / off-site URL / cross-port
                               URL / not terminated / empty answer /
                               corrupt screenshot / deleted navigation /
                               cross-fixture run -> FAIL
  H. state under-reach ....... stateful walk graded against an after DB
                               missing or corrupting the allowed delta ->
                               FAIL
"""
import json
import shutil
import sqlite3
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
EV = Path("/data/zhaoyang-user-projects/websyn/wh-verizon-audit-evidence")
# 2026-09-30 audit: the honest fixtures are the auditor's own click-only
# walks on the final rebuilt image (runs/0..19, 20/20 verifier PASS).
HONEST = EV / "runs"
SEED_REF = HONEST / "0" / "initial.db"  # frozen seed md5 f2d20153c24b6945fb5203b81d7f1fb6
PY = sys.executable

TASK_IDS = [f"Verizon--{n}" for n in range(20)]
# r3 stateful set: T19 checkout newly added
STATEFUL = [5, 8, 9, 10, 11, 13, 14, 19]
READ_ONLY = [0, 1, 2, 3, 4, 6, 7, 12, 15, 16, 17, 18]


def run_verifier(n, run_dir, extra=()):
    v = HERE / f"verify_{n}.py"
    out = subprocess.run([PY, str(v), "--run_dir", str(run_dir), *extra],
                         capture_output=True, text=True, timeout=180)
    try:
        payload = json.loads(out.stdout)
    except json.JSONDecodeError:
        payload = {"pass": False, "reason": out.stdout[-400:] + out.stderr[-400:]}
    return payload, out.returncode


def clone(run_src: Path, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(run_src, dest)
    return dest


def write_traj(run: Path, **over):
    traj = json.loads((run / "trajectory.json").read_text())
    traj.update(over)
    (run / "trajectory.json").write_text(json.dumps(traj))


def corrupt_png_bytes() -> bytes:
    return b"NOT-A-PNG-AT-ALL"


# ------------------------------------------------------------------ A. honest
@pytest.mark.parametrize("n", range(20))
def test_honest_fixture_passes(n):
    payload, code = run_verifier(n, HONEST / str(n))
    assert payload["pass"] is True, payload["reason"]
    assert code == 0


# ------------------------------------------------------------- B. no-op runs
@pytest.mark.parametrize("n", range(20))
def test_noop_run_fails(n, tmp_path):
    run = tmp_path / f"noop{n}"
    (run / "screenshots").mkdir(parents=True)
    (run / "initial.db").write_bytes(SEED_REF.read_bytes())
    (run / "after.db").write_bytes(SEED_REF.read_bytes())
    (run / "trajectory.json").write_text(json.dumps({
        "task_id": f"Verizon--{n}", "start_url": "http://127.0.0.1:46099/",
        "steps": [], "terminated": True, "termination_reason": "agent_done",
        "final_answer": "I know this from memory: the Simplicity Plan is $30 "
                        "per line and everything else follows.",
    }))
    payload, code = run_verifier(n, run)
    assert payload["pass"] is False
    assert code == 1


# ---------------------------------------------------- C. answer-only shortcut
@pytest.mark.parametrize("n", range(20))
def test_answer_only_shortcut_fails(n, tmp_path):
    fixture_answer = json.loads(
        (HONEST / str(n) / "trajectory.json").read_text())["final_answer"]
    run = tmp_path / f"shortcut{n}"
    (run / "screenshots").mkdir(parents=True)
    (run / "initial.db").write_bytes(SEED_REF.read_bytes())
    (run / "after.db").write_bytes(SEED_REF.read_bytes())
    (run / "trajectory.json").write_text(json.dumps({
        "task_id": f"Verizon--{n}", "start_url": "http://127.0.0.1:46099/",
        "steps": [], "terminated": True, "termination_reason": "agent_done",
        "final_answer": fixture_answer,
    }))
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False, "shortcut with no navigation must FAIL"


# ------------------------------------------------------------ D. wrong answers
SUBS = [("$1,199.99", "$1,189.99"), ("$30.00", "$31.00"), ("$120/month", "$121/month"),
        ("$80/mo", "$81/mo"), ("$13.88", "$14.88"), ("4.2 out of 5", "4.3 out of 5"),
        ("$300.00", "$301.00"), ("$240.00", "$241.00"), ("218.33", "218.34"),
        ("$45.00", "$46.00"), ("$160.00", "$161.00"), ("$50.00", "$51.00"),
        ("97.49", "97.50"), ("30 days", "31 days"), ("6.94", "6.95"),
        ("$2,099.99", "$2,089.99"), ("49.41", "49.42"), ("$699.99", "$689.99"),
        ("98.85", "98.86"), ("$24.99/mo", "$25.99/mo"), ("$760.00", "$761.00"),
        ("71.99", "71.98"), ("$36.11", "$36.12"), ("$1,299.99", "$1,289.99"),
        ("54.77", "54.78"), ("Wed, Sep 30 - Fri, Oct 9", "Wed, Sep 30 - Fri, Oct 10"),
        ("$370.00", "$371.00"), ("$190.00", "$191.00"), ("48.74", "48.75"),
        ("$130.00", "$131.00"), ("$140.00", "$141.00"), ("$540.00", "$541.00"),
        ("$650.00", "$651.00"), ("$160.62", "$160.63"), ("$118.17", "$118.18"),
        ("$176.46", "$176.47"), ("$210.00", "$211.00"), ("22.1 GB", "22.2 GB"),
        ("31.4 GB", "31.5 GB"), ("$70.00", "$71.00"), ("2.7 GB", "2.8 GB"),
        ("18.9 GB", "18.8 GB"), ("$60/month", "$61/month"), ("$90/month", "$91/month"),
        ("$610.00", "$611.00"), ("$114.08", "$114.09"), ("$249.99", "$248.99"),
        ("$36.94", "$36.95"), ("55 stores", "54 stores"), ("6 stores", "7 stores"),
        ("2 stores", "3 stores"), ("3 stores", "4 stores"),
        ("4009 Tacoma Mall Blvd", "4010 Tacoma Mall Blvd"),
        ("10:00 AM 06:00 PM", "10:00 AM 07:00 PM"), ("$33.33", "$33.34"),
        ("Up to 34 hours", "Up to 35 hours"), ("3.8 out of 5", "3.9 out of 5"),
        ("Up to 24 hours", "Up to 25 hours"), ("$79.99/mo", "$79.98/mo"),
        ("$84.16/mo", "$84.15/mo"), ("Monthly total: $164.15", "Monthly total: $164.16"),
        ("$730.00", "$731.00"), ("$55.00", "$56.00"), ("$330.00", "$331.00"),
        ("$100.00", "$101.00"), ("70.41", "70.42"), ("$70.41", "$70.42"),
        ("$10/mo", "$11/mo"), ("$35.00/mo", "$36.00/mo"), ("$60.00/mo", "$61.00/mo"),
        ("800-225-5499", "800-225-5498"), ("800-922-0204", "800-922-0205"),
        ("$120.00", "$121.00"), ("146.99", "146.98")]


def falsify(answer, seed_):
    """Bump the DOLLAR part of every money token (the frozen lib's money gate
    deliberately tolerates cent-level renderings, so a cent-only bump is not
    an effective falsification) and flip the anchored phrases/numbers."""
    import random
    import re as _re
    out = _re.sub(r"\$(\d+)", lambda m: "$" + str(int(m.group(1)) + 1), answer)
    for a, b in SUBS:
        if a in out:
            out = out.replace(a, b)
    return out


@pytest.mark.parametrize("n", range(20))
def test_wrong_answer_fails(n, tmp_path):
    run = clone(HONEST / str(n), tmp_path / f"wrong{n}")
    ans = json.loads((run / "trajectory.json").read_text())["final_answer"]
    write_traj(run, final_answer=falsify(ans, n))
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False, "falsified anchors must FAIL"


# ----------------------------------------------------------------- E. stale DB
@pytest.mark.parametrize("n", [9, 10, 13, 14, 19])
def test_stale_db_fails(n, tmp_path):
    """Honest run graded against an initial DB that already contains the
    state mutation (stale seed) -> FAIL."""
    run = clone(HONEST / str(n), tmp_path / f"stale{n}")
    shutil.copyfile(run / "after.db", run / "initial.db")
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


@pytest.mark.parametrize("n", [2, 15])
def test_dirty_seed_fails(n, tmp_path):
    """Read-only run graded against a pre-mutated (dirty) initial DB -> FAIL."""
    run = clone(HONEST / str(n), tmp_path / f"dirty{n}")
    con = sqlite3.connect(run / "initial.db")
    con.execute("INSERT INTO appointments (store_id, user_id, name, email, phone, "
                "topic, appt_date, appt_time, confirmation, status) VALUES "
                "(1, NULL, 'X', 'x@x.com', '123', 'Billing', '2026-10-01', "
                "'09:00 AM', 'APT999999', 'confirmed')")
    con.commit()
    con.close()
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


# --------------------------------------------------- F. read-only violations
@pytest.mark.parametrize("n", READ_ONLY)
def test_readonly_violation_fails(n, tmp_path):
    run = clone(HONEST / str(n), tmp_path / f"roviol{n}")
    con = sqlite3.connect(run / "after.db")
    con.execute("INSERT INTO appointments (store_id, user_id, name, email, phone, "
                "topic, appt_date, appt_time, confirmation, status) VALUES "
                "(1, NULL, 'Rogue', 'r@r.com', '555', 'Billing', '2026-10-02', "
                "'10:00 AM', 'APT777777', 'confirmed')")
    con.commit()
    con.close()
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


# -------------------------------------------------------- G. tampered packages
@pytest.mark.parametrize("n", [0, 2, 7, 9, 19])
def test_wrong_task_id_fails(n, tmp_path):
    run = clone(HONEST / str(n), tmp_path / f"tid{n}")
    write_traj(run, task_id=f"Verizon--{(n + 1) % 20}")
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


@pytest.mark.parametrize("n", [0, 2, 7, 9, 19])
def test_offsite_url_fails(n, tmp_path):
    run = clone(HONEST / str(n), tmp_path / f"offsite{n}")
    traj = json.loads((run / "trajectory.json").read_text())
    traj["steps"][0]["url"] = "https://example.com/evil"
    traj["steps"][0]["url_after"] = "https://example.com/evil"
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


@pytest.mark.parametrize("n", [0, 2, 7, 9, 19])
def test_cross_port_url_fails(n, tmp_path):
    run = clone(HONEST / str(n), tmp_path / f"xport{n}")
    traj = json.loads((run / "trajectory.json").read_text())
    traj["steps"][0]["url"] = "http://127.0.0.1:46098/"
    traj["steps"][0]["url_after"] = "http://127.0.0.1:46098/"
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


@pytest.mark.parametrize("n", [0, 2, 7, 9, 19])
def test_not_terminated_fails(n, tmp_path):
    run = clone(HONEST / str(n), tmp_path / f"noterm{n}")
    write_traj(run, terminated=False, termination_reason="max_steps")
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


@pytest.mark.parametrize("n", [0, 2, 7, 9, 19])
def test_empty_answer_fails(n, tmp_path):
    run = clone(HONEST / str(n), tmp_path / f"emptyans{n}")
    write_traj(run, final_answer="")
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


@pytest.mark.parametrize("n", [0, 2, 7, 9, 19])
def test_corrupt_screenshot_fails(n, tmp_path):
    run = clone(HONEST / str(n), tmp_path / f"badpng{n}")
    for shot in (run / "screenshots").glob("step_*.png"):
        shot.write_bytes(corrupt_png_bytes())
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


@pytest.mark.parametrize("n", [0, 2, 7, 9, 19])
def test_deleted_navigation_fails(n, tmp_path):
    run = clone(HONEST / str(n), tmp_path / f"delnav{n}")
    traj = json.loads((run / "trajectory.json").read_text())
    keep = max(2, len(traj["steps"]) // 5)
    traj["steps"] = traj["steps"][:keep]
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


@pytest.mark.parametrize("n", [0, 2, 7, 9, 19])
def test_cross_fixture_fails(n, tmp_path):
    """Verifier for task (n+1)%20 against task n's honest run -> FAIL."""
    payload, _ = run_verifier((n + 1) % 20, HONEST / str(n))
    assert payload["pass"] is False


# ------------------------------------------------------- H. state under-reach
def _strip_table(run: Path, table: str):
    con = sqlite3.connect(run / "after.db")
    con.execute(f"DELETE FROM {table}")
    con.commit()
    con.close()


def test_t19_missing_order_row_fails(tmp_path):
    run = clone(HONEST / "19", tmp_path / "u19a")
    _strip_table(run, "orders")
    payload, _ = run_verifier(19, run)
    assert payload["pass"] is False


def test_t19_wrong_shipping_city_fails(tmp_path):
    run = clone(HONEST / "19", tmp_path / "u19b")
    con = sqlite3.connect(run / "after.db")
    con.execute("UPDATE orders SET city='Spokane' WHERE name='Rosa Diaz'")
    con.commit()
    con.close()
    payload, _ = run_verifier(19, run)
    assert payload["pass"] is False


def test_t9_missing_payment_row_fails(tmp_path):
    run = clone(HONEST / "9", tmp_path / "u9a")
    _strip_table(run, "payments")
    payload, _ = run_verifier(9, run)
    assert payload["pass"] is False


def test_t14_missing_line_row_fails(tmp_path):
    run = clone(HONEST / "14", tmp_path / "u14a")
    _strip_table(run, "lines")
    payload, _ = run_verifier(14, run)
    assert payload["pass"] is False


def test_t8_missing_appointment_row_fails(tmp_path):
    run = clone(HONEST / "8", tmp_path / "u8a")
    _strip_table(run, "appointments")
    payload, _ = run_verifier(8, run)
    assert payload["pass"] is False


def test_t11_flags_not_written_fails(tmp_path):
    run = clone(HONEST / "11", tmp_path / "u11a")
    con = sqlite3.connect(run / "after.db")
    con.execute("UPDATE users SET autopay=0, paper_free=0 "
                "WHERE email='carol.d@test.com'")
    con.commit()
    con.close()
    payload, _ = run_verifier(11, run)
    assert payload["pass"] is False


def test_t13_plan_change_not_persisted_fails(tmp_path):
    run = clone(HONEST / "13", tmp_path / "u13a")
    con = sqlite3.connect(run / "after.db")
    con.execute("UPDATE lines SET plan_id=(SELECT id FROM plans WHERE "
                "name='Unlimited Plus') WHERE nickname='Dana'")
    con.commit()
    con.close()
    payload, _ = run_verifier(13, run)
    assert payload["pass"] is False


# --------------------------------------- audit-rail hardening pins (2026-09-30)
# The 2026-09-30 audit hardened three pre-existing low-severity gates that the
# r3 re-review documented: the PNG gate now requires a complete, decodable
# image (magic + IHDR + IEND + dimensions, so truncation fails), the money
# gate rejects cent-level drift while still accepting numerically equal and
# punctuation-adjacent honest forms, and verify_9's July anchor now requires
# the protection charge to be tied to July. These tests pin all three.


@pytest.mark.parametrize("n", [0, 9, 19])
def test_truncated_screenshot_fails(n, tmp_path):
    """A PNG truncated past the magic (signature intact, no IEND trailer,
    no pixel payload) must FAIL the screenshot gate."""
    run = clone(HONEST / str(n), tmp_path / f"trunc{n}")
    for shot in (run / "screenshots").glob("step_*.png"):
        data = shot.read_bytes()
        shot.write_bytes(data[: max(8, len(data) // 3)])
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


@pytest.mark.parametrize("n", [0, 9, 19])
def test_magic_only_png_stub_fails(n, tmp_path):
    """An 8-byte magic followed by junk (no IHDR/IEND structure) must FAIL."""
    run = clone(HONEST / str(n), tmp_path / f"stub{n}")
    for shot in (run / "screenshots").glob("step_*.png"):
        shot.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 40)
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False


def test_t9_cent_drift_answer_fails(tmp_path):
    """$160.63 reported for the $160.62 bill total must FAIL (the old pat3
    tolerated cent-level drift)."""
    run = clone(HONEST / "9", tmp_path / "drift9")
    traj = json.loads((run / "trajectory.json").read_text())
    traj["final_answer"] = traj["final_answer"].replace("160.62", "160.63")
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(9, run)
    assert payload["pass"] is False


def test_t10_cent_drift_answer_fails(tmp_path):
    """$118.18 reported for the $118.17 bill total must FAIL."""
    run = clone(HONEST / "10", tmp_path / "drift10")
    traj = json.loads((run / "trajectory.json").read_text())
    traj["final_answer"] = traj["final_answer"].replace("118.17", "118.18")
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(10, run)
    assert payload["pass"] is False


def test_money_gate_forms():
    """Pin the money gate's honest-form acceptance and drift rejection."""
    import verify_lib as vl

    class _J:
        def __init__(self):
            self.passed = None

        def ok(self, check, note):
            self.passed = True

        def fail(self, check, note):
            self.passed = False

    def money(answer, amount):
        j = _J()
        vl.check_answer_money(j, answer, "m", amount)
        return j.passed

    honest = [("$160.62", 160.62), ("total of $160.62.", 160.62),
              ("$160.62, taxes", 160.62), ("31.4 GB", 31.40),
              ("31.40 GB", 31.40), ("$1,199.99", 1199.99),
              ("about $1,199", 1199.99), ("$1,199.", 1199.99),
              ("worth $300.00.", 300.00), ("Good $330.00, Cracked", 330.00),
              ("$50", 50.00), ("$370.00", 370.00), ("$2,099.99", 2099.99),
              ("$70.00/mo", 70.00), ("$118.17.", 118.17)]
    drift = [("$160.63", 160.62), ("$160.6", 160.62), ("$160.00", 160.62),
             ("$1,199.98", 1199.99), ("$1,199.9", 1199.99), ("$49.99", 50.00),
             ("$164.16", 164.15), ("31.44 GB", 31.40), ("$330.05", 330.00)]
    boundary = [("$1,300 for it", 300.00), ("$1300 total", 300.00),
                ("300,000 miles", 300.00), ("$300.5", 300.00),
                ("21,199 things", 1199.99)]
    for answer, amount in honest:
        assert money(answer, amount), (answer, amount)
    for answer, amount in drift + boundary:
        assert not money(answer, amount), (answer, amount)


def test_t9_july_anchor_strengthened():
    """An answer that mentions July but never ties the protection charge to
    it must FAIL the jul_protection anchor."""
    import re
    src = (HERE / "verify_9.py").read_text()
    assert re.search(r'jul_protection",\s*\n?\s*r"Jul\(y\)?\[\^\.\]',
                     src) or "protection[^.]{0,200}Jul" in src
