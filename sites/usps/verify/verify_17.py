#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--17 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_17.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--17"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_claims_help", r"/help/claims")
    check_visited_path(judge, traj, "nav_claim_file", r"/claims/file")
    check_visited_path(judge, traj, "nav_claim_status", r"/claims/status")
    check_answer_phrase(judge, answer, "claim_number", "CLM-D7D8EDA")
    check_answer_money(judge, answer, "claim_amount", 280.00)
    check_answer_phrase(judge, answer, "claim_status", "Received")
    check_only_tables_changed(judge, initial, after, {"claims"})
    check_rows_added(judge, initial, after, "claims", [
        [None, "CLM-D7D8EDA", 2, "9405500000000000000004", "damage",
         None, 280.0, "Received", "2026-09-28", None, None, None],
    ], "claim_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
