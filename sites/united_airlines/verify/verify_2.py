#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--2 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_2.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--2"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: sign-in -> award search SFO-ORD Oct 5 -> booking chain.
    check_visited_path(judge, traj, "nav_signin", r'/signin')
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=SFO.*?destination=ORD.*?depart=2026-10-05')
    check_visited_path(judge, traj, "nav_payment", r'/booking/payment')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    # answer ground truth: 42,595 miles redeemed (flight 45 ECO, 100 miles/$).
    check_answer_number(judge, answer, "miles_redeemed", 42595)
    check_answer_number(judge, answer, "balance_after", 25855)
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    # DB after-state: award booking on alice's account, miles deducted exactly once.
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers",
                              "users", "activities"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", 1,
                      "alice.j@example.com", None, "ECO", 1, 0, 1, 42595,
                      None, None, 0.0, "confirmed", None, None, None, None]],
                    "award_booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 45, "2026-10-05", "ECO", 421.69]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Alice", "Johnson", None, None, None,
                      "8511174410", None, None, None]], "pax_row")
    check_rows_changed(judge, initial, after, "users",
                       [[1, "alice.j@example.com", None, "Alice", "Johnson",
                         "8511174410", 25855, None, None, "Premier Silver",
                         None, None, None, None]],
                       "alice_miles_deducted")
    check_rows_added(judge, initial, after, "activities",
                    [[None, 1, None, "rx:^Award travel", "MileagePlus",
                      -42595, None]],
                    "activity_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
