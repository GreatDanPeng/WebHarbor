#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--8 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_8.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--8"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: bob's trips, trip details, change flow for QT83NB.
    check_visited_path(judge, traj, "nav_mytrips", r'/mytrips')
    check_visited_path(judge, traj, "nav_trip", r'/mytrips/QT83NB')
    check_visited_path(judge, traj, "nav_change", r'/mytrips/QT83NB/change/2')
    # answer ground truth (deepened at 93a2638f to a before/after itinerary
    # comparison): original leg UA2803 departing 14:33 -> 16:31; latest
    # same-day ORD->DEN flight = UA1974 18:17 -> 20:22, fare difference
    # $19.84 (EPU $281.42 vs $261.58), no change fee.
    check_answer_phrase(judge, answer, "original_flight", "2803")
    check_answer_any(judge, answer, "original_departure", ["14:33"])
    check_answer_phrase(judge, answer, "new_flight", "1974")
    check_answer_any(judge, answer, "new_departure", ["18:17"])
    check_answer_money(judge, answer, "fare_difference", 19.84)
    ok_fee = ("no change fee" in answer.lower()) or ("$0" in answer) or ("0" in answer)
    if ok_fee:
        judge.ok("change_fee", "no change fee")
    else:
        judge.fail("change_fee", "answer must state no change fee / $0")
    check_only_tables_changed(judge, initial, after, {"bookings", "booking_legs"})
    check_rows_changed(judge, initial, after, "bookings",
                       [[None, "QT83NB", 2, "bob.m@example.com", None, "EPU",
                         1, 0, 0, 0, "4242", "Visa", 281.42, "confirmed",
                         None, None, None, None]],
                       "booking_total")
    check_rows_changed(judge, initial, after, "booking_legs",
                       [[2, 2, 11, "2026-09-28", "EPU", 281.42]], "leg_changed")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
