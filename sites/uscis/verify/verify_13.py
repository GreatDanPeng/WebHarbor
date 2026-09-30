#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--13 (uscis).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-uscis-review, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_13.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--13"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the Naturalization Eligibility Tool.
    check_visited_path(judge, traj, "nav_eligibility",
                       r"/citizenship-resource-center/learn-about-citizenship/"
                       r"naturalization-eligibility-tool-0")
    # answer ground truth
    check_answer_phrase(judge, answer, "outcome_headline",
                        "You may already be a U.S. citizen.")
    check_answer_count_at_least(judge, answer, "explanation",
                                ["file a different application",
                                 "Certificate of Citizenship",
                                 "born abroad",
                                 "automatically made you a U.S. citizen"], 3)
    check_answer_phrase(judge, answer, "other_form", "N-600")
    # second scenario (no citizen parent, 35, not armed forces, not LPR,
    # no citizen spouse, not a U.S. national) -> not-eligible outcome
    check_answer_phrase(judge, answer, "outcome2_headline",
                        "You may not be eligible to apply for naturalization "
                        "at this time.")
    check_answer_count_at_least(judge, answer, "key_difference",
                                ["through", "parents",
                                 "not eligible",
                                 "N-600"], 3)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
