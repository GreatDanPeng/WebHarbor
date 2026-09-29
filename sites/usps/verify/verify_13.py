#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--13 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_13.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--13"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_hold_page", r"/manage/hold-mail")
    check_visited_path(judge, traj, "nav_hold_request", r"/manage/hold-mail/request")
    check_answer_phrase(judge, answer, "active_confirmation", "HLD-748291")
    check_answer_phrase(judge, answer, "active_start", "September 25, 2026")
    check_answer_phrase(judge, answer, "active_end", "October 5, 2026")
    check_answer_phrase(judge, answer, "what_happens",
                        "Hold all mail, deliver on end date")
    check_answer_phrase(judge, answer, "new_confirmation", "HLD-FD88495")
    check_answer_number(judge, answer, "max_days", 30)
    # audit deepening (ordinal 57): Carol's PO Box card and her Informed
    # Delivery feed.
    check_answer_phrase(judge, answer, "po_box_number", "3227")
    check_answer_phrase(judge, answer, "po_box_expiry", "March 15, 2027")
    check_visited_path(judge, traj, "nav_informed",
                       r"/account/informed-delivery")
    check_answer_phrase(judge, answer, "informed_sender", "Bay Financial")
    check_answer_phrase(judge, answer, "informed_category", "Bill/Statement")
    check_answer_money(judge, answer, "coa_identity_fee", 1.25)
    check_visited_path(judge, traj, "nav_coa_page", r"/manage/forward")
    check_only_tables_changed(judge, initial, after, {"hold_mail_requests"})
    check_rows_added(judge, initial, after, "hold_mail_requests", [
        [None, 3, "HLD-FD88495", "2026-10-01", "2026-10-15", None, "Active",
         "Hold all mail, deliver on end date", "2026-09-28"],
    ], "hold_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
