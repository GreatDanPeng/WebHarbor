#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--3 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_3.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--3"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: bob signs in, IAD-DEN Oct 8 Economy Plus search, booking chain.
    check_visited_path(judge, traj, "nav_signin", r'/signin')
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=IAD.*?destination=DEN.*?depart=2026-10-08')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    # answer ground truth: cheapest EPU = UA599 $325.61 (Premier Gold 0.98x).
    check_answer_phrase(judge, answer, "cheapest_flight", "599")
    check_answer_money(judge, answer, "total_charged", 325.61)
    check_answer_number(judge, answer, "miles_credited", 2605)
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers",
                              "users", "activities"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", 2,
                      "bob.m@example.com", None, "EPU", 1, 0, 0, 0,
                      "9010", "Visa", 325.61, "confirmed", None, None, None,
                      None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 14, "2026-10-08", "EPU", 325.61]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Robert", "Miller", None, None, None,
                      "5658356101", None, None, None]], "pax_row")
    check_rows_changed(judge, initial, after, "users",
                       [[2, "bob.m@example.com", None, "Bob", "Miller",
                         "5658356101", 145805, 32, 9506, "Premier Gold",
                         None, None, None, None]],
                       "bob_miles_credited")
    check_rows_added(judge, initial, after, "activities",
                    [[None, 2, None, "rx:^Flight credit", "United", 2605, 326]],
                    "activity_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
