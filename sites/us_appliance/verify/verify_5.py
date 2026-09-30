#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--5 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_5.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "USAppliance--5"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the order tracking page.
    check_visited_path(judge, traj, "nav_tracking", r"/ordertracking\.html")
    # answer ground truth
    check_answer_phrase(judge, answer, "error_wrong_email",
                        "The order number and email do not match our records")
    check_answer_phrase(judge, answer, "o10003_status", "In Transit")
    check_answer_phrase(judge, answer, "o10003_carrier", "Valley Companies")
    check_answer_phrase(judge, answer, "o10003_tracking", "VC559201")
    check_answer_phrase(judge, answer, "o10003_eta", "Oct 2, 2026")
    check_answer_phrase(judge, answer, "o10003_latest_event", "In Transit")
    check_answer_phrase(judge, answer, "o10003_latest_detail", "Your shipment is on its way")
    check_answer_phrase(judge, answer, "o10001_status", "Delivered")
    check_answer_phrase(judge, answer, "o10001_carrier", "R+L Carriers")
    # audit-rail deepening: orders 10004 (Processing, no carrier line yet)
    # and 10005 (Out for Delivery via FedEx).
    check_answer_phrase(judge, answer, "o10004_status", "Processing")
    check_answer_count_at_least(judge, answer, "o10004_no_carrier",
                                ["no carrier", "no shipping carrier",
                                 "carrier not", "has not shipped yet",
                                 "not yet shipped", "no tracking"], 1)
    check_answer_phrase(judge, answer, "o10005_status", "Out for Delivery")
    check_answer_phrase(judge, answer, "o10005_carrier", "FedEx")
    check_answer_phrase(judge, answer, "o10005_tracking", "774912345678")
    check_answer_phrase(judge, answer, "carrier_note",
                        "24-48 hours for the shipping company to post the tracking information in their systems")
    check_answer_phrase(judge, answer, "carrier_phone_card",
                        "R+L Carriers at 1-800-543-5589")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
