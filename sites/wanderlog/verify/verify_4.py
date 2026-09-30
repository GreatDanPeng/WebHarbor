#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--4 (wanderlog).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-wanderlog-review, seed md5
b32e9905a17605ce9c983780764c9ee4) — never read from tasks.jsonl.
Usage: python3 verify_4.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--4"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: login as alice, Tokyo Weekend planner, add-a-place search
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_plan", r"/plan/tokyowkend")
    check_visited_path(judge, traj, "nav_add_place", r"/plan/tokyowkend/add")
    # answer ground truth
    check_answer_phrase(judge, answer, "day_card", "Day 1 · Oct 17")
    check_answer_phrase(judge, answer, "new_stop", "Shinjuku Gyoen")
    check_answer_phrase(judge, answer, "start_time", "09:00")
    check_answer_number(judge, answer, "duration", 90)
    check_answer_phrase(judge, answer, "note", "Garden gates open at nine")
    check_answer_number(judge, answer, "d1_stops", 4)
    check_answer_any(judge, answer, "privacy", ["Public", "public"])
    # DB contract: exactly one new itinerary stop on Day 1, trip touched_at updated
    check_only_tables_changed(judge, initial, after, {"trips", "trip_entries"})
    check_rows_added(judge, initial, after, "trip_entries",
                     [(None, 5, 126, "Garden gates open at nine", "09:00", 90, 4, 17)],
                     "db_entry_added")
    check_rows_changed(judge, initial, after, "trips",
                       [(2, "tokyowkend", "tokyowkendv", "Tokyo Weekend", 17, 1,
                         "2026-10-17", "2026-10-18", 1, "USD", "public",
                         "2026-09-20", "2026-09-29")],
                       "db_trip_touched")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
