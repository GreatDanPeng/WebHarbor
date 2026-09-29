"""Deterministic verifier contract tests for the 20 the_weather_network tasks.

Covers, per task: the honest trajectory (from the reviewer's live walks,
frozen in fixtures_data.SPECS) MUST PASS; a no-op run (homepage only, empty
answer, clean DB) MUST FAIL; a knowledge-shortcut (correct answer + delta,
homepage-only navigation) MUST FAIL; a wrong answer MUST FAIL; a
state-mismatch (success claim, no DB delta) MUST FAIL for stateful tasks.
Every task MUST FAIL on a mutated after-DB (a non-allowed table touched).
Package tampering (task_id mismatch, off-site URL, missing screenshot,
non-done trajectory, undecodable screenshot) MUST fail closed.

No LLM: snapshots are seed copies mutated through sqlite, trajectories are
written in the agent_demo/agent.py shape.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from _support import (RunBuilder, acquire_seed, build_run, copy_db,  # noqa: E402
                       exec_sql, honest_run, noop_run, run_verifier,
                       shortcut_run, state_mismatch_run, task_ques,
                       wrong_answer_run)
from fixtures_data import SPECS, WRONG_ANSWERS  # noqa: E402

STATEFUL = {5, 14}
ALL = list(range(20))


# ---------------------------------------------------------------- happy path
@pytest.mark.parametrize("task_no", ALL)
def test_honest_run_passes(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    run_verifier(task_no, run, expect_pass=True)


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
    """Touching a table outside the task's allowed delta must FAIL."""
    run = build_run(tmp_path, task_no, apply_sql=True,
                     mutate_after_sql="INSERT INTO alerts (placecode, location_name, "
                     "region, name, condition, type, priority, status, treatment, "
                     "source_text, issued, expires, updated, message, recommended, related) "
                     "VALUES ('W_FAKE00001', 'Fakeville', 'Alberta', 'Fake Alert', 'frost', "
                     "'advisory', 'minor', 'active', 'N/A', 'fake', '2026-09-26T15:00:00', "
                     "'2026-09-27T07:00:00', '2026-09-26T15:00:00', 'fake', 'fake', '');")
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- package tampering fails closed
@pytest.mark.parametrize("task_no", ALL)
def test_task_id_mismatch_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    traj = json.loads((run / "trajectory.json").read_text())
    traj["task_id"] = "Some Other Site--1"
    (run / "trajectory.json").write_text(json.dumps(traj))
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL)
def test_offsite_url_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    traj = json.loads((run / "trajectory.json").read_text())
    traj["steps"][0]["url_after"] = "https://example.com/en"
    (run / "trajectory.json").write_text(json.dumps(traj))
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL)
def test_missing_screenshot_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    for png in sorted((run / "screenshots").glob("step_*.png"))[1:]:
        png.unlink()
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL)
def test_not_done_trajectory_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    traj = json.loads((run / "trajectory.json").read_text())
    traj["terminated"] = False
    traj["termination_reason"] = None
    (run / "trajectory.json").write_text(json.dumps(traj))
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL)
def test_undecodable_screenshot_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    first = sorted((run / "screenshots").glob("step_*.png"))[0]
    first.write_bytes(b"\x89PNG\r\n\x1a\n" + b"garbage" * 10)
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL)
def test_empty_answer_fails(tmp_path, task_no):
    run = wrong_answer_run(tmp_path, task_no, "")
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- tasks.jsonl contract
REPO = Path(__file__).resolve().parents[4]  # wh-twn-review-wt (repo root)


def test_tasks_jsonl_seven_keys_no_answer():
    """Every row: 7 keys, no answer key, verifier_path + judge_rubric present."""
    rows = [json.loads(l) for l in
            (REPO / "sites/the_weather_network/tasks.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 20
    for row in rows:
        assert sorted(row.keys()) == ["id", "judge_rubric", "ques", "upstream_url",
                                      "verifier_path", "web", "web_name"], row.keys()
        assert "answer" not in row
        assert row["verifier_path"].startswith("sites/the_weather_network/verify/verify_")
        assert (REPO / row["verifier_path"]).is_file(), row["verifier_path"]
        assert row["judge_rubric"].strip().upper().startswith("FACT CHECKPOINTS")
        assert row["web_name"] == "The Weather Network"


def test_five_key_prefix_is_byte_identical_to_contribution():
    """The 5-key prefix of every tasks.jsonl row must be byte-identical to the
    contributor's rows at the reviewed fix commit (2d15effd, r3) - the reviewer
    only appends verifier_path+judge_rubric (re-synced in r2/r3 onto the new
    prefix). The one sanctioned exception is the `web` port: the audit-phase
    slot normalization moves it to the site's assigned merge port (40143; the
    slot formula index = registered sites on main (99) + 44)."""
    import subprocess
    contrib = subprocess.run(
        ["git", "-C", str(REPO), "show", "2d15effd:sites/the_weather_network/tasks.jsonl"],
        capture_output=True, text=True)
    if contrib.returncode != 0:
        pytest.skip("contribution commit not available on this machine")
    theirs = contrib.stdout.splitlines()
    mine = (REPO / "sites/the_weather_network/tasks.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(mine) == len(theirs) == 20
    old_web, new_web = '"web": "http://localhost:40099/"', '"web": "http://localhost:40143/"'
    for a, b in zip(mine, theirs):
        row_a, row_b = json.loads(a), json.loads(b)
        assert row_b["web"] == "http://localhost:40099/"
        assert row_a["web"] == "http://localhost:40143/"
        prefix_a = {k: row_a[k] for k in ("web_name", "id", "ques", "upstream_url")}
        prefix_b = {k: row_b[k] for k in ("web_name", "id", "ques", "upstream_url")}
        assert prefix_a == prefix_b, row_a["id"]
        # byte-prefix property modulo the port normalization:
        assert a.startswith(b[:-1].replace(old_web, new_web) + ", "), row_a["id"]


def test_word_count_within_100():
    rows = [json.loads(l) for l in
            (REPO / "sites/the_weather_network/tasks.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    for row in rows:
        n = len(row["ques"].split())
        assert 15 <= n <= 100, f"{row['id']} has {n} words"
