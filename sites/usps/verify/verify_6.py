#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--6 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_6.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--6"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_cns_step3", r"/clicknship/create\?step=3")
    check_visited_path(judge, traj, "nav_label", r"/clicknship/label")
    check_answer_money(judge, answer, "ga_price", 18.40)
    check_answer_money(judge, answer, "pm_price", 23.25)
    check_answer_phrase(judge, answer, "chosen_service", "USPS Ground Advantage")
    check_answer_money(judge, answer, "total_paid", 18.40)
    check_answer_regex(judge, answer, "new_tracking", r"94\d{20}")
    check_only_tables_changed(judge, initial, after,
                              {"shipments", "scan_events"})
    # NOTE (reviewer finding F-7): the shipped wizard blanks the step-1
    # address fields on later POSTs, so the honest row carries empty
    # sender/recipient fields.
    check_rows_added(judge, initial, after, "shipments", [
        [None, r"rx:^94\d{20}$", 1, "ga", None, None, None, None, None,
         None, None, None, 6.0, "2026-09-28", "Shipping Label Created",
         "2026-10-01", None, None, 0, None, 1, 18.40, 0, None,
         "2026-09-28"],
    ], "cns_shipment_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
