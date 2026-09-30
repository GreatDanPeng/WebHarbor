#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--13 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_13.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--13"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: MileagePlus join, SFO-PDX Oct 9 booking chain.
    check_visited_path(judge, traj, "nav_join", r'/mileageplus/join')
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=SFO.*?destination=PDX.*?depart=2026-10-09')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    # answer ground truth: deterministic MileagePlus number (sha256 of the
    # join email), ECO $172.95, 865 award miles credited (5 miles/$, Member).
    check_answer_number(judge, answer, "mp_number", "1759967178")
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_number(judge, answer, "miles_credited", 865)
    check_only_tables_changed(judge, initial, after,
                             {"users", "activities", "bookings",
                              "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "users",
                    [[5, "frank.lee@example.com", None, "Frank", "Lee",
                      "1759967178", 865, 1, 173, "Member", None, None,
                      None, None]], "user_row")
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", 5,
                      "frank.lee@example.com", None, "ECO", 1, 0, 0, 0,
                      "4242", "Visa", 172.95, "confirmed", None, None, None,
                      None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 43, "2026-10-09", "ECO", 172.95]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Frank", "Lee", None, None, None,
                      "1759967178", None, None, None]], "pax_row")
    check_rows_added(judge, initial, after, "activities",
                    [[None, 5, None, "rx:^Flight credit", "United", 865, 173]],
                    "activity_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
