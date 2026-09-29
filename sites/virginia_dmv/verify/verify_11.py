#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--11 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the r3 honest Playwright walks on
the fix container wh-vadm-fix3, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r3-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_11.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_ordered,
    check_answer_money_after, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Virginia DMV--11"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # forms catalog: CRD 01 + counts + CSMA 8 + PPI page + fee + wizard booking
    check_visited_path(judge, traj, "nav_forms", r"/forms")
    check_visited_path(judge, traj, "nav_search", r"/forms\?q=")
    check_visited_path(judge, traj, "nav_ppi", r"/records/ppi")
    check_visited_path(judge, traj, "nav_fees", r"/vehicles/taxes-fees")
    check_visited_path(judge, traj, "nav_wizard", r"/appointments/new")
    check_answer_any(judge, answer, "form_number", ["crd 01", "crd-01", "crd01"])
    check_answer_phrase(judge, answer, "form_title", "Request for Vehicle Information by a Prospective Purchaser")
    check_answer_number(judge, answer, "total_forms", 419)
    check_answer_number(judge, answer, "spanish_forms", 17)
    check_answer_any(judge, answer, "translator_form", ["csma 8", "csma8"])
    check_answer_count_at_least(judge, answer, "ppi_ways",
                                ["online", "by mail", "customer service center"], 3)
    check_answer_any(judge, answer, "ppi_mail_wait", ["15 days", "up to 15"])
    check_answer_money(judge, answer, "ppi_fee", 12.00)
    check_answer_regex(judge, answer, "confirmation_number", r"VADM\d{6}-[A-F0-9]{6}")
    check_answer_regex(judge, answer, "booked_time", r"\d{1,2}:\d{2} AM")
    check_answer_any(judge, answer, "booked_date", ["2026-10-06", "october 6"])
    check_answer_any(judge, answer, "booked_service", ["driver record / vehicle record",
                                                       "driver record/vehicle record"])
    check_only_tables_changed(judge, initial, after, {"appointments"})
    check_rows_added(judge, initial, after, "appointments", [
        (None, "rx:^VADM\\d{6}-[A-F0-9]{6}$", None, "Sam Taylor", "sam.taylor@example.com",
         "alexandria", "Driver Record / Vehicle Record", "2026-10-06",
         "rx:^\\d{1,2}:\\d{2} AM$", "Confirmed", "2026-09-29"),
    ], "appt_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
