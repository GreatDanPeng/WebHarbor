#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--18 (wanderlog).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-wanderlog-review, seed md5
b32e9905a17605ce9c983780764c9ee4) — never read from tasks.jsonl.
Usage: python3 verify_18.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--18"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: login as bob, the shared trip, add-a-place search
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_plan", r"/plan/parisinspring")
    check_visited_path(judge, traj, "nav_add_place", r"/plan/parisinspring/add")
    # answer ground truth
    check_answer_phrase(judge, answer, "day_card", "Day 3 · Apr 12")
    check_answer_phrase(judge, answer, "new_stop", "Breizh Café")
    check_answer_phrase(judge, answer, "start_time", "09:00")
    check_answer_number(judge, answer, "duration", 60)
    check_answer_phrase(judge, answer, "note", "Buckwheat crêpes for breakfast")
    check_answer_number(judge, answer, "d3_stops_after", 4)
    check_answer_number(judge, answer, "packing_done", 3)
    check_answer_number(judge, answer, "packing_total", 5)
    # DB contract: exactly one new Day 3 stop added by the collaborator
    check_only_tables_changed(judge, initial, after, {"trips", "trip_entries"})
    check_rows_added(judge, initial, after, "trip_entries",
                     [(None, 3, 52, "Buckwheat crêpes for breakfast", "09:00", 60, 4, 18)],
                     "db_entry_added")
    check_rows_changed(judge, initial, after, "trips",
                       [(1, "parisinspring", "parisinspringv", "Paris in the Spring",
                         17, 9614, "2027-04-10", "2027-04-13", 2, "USD", "link",
                         "2026-09-12", "2026-09-29")],
                       "db_trip_touched")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
