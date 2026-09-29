#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--14 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the r3 honest Playwright walks on
the fix container wh-vadm-fix3, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r3-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_14.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--14"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # carol.d: renewal preview + replacement order + replacement-license rules
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_renewal", r"/account/license/renew")
    check_visited_path(judge, traj, "nav_renewal_preview", r"/account/license/renew\?years=8")
    check_visited_path(judge, traj, "nav_replace", r"/account/license/replace")
    check_visited_path(judge, traj, "nav_receipt_copy", r"/account/receipt/REP")
    check_visited_path(judge, traj, "nav_replace_rules", r"/licenses-ids/license/replace")
    check_visited_path(judge, traj, "nav_forms", r"/forms")
    check_answer_money(judge, answer, "renewal_preview_total", 32.00)
    check_answer_any(judge, answer, "credential_type", ["driver's license", "driver\u2019s license", "drivers license"])
    check_answer_any(judge, answer, "credential_class", ["class d", "\u2014 class d", "- class d"])
    check_answer_phrase(judge, answer, "account_status", "Expired - renewable online within 1 year")
    check_answer_count_at_least(judge, answer, "other_reasons", ["damaged", "never received in the mail", "never received"], 2)
    check_answer_money(judge, answer, "replacement_fee", 20.00)
    check_answer_money(judge, answer, "total_charged", 20.00)
    check_answer_regex(judge, answer, "receipt_number", r"REP\d{6}-[A-F0-9]{6}")
    check_answer_any(judge, answer, "card_arrival", ["5 business days", "five business days"])
    check_answer_any(judge, answer, "receipt_copy", ["replacement driver's license card $20.00",
                                                      "replacement driver's license card"])
    check_answer_any(judge, answer, "renew_or_replace", ["less than one year away", "renew instead"])
    check_answer_count_at_least(judge, answer, "online_blockers",
                                ["under 18", "under the age of 18", "expired", "name change",
                                 "owe dmv", "owe money", "owing money"], 2)
    check_answer_any(judge, answer, "in_person_application",
                     ["driver's license and identification card application", "dl 1p", "dl1p"])
    check_only_tables_changed(judge, initial, after, {"transactions"})
    check_rows_added(judge, initial, after, "transactions", [
        (None, "rx:^REP\\d{6}-[A-F0-9]{6}$", 3, "Driver's License Replacement",
         "rx:Lost or stolen", "$20.00", None, "2026-09-29"),
    ], "txn_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
