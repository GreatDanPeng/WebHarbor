#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--0 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_0.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--0"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_postcalc", r"/postcalc/")
    check_visited_path(judge, traj, "nav_letters_calc", r"/postcalc/letters")
    check_answer_money(judge, answer, "stamped_3oz", 1.40)
    check_answer_money(judge, answer, "stamped_2oz", 1.11)
    check_answer_money(judge, answer, "metered_1oz", 0.78)
    check_answer_money(judge, answer, "postcard", 0.65)
    check_answer_money(judge, answer, "diff_3oz_vs_postcard", 0.75)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
