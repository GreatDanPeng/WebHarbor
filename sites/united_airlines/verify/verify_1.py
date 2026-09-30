#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--1 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_1.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--1"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: CMX-ORD round-trip search, both selections, booking chain.
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=CMX.*?destination=ORD.*?depart=2026-10-14')
    check_visited_path(judge, traj, "nav_return", r'/flights/select-return\?origin=ORD&destination=CMX|/flights/search\?.*?origin=ORD.*?destination=CMX.*?depart=2026-10-21')
    check_visited_path(judge, traj, "nav_passengers", r'/booking/passengers')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    check_answer_phrase(judge, answer, "outbound_flight", "5131")
    check_answer_phrase(judge, answer, "return_flight", "6067")
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_money(judge, answer, "total_charged", 273.90)
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", None,
                      "dana.reyes@example.com", None, "ECO", 1, 0, 0, 0,
                      "7890", "Mastercard", 273.9, "confirmed", None, None,
                      None, None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 3, "2026-10-14", "ECO", 138.95],
                     [None, 5, 28, "2026-10-21", "ECO", 134.95]], "leg_rows")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Dana", "Reyes", None, None, None, None,
                      None, None, None]], "pax_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
