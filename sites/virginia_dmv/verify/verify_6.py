#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--6 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the reviewer's independent
Playwright honest walks on the review container wh-vadm-review, seed md5
e20897642a951494ced5ad6393a78ad7) — never read from tasks.jsonl.
Usage: python3 verify_6.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_ordered,
    check_answer_phrase, check_answer_regex, check_read_only,
    check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Virginia DMV--6"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # bob.c: reserve a Richmond Central renewal appointment, then cancel it
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_new_appointment", r"/appointments/new")
    check_visited_path(judge, traj, "nav_lookup", r"/appointments/lookup")
    check_answer_phrase(judge, answer, "office_address", "2300 West Broad Street")
    check_answer_regex(judge, answer, "confirmation_number", r"VADM\d{6}-[A-F0-9]{6}")
    check_answer_regex(judge, answer, "booked_time", r"\d{1,2}:\d{2} AM")
    check_answer_any(judge, answer, "booked_date", ["2026-10-08", "october 8"])
    check_answer_phrase(judge, answer, "confirmation_email", "bob.c@test.com")
    check_answer_any(judge, answer, "cancel_text", ["canceled", "cancelled"])
    check_only_tables_changed(judge, initial, after, {"appointments"})
    check_rows_added(judge, initial, after, "appointments", [
        (None, "rx:^VADM\\d{6}-[A-F0-9]{6}$", 2, "Bob Chen", "bob.c@test.com",
         "richmond-central", "Driver's License Renewal", "2026-10-08",
         "rx:^\\d{1,2}:\\d{2} AM$", "Canceled", "2026-09-29"),
    ], "appt_added_canceled")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
