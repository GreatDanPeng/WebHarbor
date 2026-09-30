#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--6 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_6.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--6"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_account", r"/account")
    check_visited_path(judge, traj, "nav_ttp_status", r"/ttp/status/GE-77031188")
    check_visited_path(judge, traj, "nav_schedule", r"/ttp/schedule/GE-77031188")
    check_visited_path(judge, traj, "nav_ttp_overview", r"/travel/trusted-traveler-programs")
    check_answer_phrase(judge, answer, "app_number", "GE-77031188")
    check_answer_phrase(judge, answer, "status_before", "Conditionally Approved")
    check_answer_money(judge, answer, "fee", 120.00)
    check_answer_phrase(judge, answer, "austin_center", "Austin-Bergstrom")
    check_answer_phrase(judge, answer, "interview_date", "2026-10-15")
    check_answer_phrase(judge, answer, "interview_slot", "9:00 a.m.")
    check_answer_phrase(judge, answer, "status_after", "Interview Scheduled")
    check_answer_phrase(judge, answer, "austin_phone", "(512) 530-3056")
    check_answer_number(judge, answer, "ge_years", 5)
    check_answer_money(judge, answer, "nexus_fee", 50.00)
    # DB: exactly the Bob GE row changed, nothing else
    check_only_tables_changed(judge, initial, after, {"ttp_applications"})
    check_rows_changed(judge, initial, after, "ttp_applications", [
        [None, "GE-77031188", 2, None, None, None, None, None, None, None,
         None, "Interview Scheduled", None, None, 24, "2026-10-15", "9:00 a.m."],
    ], "ttp_row_scheduled")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
