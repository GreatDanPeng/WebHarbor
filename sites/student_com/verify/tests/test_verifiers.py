"""Deterministic verifier contract tests for the 21 student_com tasks.

Covers, per task: the honest trajectory (from the reviewer's live walks, frozen
in fixtures_data.SPECS) MUST PASS — except the three tasks BLOCKED by site
defects found during the review (16/18/20), whose honest runs MUST FAIL on the
documented blocked checks; a no-op run (homepage only, empty answer, clean DB)
MUST FAIL; a knowledge-shortcut (correct answer + delta, homepage-only
navigation) MUST FAIL; a wrong answer MUST FAIL; a state-mismatch (success
claim, no DB delta) MUST FAIL for stateful tasks. Every task MUST FAIL on a
mutated after-DB (a non-allowed table touched). Package tampering (task_id
mismatch, off-site URL, missing screenshot, non-done trajectory, undecodable
screenshot) MUST fail closed.

No LLM: snapshots are seed copies mutated through sqlite, trajectories are
written in the agent_demo/agent.py shape.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from _support import (BASE, RunBuilder, VERIFY_DIR, acquire_seed, copy_db,  # noqa: E402
                       exec_sql, honest_run, noop_run, run_verifier,
                       shortcut_run, state_mismatch_run, task_ques,
                       wrong_answer_run)
from fixtures_data import SPECS, WRONG_ANSWERS  # noqa: E402

# r2 (post-fix state, contribution @ 4f36ddd0): the three tasks the round-1
# review found BLOCKED by site defects (16/20 — the Retreat at Tampa page
# crashed with HTTP 500 on scalar room_details; 18 — the contact email was
# never rendered) are now SOLVABLE: the fixes landed in 6fc99228 and the
# honest fixtures pass their verifiers, so the blocked-task machinery is
# retired and every honest run must PASS.
BLOCKED: set[int] = set()
STATEFUL = {0, 2, 7, 11, 14, 20}
ALL = sorted(set(range(21)))


# ---------------------------------------------------------------- happy path
@pytest.mark.parametrize("task_no", [n for n in ALL if n not in BLOCKED])
def test_honest_run_passes(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    run_verifier(task_no, run, expect_pass=True)


def test_blocked_task_machinery_retired():
    """The round-1 blocked set (16/18/20) is empty at the post-fix state: the
    site defects were repaired in the contribution's 6fc99228 and all three
    tasks now pass their verifiers on honest runs (see test_honest_run_passes)."""
    assert BLOCKED == set()


@pytest.mark.parametrize("task_no", sorted(BLOCKED))
def test_blocked_task_honest_run_fails_on_documented_check(tmp_path, task_no):
    """Retained for provenance: parametrized over the (now empty) blocked set."""
    run = honest_run(tmp_path, task_no)
    verdict = run_verifier(task_no, run, expect_pass=False)
    assert "answer_" in verdict["reason"], verdict["reason"]


# ---------------------------------------------------------------- no-op fails
@pytest.mark.parametrize("task_no", ALL)
def test_noop_run_fails(tmp_path, task_no):
    run = noop_run(tmp_path, task_no)
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- shortcut fails
@pytest.mark.parametrize("task_no", ALL)
def test_shortcut_run_fails(tmp_path, task_no):
    run = shortcut_run(tmp_path, task_no)
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- wrong answers fail
@pytest.mark.parametrize("task_no", ALL)
def test_wrong_answer_fails(tmp_path, task_no):
    run = wrong_answer_run(tmp_path, task_no, WRONG_ANSWERS[task_no])
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- state mismatch fails
@pytest.mark.parametrize("task_no", sorted(STATEFUL))
def test_state_mismatch_fails(tmp_path, task_no):
    run = state_mismatch_run(tmp_path, task_no)
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- after-DB mutation fails
@pytest.mark.parametrize("task_no", ALL)
def test_after_db_mutation_fails(tmp_path, task_no):
    """Touching a table outside the task's allowed delta must FAIL (read-only
    contract for read-only tasks; exact-delta contract for stateful tasks)."""
    run = honest_run(tmp_path, task_no)
    db = sqlite3.connect(run / "after.db")
    db.execute("UPDATE properties SET name = name || ' tampered' WHERE id = 1")
    db.commit()
    db.close()
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- package tampering
@pytest.mark.parametrize("task_no", ALL)
def test_task_id_mismatch_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    traj = json.loads((run / "trajectory.json").read_text())
    traj["task_id"] = "Student.com--999"
    (run / "trajectory.json").write_text(json.dumps(traj))
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL)
def test_offsite_url_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    traj = json.loads((run / "trajectory.json").read_text())
    traj["steps"][0]["url_after"] = "https://example.org/"
    (run / "trajectory.json").write_text(json.dumps(traj))
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL)
def test_missing_screenshot_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    shots = sorted((run / "screenshots").glob("step_*.png"))
    shots[0].unlink()
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL)
def test_undecodable_screenshot_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    shots = sorted((run / "screenshots").glob("step_*.png"))
    shots[0].write_bytes(b"not a png at all")
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL)
def test_not_terminated_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    traj = json.loads((run / "trajectory.json").read_text())
    traj["terminated"] = False
    traj["termination_reason"] = None
    (run / "trajectory.json").write_text(json.dumps(traj))
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- seed contract
def test_seed_digests_match_frozen_contract():
    db_path = acquire_seed()
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    sys.path.insert(0, str(Path(__file__).parents[1]))
    import verify_lib
    assert verify_lib.schema_digest(db) == verify_lib.SCHEMA_SHA256
    assert verify_lib.rows_digest(db) == verify_lib.SEED_ROWS_SHA256
    counts = verify_lib.table_counts(db)
    assert counts == verify_lib.SEED_COUNTS


def test_tasks_jsonl_has_no_answer_key():
    for line in (Path(__file__).parents[2] / "tasks.jsonl").read_text().splitlines():
        row = json.loads(line)
        assert "answer" not in row
        assert "verifier_path" in row and "judge_rubric" in row
        assert set(row) == {"id", "ques", "upstream_url", "web", "web_name",
                            "verifier_path", "judge_rubric"}


def test_five_key_prefix_is_byte_identical_to_contribution():
    """The 5-key prefix of every tasks.jsonl row must be byte-identical to the
    contributor's rows at the reviewed fix commit (4f36ddd0) — the reviewer only
    appends verifier_path+judge_rubric (re-synced in r2 onto the new prefix).
    The one sanctioned exception is the `web` port: the audit-phase slot
    normalization moves it to the site's assigned merge port (40141; the slot
    formula index = registered sites on main (99) + 42)."""
    import subprocess
    wt = Path(__file__).resolve().parents[4]  # the worktree root
    contrib = subprocess.run(
        ["git", "show", "4f36ddd0:sites/student_com/tasks.jsonl"],
        cwd=wt, capture_output=True, text=True)
    if contrib.returncode != 0:
        pytest.skip("contribution commit not available on this machine")
    mine = (Path(__file__).parents[2] / "tasks.jsonl").read_text().splitlines()
    theirs = contrib.stdout.splitlines()
    assert len(mine) == len(theirs) == 21
    old_web, new_web = '"web": "http://localhost:40094/"', '"web": "http://localhost:40141/"'
    for a, b in zip(mine, theirs):
        row_a, row_b = json.loads(a), json.loads(b)
        assert row_b["web"] == "http://localhost:40094/"
        assert row_a["web"] == "http://localhost:40141/"
        prefix_a = {k: row_a[k] for k in ("web_name", "id", "ques", "upstream_url")}
        prefix_b = {k: row_b[k] for k in ("web_name", "id", "ques", "upstream_url")}
        assert prefix_a == prefix_b, row_a["id"]
        # byte-prefix property modulo the port normalization:
        assert a.startswith(b[:-1].replace(old_web, new_web) + ", "), row_a["id"]
