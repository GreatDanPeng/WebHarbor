#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--9 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_9.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--9"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: DEN-SLC Oct 16 booking chain, then My Trips cancel flow.
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=DEN.*?destination=SLC.*?depart=2026-10-16')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    check_visited_path(judge, traj, "nav_trip", r'/mytrips/')
    check_visited_path(judge, traj, "nav_cancel", r'/cancel')
    # answer ground truth: ECO $131.95 charged, full refund $131.95 to the
    # original payment method (Visa ...4242).
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_money(judge, answer, "total_paid", 131.95)
    check_answer_money(judge, answer, "refund_amount", 131.95)
    check_answer_any(judge, answer, "refund_destination",
                    ["original payment method", "card", "visa"])
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", None,
                      "casey.kim@example.com", None, "ECO", 1, 0, 0, 0,
                      "4242", "Visa", 131.95, "canceled", None, 131.95,
                      "card", None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 39, "2026-10-16", "ECO", 131.95]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Casey", "Kim", None, None, None, None,
                      None, None, None]], "pax_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
