#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--12 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_12.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--12"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # bob.c: change mailing address + the address rules pages
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_address_change", r"/account/address-change")
    check_visited_path(judge, traj, "nav_receipt_copy", r"/account/receipt/ADR")
    check_visited_path(judge, traj, "nav_piu", r"/records/personal-information-updates")
    check_visited_path(judge, traj, "nav_address_page", r"/online-services/address-change")
    check_answer_phrase(judge, answer, "confirmation_message", "Your address has been updated")
    check_answer_phrase(judge, answer, "updated_address", "4020 University Drive")
    check_answer_phrase(judge, answer, "updated_city_zip", "Fairfax")
    check_answer_regex(judge, answer, "receipt_number", r"ADR\d{6}-[A-F0-9]{6}")
    check_answer_any(judge, answer, "receipt_copy", ["address change", "$0.00"])
    check_answer_number(judge, answer, "notify_days", 30)
    check_answer_any(judge, answer, "po_box", ["p.o. box or business address is not acceptable",
                                               "not acceptable"])
    check_answer_count_at_least(judge, answer, "voter_note",
                                ["register to vote", "voter registration address"], 1)
    check_answer_any(judge, answer, "out_of_state", ["cancel your driver's license",
                                                    "may cancel your driver's license or photo id"])
    check_answer_count_at_least(judge, answer, "address_kinds",
                                ["residence/home", "mailing address",
                                 "vehicle registration mailing address"], 3)
    check_only_tables_changed(judge, initial, after, {"users", "transactions"})
    check_rows_changed(judge, initial, after, "users", [
        (2, "bob.c@test.com", None, None, None, "4020 University Drive", "Fairfax", "VA", "22030", None, None),
    ], "address_updated")
    check_rows_added(judge, initial, after, "transactions", [
        (None, "rx:^ADR\\d{6}-[A-F0-9]{6}$", 2, "Address Change",
         "rx:4020 University Drive", "$0.00", None, "2026-09-29"),
    ], "txn_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
