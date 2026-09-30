#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--4 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_4.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_answer_regex, check_attributed_money, check_only_tables_changed,
    check_read_only, check_rows_added, check_screenshots,
    check_seed_contract, check_section_phrase, check_trajectory_identity,
    check_visited_any, check_visited_path, final_answer, run_verifier,
)

TASK_ID = "USPS.com--4"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_account", r"/account(?!/)")
    check_visited_path(judge, traj, "nav_track_003", r"/tracking/9405500000000000000003")
    check_visited_path(judge, traj, "nav_informed", r"/account/informed-delivery")
    check_answer_phrase(judge, answer, "tracking_number",
                        "9405500000000000000003")
    check_answer_phrase(judge, answer, "status", "In Transit")
    check_answer_phrase(judge, answer, "expected", "September 30, 2026")
    check_answer_any(judge, answer, "latest_scan", [
        "DENVER, CO", "2026-09-26 12:00"])
    check_answer_number(judge, answer, "informed_pieces", 3)
    # premise fix (reviewer F-6): the task now says "today's bill and its
    # mail category" — bob's feed has exactly one Bill/Statement piece
    # today (Lakeshore Hardware), so the anchor stays put.
    check_answer_phrase(judge, answer, "bill_sender", "Lakeshore Hardware")
    # r2 deepening (fix F-3): dashboard pickup confirmation, bill category,
    # renewal sender, and the older-than-today count.
    check_answer_phrase(judge, answer, "pickup_confirmation", "PKG-338275")
    check_answer_phrase(judge, answer, "bill_category", "Bill/Statement")
    check_answer_phrase(judge, answer, "renewal_sender",
                        "Illinois Secretary of State")
    check_answer_number(judge, answer, "older_pieces", 1)
    # audit deepening (ordinal 57): Bob's seeded claim, his most recent
    # delivery, and the older-than-today Informed Delivery sender.
    check_visited_path(judge, traj, "nav_claim_detail", r"/claims/CLM-55219088")
    check_visited_path(judge, traj, "nav_delivery_010",
                       r"/tracking/9405500000000000000010")
    check_answer_phrase(judge, answer, "claim_status", "In Review")
    check_answer_money(judge, answer, "claim_amount", 280.00)
    check_answer_any(judge, answer, "delivery_010_time", [
        "4:41 pm", "2026-09-24"])
    check_answer_phrase(judge, answer, "older_piece_sender",
                        "Midwest Chess League")
    # audit deepening (ordinal 57): the task now also SAVES the in-transit
    # tracking number to the account ("Candle restock") — the only allowed
    # state change (verify_4 was read-only before the deepening).
    check_answer_phrase(judge, answer, "saved_label", "Candle restock")
    check_only_tables_changed(judge, initial, after, {"saved_tracking"})
    check_rows_added(judge, initial, after, "saved_tracking", [
        [None, 2, "9405500000000000000010", "Candle restock", "2026-09-28"],
    ], "saved_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
