#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--14 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_14.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--14"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_forward", r"/manage/forward")
    check_visited_path(judge, traj, "nav_coa_request", r"/manage/change-address/request")
    check_answer_money(judge, answer, "identity_fee", 1.25)
    check_answer_phrase(judge, answer, "pfs", "Premium Forwarding Service")
    check_answer_regex(judge, answer, "confirmation", r"COA-[0-9A-F]{7}")
    check_answer_phrase(judge, answer, "move_type", "Family")
    check_only_tables_changed(judge, initial, after, {"change_of_address"})
    check_rows_added(judge, initial, after, "change_of_address", [
        [None, None, "rx:^COA-[0-9A-F]{7}$", "rx:^Family", None,
         "2026-10-05", "88 State St, Boston, MA, 02110",
         "12 Beacon St, Boston, MA, 02108", "carol.d@test.com", "Active",
         1.25, "2026-09-28"],
    ], "coa_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
