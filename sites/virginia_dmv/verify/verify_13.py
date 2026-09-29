#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--13 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_13.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--13"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # alice.j: certified driving record order + RAV4 title/VIN + fee cross-check
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_records_order", r"/account/records")
    check_visited_path(judge, traj, "nav_receipt_copy", r"/account/receipt/REC")
    check_visited_path(judge, traj, "nav_records_hub", r"/records(?!/)")
    check_visited_path(judge, traj, "nav_fees", r"/vehicles/taxes-fees")
    check_answer_money(judge, answer, "base_price", 8.00)
    check_answer_money(judge, answer, "certified_extra", 5.00)
    check_answer_money(judge, answer, "total", 13.00)
    check_answer_regex(judge, answer, "receipt_number", r"REC\d{6}-[A-F0-9]{6}")
    check_answer_number(judge, answer, "online_view_days", 5)
    check_answer_phrase(judge, answer, "rav4_title", "T9013-4427")
    check_answer_phrase(judge, answer, "rav4_vin", "2T3W1RFV0KW204361")
    check_answer_money(judge, answer, "mail_price", 9.00)
    check_answer_money(judge, answer, "online_price", 8.00)
    check_answer_count_at_least(judge, answer, "receipt_copy_lines",
                                ["driving record $8.00", "certified record $5.00", "$13.00"], 2)
    check_only_tables_changed(judge, initial, after, {"transactions", "record_requests"})
    check_rows_added(judge, initial, after, "record_requests", [
        (None, "rx:^REC\\d{6}-[A-F0-9]{6}$", 1, "driver", 1, "online", None, "Processing", "$13.00", "2026-09-29"),
    ], "record_request_added")
    check_rows_added(judge, initial, after, "transactions", [
        (None, "rx:^REC\\d{6}-[A-F0-9]{6}$", 1, "Record Request",
         "rx:certified", "$13.00", None, "2026-09-29"),
    ], "txn_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
