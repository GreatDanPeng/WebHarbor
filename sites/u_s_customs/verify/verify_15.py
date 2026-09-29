#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--15 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_15.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--15"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_account", r"/account")
    # F-6 fix: Dana's seeded saved crossing is now pinned to port_number
    # 250601 — "Otay Mesa - Passenger" — whose lanes report live delays
    # (standard passenger 185 min, Ready Lane 120 min). The task premise
    # (a saved crossing with a live standard passenger delay and Ready Lane
    # delay) matches the seed state; the honest answer reports 185/120.
    check_visited_path(judge, traj, "nav_saved_crossing", r"/bwt/crossing/250601")
    check_visited_path(judge, traj, "nav_saved_job", r"/careers/job/882256600")
    check_visited_path(judge, traj, "nav_ttp_app", r"/ttp/status/GE-77554402")
    check_visited_path(judge, traj, "nav_schedule", r"/ttp/schedule/GE-77554402")
    check_answer_phrase(judge, answer, "saved_crossing", "Otay Mesa - Passenger")
    check_answer_number(judge, answer, "std_passenger_delay", 185)
    check_answer_number(judge, answer, "ready_lane_delay", 120)
    # the old seed state (250609, all lanes Update Pending) belongs to a
    # DIFFERENT crossing; reporting it as the saved crossing is wrong
    check_answer_absent(judge, answer, "stale_state", "update pending")
    check_answer_phrase(judge, answer, "job_salary", "$51,632 - $92,912")
    check_answer_phrase(judge, answer, "job_closing", "09/30/2026")
    check_answer_phrase(judge, answer, "ttp_number", "GE-77554402")
    check_answer_phrase(judge, answer, "ttp_program", "Global Entry")
    check_answer_phrase(judge, answer, "ttp_status", "Interview Scheduled")
    check_answer_phrase(judge, answer, "interview_date", "2026-10-14")
    check_answer_phrase(judge, answer, "interview_slot", "10:00 a.m.")
    check_answer_phrase(judge, answer, "lax_hours", "7:30 a.m. - 9:30 p.m.")
    check_answer_phrase(judge, answer, "lax_phone", "(310) 642-1425")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
