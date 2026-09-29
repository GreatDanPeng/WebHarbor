#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--10 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_10.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_phrase, check_read_only, check_rows_added,
    check_rows_changed, check_only_tables_changed, check_screenshots,
    check_seed_contract, check_trajectory_identity, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "United Airlines--10"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: ZW57PC lookup, cancel flow, Basic Economy change policy page.
    check_visited_path(judge, traj, "nav_mytrips", r'/mytrips')
    check_visited_path(judge, traj, "nav_trip", r'/mytrips/ZW57PC')
    check_visited_path(judge, traj, "nav_cancel", r'/mytrips/ZW57PC/cancel')
    check_visited_path(judge, traj, "nav_policy", r'/travel-info/policies/flight-change')
    # answer ground truth: Basic Economy cannot be changed; the canceled value
    # stays as a future flight credit (ticket $198.08; cash refund $0).
    ok_change = ("cannot be changed" in answer.lower()) or \
                 ("not changeable" in answer.lower()) or \
                 ("can't be changed" in answer.lower()) or \
                 ("cannot change" in answer.lower())
    if ok_change:
        judge.ok("be_change_rule", "Basic Economy cannot be changed")
    else:
        judge.fail("be_change_rule", "answer must state Basic Economy cannot be changed")
    check_answer_phrase(judge, answer, "value_outcome", "credit")
    check_answer_money(judge, answer, "ticket_value", 198.08)
    check_only_tables_changed(judge, initial, after, {"bookings"})
    check_rows_changed(judge, initial, after, "bookings",
                       [[None, "ZW57PC", 3, "carol.w@example.com", None, "BE",
                         1, 0, 0, 0, "4242", "Visa", 198.08, "canceled",
                         None, 0.0, "travel credit", None]],
                       "cancel_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
