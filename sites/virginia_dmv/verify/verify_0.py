#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--0 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_0.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--0"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # carol.d: license facts + fee-chart cross-check + 8-year renewal with REAL ID
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_account", r"/account(?!/)")
    check_visited_path(judge, traj, "nav_renew", r"/account/license/renew")
    check_visited_path(judge, traj, "nav_renew_preview", r"/account/license/renew\?years=8")
    check_visited_path(judge, traj, "nav_fees", r"/vehicles/taxes-fees")
    check_visited_path(judge, traj, "nav_receipt_copy", r"/account/receipt/LIC")
    check_answer_phrase(judge, answer, "license_number", "D5540917")
    check_answer_phrase(judge, answer, "current_expiration", "2025-08-02")
    check_answer_any(judge, answer, "real_id_status", ["not real id compliant"])
    check_answer_money(judge, answer, "per_year_cost", 4.00)
    check_answer_money(judge, answer, "standard_term_total", 32.00)
    check_answer_money(judge, answer, "real_id_fee", 10.00)
    check_answer_money(judge, answer, "total_charged", 42.00)
    check_answer_regex(judge, answer, "receipt_number", r"LIC\d{6}-[A-F0-9]{6}")
    check_answer_phrase(judge, answer, "new_expiration", "2033-08-02")
    check_answer_any(judge, answer, "card_arrival", ["5 business days", "five business days"])
    check_answer_phrase(judge, answer, "fee_chart_form", "DMV 201")
    check_answer_phrase(judge, answer, "fee_chart_edition", "08/10/2026")
    check_answer_money(judge, answer, "receipt_copy_license_line", 32.00)
    check_only_tables_changed(judge, initial, after, {"transactions", "user_licenses"})
    check_rows_added(judge, initial, after, "transactions", [
        (None, "rx:^LIC\\d{6}-[A-F0-9]{6}$", 3, "Driver's License Renewal",
         "rx:with REAL ID", "$42.00", None, "2026-09-29"),
    ], "txn_added")
    check_rows_changed(judge, initial, after, "user_licenses", [
        (None, 3, "D5540917", None, None, None, "2033-08-02", "Valid", 1, None, None),
    ], "license_renewed")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
