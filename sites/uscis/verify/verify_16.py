#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--16 (uscis).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-uscis-review, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_16.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--16"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: login, the 4-step appointment booking, confirmation, and
    # the appointment view flow.
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_appt_new", r"/appointment/new")
    check_visited_path(judge, traj, "nav_confirmed", r"/appointment/confirmed")
    check_visited_path(judge, traj, "nav_appt_view", r"/appointment/view")
    # answer ground truth (slot choice is the agent's own; office and status
    # are frozen)
    check_answer_any(judge, answer, "office", ["Boston", "BOS"])
    check_answer_phrase(judge, answer, "booked_date", "2026-10-")
    check_answer_count_at_least(judge, answer, "booked_time",
                                ["09:00", "09:45", "10:30", "11:15", "01:00",
                                 "01:45", "02:30", "03:15"], 1)
    check_answer_phrase(judge, answer, "confirmation", "USCBOS")
    check_answer_phrase(judge, answer, "view_status", "Scheduled")
    # DB: exactly one new appointments row (ADIT Stamp at BOS, Scheduled),
    # nothing else changed.
    check_only_tables_changed(judge, initial, after, {"appointments"})
    check_rows_added(judge, initial, after, "appointments",
                     [[None, 3, "ADIT Stamp", None, "BOS", "Boston",
                       "rx:^2026-10-(0[5-9]|1[0-6])$",
                       "rx:^(09:00|09:45|10:30|11:15|01:00|01:45|02:30|03:15) (AM|PM)$",
                       "rx:^USCBOS\\d+$", "Scheduled"]],
                     "db_appointment_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
