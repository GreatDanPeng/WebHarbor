#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--10 (wanderlog).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-wanderlog-review, seed md5
b32e9905a17605ce9c983780764c9ee4) — never read from tasks.jsonl.
Usage: python3 verify_10.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--10"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: plan-a-trip destination search, create, add a section
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_plan_new", r"/plan/new")
    check_visited_path(judge, traj, "nav_kyoto_pick", r"/plan/new\?[^ ]*geo_id=2")
    # answer ground truth
    check_answer_phrase(judge, answer, "sec1", "Day 1 · Nov 21")
    check_answer_phrase(judge, answer, "sec2", "Day 2 · Nov 22")
    check_answer_phrase(judge, answer, "new_section", "Day 3 · Fushimi Inari day trip")
    check_answer_number(judge, answer, "sections_after", 3)
    # DB contract: one new trip (deterministic keys) + its three sections
    check_only_tables_changed(judge, initial, after, {"trips", "trip_sections"})
    check_rows_added(judge, initial, after, "trips",
                     [(None, "rx:[0-9a-f]{10}", "rx:[0-9a-f]{10}", "Kyoto Temple Weekend",
                       20, 2, "2026-11-21", "2026-11-22", 2, "USD", "private",
                       "2026-09-29", "2026-09-29")],
                     "db_trip_added")
    check_rows_added(judge, initial, after, "trip_sections",
                     [(None, None, "Day 1 · Nov 21", 1, 1),
                      (None, None, "Day 2 · Nov 22", 2, 2),
                      (None, None, "Day 3 · Fushimi Inari day trip", 3, 3)],
                     "db_sections_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
