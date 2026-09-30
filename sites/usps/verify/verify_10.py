#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--10 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_10.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--10"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_po_boxes", r"/po-boxes")
    check_visited_path(judge, traj, "nav_locations", r"/locations")
    check_visited_path(judge, traj, "nav_boston", r"/locations/boston-ma-02205")
    check_visited_path(judge, traj, "nav_reserve", r"/po-boxes/reserve/boston-ma-02205")
    check_answer_money(judge, answer, "size2_6mo", 65.00)
    check_answer_money(judge, answer, "size5_6mo", 40.00)
    # r2 deepening (fix F-3): Size 7 fees for both periods, and the Boston
    # Post Office's Monday-Friday hours read from its detail page.
    check_answer_money(judge, answer, "size7_3mo", 21.00)
    check_answer_money(judge, answer, "size7_6mo", 31.00)
    check_answer_any(judge, answer, "boston_mon_fri",
                     ["9:00 am - 7:00 pm", "9:00 am to 7:00 pm"])
    check_answer_number(judge, answer, "box_number", 7792)
    check_answer_money(judge, answer, "fee_paid", 65.00)
    # audit deepening (ordinal 57): Size 1 six-month fee and the
    # Cambridge (02138) comparison.
    check_answer_money(judge, answer, "size1_6mo", 81.00)
    check_visited_path(judge, traj, "nav_cambridge",
                       r"/locations/cambridge-ma-02138")
    check_answer_phrase(judge, answer, "cambridge_name", "Cambridge")
    check_answer_any(judge, answer, "cambridge_mon_fri", ["9:00 am - 7:00 pm"])
    check_only_tables_changed(judge, initial, after, {"po_box_rentals"})
    check_rows_added(judge, initial, after, "po_box_rentals", [
        [None, None, None, "7792", "2", 65.0, "6 months", "Reserved",
         "2027-03-30", "2026-09-28"],
    ], "rental_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
