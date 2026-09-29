#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--0 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_0.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--0"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: home booking widget -> ORD-DEN search -> cheapest Economy -> booking chain.
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=ORD.*?destination=DEN.*?depart=2026-10-15')
    check_visited_path(judge, traj, "nav_passengers", r'/booking/passengers')
    check_visited_path(judge, traj, "nav_payment", r'/booking/payment')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    # answer ground truth (deterministic fares from the frozen seed):
    #   UA2803 ECO $210.95 / UA2790 ECO $202.95 / UA1974 ECO $226.95.
    check_answer_phrase(judge, answer, "cheapest_flight", "2790")
    check_answer_money(judge, answer, "cheapest_eco_fare", 202.95)
    # every Economy fare compared must be reported (three fares of that day).
    check_answer_count_at_least(judge, answer, "all_eco_fares_reported",
                                ["210.95", "202.95", "226.95"], 3)
    # confirmation number must match the booking persisted by the run.
    row = after.execute(
        "SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_money(judge, answer, "total_charged", 202.95)
    # DB after-state: exactly one new ECO booking ORD->DEN Oct 15 for Jordan Hayes.
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", None,
                      "jordan.hayes@example.com", None, "ECO", 1, 0, 0, 0,
                      "4242", "Visa", 202.95, "confirmed", None, None, None,
                      None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 10, "2026-10-15", "ECO", 202.95]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Jordan", "Hayes", None, None, None, None,
                      None, None, None]], "pax_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
