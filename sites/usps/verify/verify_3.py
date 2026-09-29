#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--3 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_3.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--3"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_tracking", r"/tracking")
    check_visited_path(judge, traj, "nav_track_003", r"/tracking/9405500000000000000003")
    check_visited_path(judge, traj, "nav_track_007", r"/tracking/9405500000000000000007")
    check_section_phrase(judge, answer, "t3_status",
                        "9405500000000000000003", "In Transit")
    check_answer_absent(judge, answer, "t3_no_late",
                        "9405500000000000000003 In Transit, Arriving Late")
    check_section_phrase(judge, answer, "t3_expected",
                        "9405500000000000000003", "September 30, 2026")
    check_answer_number(judge, answer, "t3_events", 4)
    check_answer_any(judge, answer, "t3_latest_scan", [
        "DENVER, CO", "Denver, CO", "2026-09-26 12:00"])
    # r2 deepening (fix F-3): earliest scan for 003, and 007 event
    # count / service / insured value.
    check_answer_any(judge, answer, "t3_earliest_scan", [
        "2026-09-25", "Chicago, IL", "Shipping Label Created"])
    check_section_phrase(judge, answer, "t7_status",
                        "9405500000000000000007", "In Transit, Arriving Late",
                        must_not_appear_before=True)
    check_section_phrase(judge, answer, "t7_exception",
                        "9405500000000000000007", "Processing Exception")
    check_answer_number(judge, answer, "t7_events", 7)
    check_section_phrase(judge, answer, "t7_service",
                        "9405500000000000000007", "Priority Mail")
    check_answer_money(judge, answer, "t7_insured", 100.00)
    # audit deepening (ordinal 57): two more seeded shipments plus the
    # tracking-status glossary meaning.
    check_visited_path(judge, traj, "nav_track_005",
                       r"/tracking/9405500000000000000005")
    check_visited_path(judge, traj, "nav_track_008",
                       r"/tracking/9405500000000000000008")
    check_section_phrase(judge, answer, "t5_status",
                         "9405500000000000000005", "Out for Delivery")
    check_section_phrase(judge, answer, "t5_signature",
                         "9405500000000000000005", "Signature required")
    check_section_phrase(judge, answer, "t8_status",
                         "9405500000000000000008", "Delivered")
    check_section_phrase(judge, answer, "t8_service",
                         "9405500000000000000008", "Media Mail")
    check_answer_phrase(judge, answer, "glossary_in_transit",
                        "moving through the USPS network")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
