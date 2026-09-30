#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--20 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_20.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--20"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: change policy page, ORD-AUS booking chain, cancel flow.
    check_visited_path(judge, traj, "nav_policy", r'/travel-info/policies/flight-change')
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=ORD.*?destination=AUS.*?depart=2026-10-21')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    check_visited_path(judge, traj, "nav_cancel", r'/cancel')
    # answer ground truth: no change fee on standard United Economy (fare
    # difference only); Basic Economy is not changeable; ORD-AUS ECO $234.95
    # charged then fully refunded to the original payment method.
    ok_fee = ("no change fee" in answer.lower()) or ("$0" in answer) or \
             ("0 change fee" in answer)
    if ok_fee:
        judge.ok("standard_change_fee", "no change fee")
    else:
        judge.fail("standard_change_fee", "answer must state the no-change-fee rule")
    ok_be = ("basic economy" in answer.lower()) and \
            (("not changeable" in answer.lower()) or \
             ("cannot be changed" in answer.lower()) or \
             ("can't be changed" in answer.lower()))
    if ok_be:
        judge.ok("be_rule", "Basic Economy not changeable")
    else:
        judge.fail("be_rule", "answer lacks the Basic Economy rule")
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_money(judge, answer, "total_charged", 234.95)
    check_answer_money(judge, answer, "refund_amount", 234.95)
    check_answer_any(judge, answer, "refund_destination",
                    ["original payment method", "card", "visa"])
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", None,
                      "sam.ortiz@example.com", None, "ECO", 1, 0, 0, 0,
                      "4242", "Visa", 234.95, "canceled", None, 234.95,
                      "card", None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 48, "2026-10-21", "ECO", 234.95]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Sam", "Ortiz", None, None, None, None,
                      None, None, None]], "pax_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
