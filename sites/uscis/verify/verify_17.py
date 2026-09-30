#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--17 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_17.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_any, check_answer_count_at_least, check_answer_money,
    check_answer_number, check_answer_ordered, check_answer_phrase,
    check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "USCIS.gov--17"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: login, dashboard, cancel, the new-appointment flow for
    # ZIP 77002, and the appointment view flow.
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_dashboard", r"/account(?!/)")
    check_visited_path(judge, traj, "nav_appt_new", r"/appointment/new")
    check_visited_path(judge, traj, "nav_appt_view", r"/appointment/view")
    # answer ground truth
    check_answer_phrase(judge, answer, "service_type", "Emergency Advance Parole")
    check_answer_phrase(judge, answer, "office", "Houston")
    check_answer_phrase(judge, answer, "date", "2026-10-06")
    check_answer_phrase(judge, answer, "time", "09:45 AM")
    check_answer_phrase(judge, answer, "old_status", "Canceled")
    check_answer_regex(judge, answer, "new_confirmation", r"USCHOU\d{10}")
    check_answer_phrase(judge, answer, "new_status", "Scheduled")
    check_answer_ordered(judge, answer, "status_order", ["Canceled", "Scheduled"])
    # DB: the seeded HOU appointment row changed to Canceled, plus exactly one
    # new Scheduled EAP row at the Houston office for the same user.
    check_only_tables_changed(judge, initial, after, {"appointments"})
    check_rows_changed(judge, initial, after, "appointments",
                       [[None, 4, "Emergency Advance Parole (EAP)", None,
                         "HOU", "Houston", "2026-10-06", "09:45 AM",
                         "USCHOU2610060945", "Canceled"]],
                       "db_appointment_canceled")
    check_rows_added(judge, initial, after, "appointments",
                     [[None, 4, "Emergency Advance Parole (EAP)", None,
                       "HOU", "Houston", None, None, None, "Scheduled"]],
                     "db_appointment_booked")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
