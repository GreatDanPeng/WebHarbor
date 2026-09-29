#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--19 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_19.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--19"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_advisories", r"/travel/advisories-wait-times")
    check_visited_path(judge, traj, "nav_bwt_canada", r"/bwt\?.*border=canada")
    check_visited_path(judge, traj, "nav_search_7507", r"/search\?.*q=[^#]*7507")
    check_answer_phrase(judge, answer, "form_number", "7507")
    check_answer_phrase(judge, answer, "form_name", "General Declaration")
    check_answer_phrase(judge, answer, "who_may_submit", "owners and operators of commercial aircraft")
    check_answer_phrase(judge, answer, "protect", "Personally Identifiable Information")
    check_answer_number(judge, answer, "canada_crossings", 30)
    check_answer_phrase(judge, answer, "first_crossing", "Alexandria Bay")
    check_answer_phrase(judge, answer, "first_hours", "24 hrs/day")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
