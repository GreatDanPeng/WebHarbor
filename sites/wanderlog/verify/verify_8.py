#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--8 (wanderlog).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-wanderlog-review, seed md5
b32e9905a17605ce9c983780764c9ee4) — never read from tasks.jsonl.
Usage: python3 verify_8.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_number_absent,
    check_answer_ordered, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Wanderlog--8"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: alice invites from the planner; carol accepts from her trips page
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_plan", r"/plan/parisinspring")
    check_visited_path(judge, traj, "nav_plans", r"/plans")
    # answer ground truth
    check_answer_phrase(judge, answer, "invite_msg", "Invitation sent to Carol Davis.")
    check_answer_phrase(judge, answer, "d2_first", "Louvre Museum")
    check_answer_phrase(judge, answer, "d2_time", "09:30")
    check_answer_phrase(judge, answer, "owner", "Alice Johnson")
    # DB contract: exactly one accepted collaborator row added
    check_only_tables_changed(judge, initial, after, {"trip_collaborators"})
    check_rows_added(judge, initial, after, "trip_collaborators",
                     [(None, 1, 19, "carol.d@test.com", "editor", "accepted", "2026-09-29")],
                     "db_collab_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
