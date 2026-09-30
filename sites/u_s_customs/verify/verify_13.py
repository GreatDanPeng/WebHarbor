#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--13 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_13.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--13"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_careers_search", r"/careers/search\?.*q=[^#]*(Border|Officer)")
    check_visited_path(judge, traj, "nav_bpa_posting", r"/careers/job/882256600")
    check_visited_path(judge, traj, "nav_cbpo_posting", r"/careers/job/882166800")
    check_answer_phrase(judge, answer, "bpa_salary", "$51,632 - $92,912")
    check_answer_phrase(judge, answer, "bpa_closing", "09/30/2026")
    check_answer_phrase(judge, answer, "bpa_announcement", "BPA DH 26-12")
    check_answer_money(judge, answer, "bpa_incentive", 20000)
    check_answer_count_at_least(judge, answer, "incentive_split", ["10,000"], 1)
    check_answer_phrase(judge, answer, "cbpo_salary", "$41,863 - $112,415")
    check_answer_phrase(judge, answer, "cbpo_closing", "09/30/2026")
    check_answer_phrase(judge, answer, "cbpo_drug", "Yes")
    check_answer_number(judge, answer, "salary_gap", 9769)
    check_answer_phrase(judge, answer, "bpa_org", "U.S. Border Patrol")
    check_answer_phrase(judge, answer, "cbpo_org", "Office of Field Operations")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
