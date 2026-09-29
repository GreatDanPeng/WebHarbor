#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--9 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_9.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--9"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_locations", r"/locations")
    check_visited_path(judge, traj, "nav_de_search", r"/locations/\?.*q=DE")
    check_visited_path(judge, traj, "nav_bear",
                       r"/locations/bear-de-19701")
    check_visited_path(judge, traj, "nav_second",
                       r"/locations/bowers-de-19932")
    # r2 truth-move #3/#4/#5 (fix F-10): a 2-letter query is an exact state
    # match now, so DE lists only Delaware offices — the kiosk-filtered count
    # is 35 and the first three are Bear/Bowers/Bridgeville (not the old
    # fuzzy Alaska hits). Hours render in 12-hour clock (fix F-13).
    check_answer_number(judge, answer, "locations_shown", 35)
    check_answer_count_at_least(judge, answer, "first_three",
                                ["Bear", "19701", "Bowers",
                                 "19932", "Bridgeville", "19933"], 6)
    check_answer_any(judge, answer, "hours_full",
                     ["8:00 am - 6:00 pm"])
    check_answer_any(judge, answer, "sat_hours",
                     ["9:00 am - 12:00 pm"])
    check_answer_any(judge, answer, "lobby_hours", ["24 hours"])
    check_answer_phrase(judge, answer, "bear_zip", "19701")
    check_answer_count_at_least(judge, answer, "po_box_rentals",
                                ["Reserve a PO Box", "PO Box"], 1)
    check_answer_any(judge, answer, "second_sat_hours", ["Closed"])
    check_answer_number(judge, answer, "total_de_locations", 63)
    # audit deepening (ordinal 57): third kiosk result weekday hours and
    # the Po Box Rental filter count for Delaware.
    check_visited_path(judge, traj, "nav_bridgeville",
                       r"/locations/bridgeville-de-19933")
    check_answer_any(judge, answer, "bridgeville_weekday", [
        "8:00 am - 5:00 pm"])
    check_answer_number(judge, answer, "po_box_rental_count", 33)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
