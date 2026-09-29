#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--7 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_7.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--7"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_pickup", r"/pickup")
    check_answer_phrase(judge, answer, "confirmation", "PKG-C0DAFAB")
    check_answer_phrase(judge, answer, "pickup_date", "September 30, 2026")
    # audit deepening (ordinal 57): the pickup request now carries the
    # phone/email from the task text, and the walk checks the serving
    # Post Office for ZIP 02110.
    check_answer_phrase(judge, answer, "pickup_address",
                        "88 State St, Boston, MA, 02110")
    check_visited_path(judge, traj, "nav_locations_02110", r"/locations/")
    check_answer_phrase(judge, answer, "boston_po_name", "Boston")
    check_only_tables_changed(judge, initial, after, {"pickup_requests"})
    check_rows_added(judge, initial, after, "pickup_requests", [
        [None, None, "PKG-C0DAFAB", "2026-09-30",
         "88 State St, Boston, MA, 02110", "(857) 555-0144",
         "seller@example.com", None, None,
         "Scheduled", "2026-09-28"],
    ], "pickup_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
