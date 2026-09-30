#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--1 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_1.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--1"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # alice.j: 1/2/3-year Camry previews + 2-year renewal + receipt reopen
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_renew", r"/account/vehicles/1/renew")
    check_visited_path(judge, traj, "nav_preview_1yr", r"/account/vehicles/1/renew\?years=1")
    check_visited_path(judge, traj, "nav_preview_2yr", r"/account/vehicles/1/renew\?years=2")
    check_visited_path(judge, traj, "nav_preview_3yr", r"/account/vehicles/1/renew\?years=3")
    check_visited_path(judge, traj, "nav_registration", r"/vehicles/registration")
    check_visited_path(judge, traj, "nav_receipt_copy", r"/account/receipt/REG")
    check_answer_money(judge, answer, "one_year_total", 29.75)
    check_answer_money(judge, answer, "two_year_total", 56.50)
    check_answer_money(judge, answer, "three_year_total", 85.25)
    check_answer_money(judge, answer, "two_year_registration", 61.50)
    check_answer_money(judge, answer, "internet_discount", 2.00)
    check_answer_money(judge, answer, "multiyear_discount", 3.00)
    check_answer_any(judge, answer, "multiyear_advertised",
                     ["$3", "three-year", "3 discount", "$4 discount online"])
    check_answer_regex(judge, answer, "receipt_number", r"REG\d{6}-[A-F0-9]{6}")
    check_answer_phrase(judge, answer, "new_expiration", "2028-10-15")
    check_answer_count_at_least(judge, answer, "receipt_copy_lines",
                                ["$61.50", "-$2.00", "-$3.00"], 3)
    check_only_tables_changed(judge, initial, after, {"transactions", "vehicles"})
    check_rows_added(judge, initial, after, "transactions", [
        (None, "rx:^REG\\d{6}-[A-F0-9]{6}$", 1, "Registration Renewal",
         "rx:2-year online renewal", "$56.50", None, "2026-09-29"),
    ], "txn_added")
    check_rows_changed(judge, initial, after, "vehicles", [
        (1, None, None, None, None, None, None, None, None, "2028-10-15", 2, None, None, None, None, None),
    ], "vehicle_renewed")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
