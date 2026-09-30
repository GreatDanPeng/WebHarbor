#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--14 (uscis).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-uscis-review, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_14.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_office_range_map,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "USCIS.gov--14"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the Naturalization Eligibility Tool, 8 answered questions.
    check_visited_path(judge, traj, "nav_eligibility",
                       r"/citizenship-resource-center/learn-about-citizenship/"
                       r"naturalization-eligibility-tool-0")
    # answer ground truth
    check_answer_number(judge, answer, "question_count", 8)
    check_answer_any(judge, answer, "outcome_headline",
                    ["You may be eligible to apply for naturalization."])
    check_answer_count_at_least(judge, answer, "explanation",
                                ["lawful permanent resident for more than 5 years",
                                 "good moral character",
                                 "English and civics requirements"], 2)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
