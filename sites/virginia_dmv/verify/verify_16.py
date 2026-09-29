#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--16 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the r3 honest Playwright walks on
the fix container wh-vadm-fix3, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r3-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_16.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--16"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # alice.j: certified Camry vehicle record + buy-sell research + fee cross-check
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_records_order", r"/account/records")
    check_visited_path(judge, traj, "nav_receipt_copy", r"/account/receipt/REC")
    check_visited_path(judge, traj, "nav_buy_sell", r"/vehicles/buy-sell")
    check_visited_path(judge, traj, "nav_contact", r"/contact-us")
    check_visited_path(judge, traj, "nav_ppi", r"/records/ppi")
    check_visited_path(judge, traj, "nav_fees", r"/vehicles/taxes-fees")
    check_answer_phrase(judge, answer, "camry_title", "T8842-1195")
    check_answer_phrase(judge, answer, "camry_vin", "1HGCF1A23XA448119")
    check_answer_money(judge, answer, "total_charged", 13.00)
    check_answer_regex(judge, answer, "receipt_number", r"REC\d{6}-[A-F0-9]{6}")
    check_answer_count_at_least(judge, answer, "receipt_copy_lines",
                                ["vehicle record (2019 toyota camry) $8.00",
                                 "certified record $5.00", "$13.00"], 2)
    check_answer_count_at_least(judge, answer, "seller_steps",
        ["sign the vehicle over", "sign over the title", "remove license plates", "remove the plates",
         "notify dmv", "notify your insurance company"], 4)
    check_answer_any(judge, answer, "plates_rule", ["remove the plates", "remove your plates", "remove license plates",
                                                    "transfer them to a replacement vehicle", "turn in/inactivate"])
    check_answer_any(judge, answer, "refund_form", ["fms-210", "fms 210"])
    check_answer_any(judge, answer, "gift_form", ["sut-3", "sut 3"])
    check_answer_any(judge, answer, "phone", ["(804) 497-7100", "804-497-7100"])
    check_answer_any(judge, answer, "buyer_application", ["vsa 17a", "vsa17a"])
    check_answer_count_at_least(judge, answer, "ppi_report_includes",
                                ["vehicle description", "vehicle history", "current vehicle information",
                                 "sold date", "disclosure statement"], 3)
    check_answer_money_after(judge, answer, "registration_transfer_fee", "registration transfer", 2.00)
    check_answer_money_after(judge, answer, "replacement_card_fee", "replacement registration card", 2.00)
    check_answer_money(judge, answer, "vehicle_record_online", 8.00)
    check_answer_money_after(judge, answer, "original_title_fee", "original title", 15.00)
    check_only_tables_changed(judge, initial, after, {"transactions", "record_requests"})
    check_rows_added(judge, initial, after, "record_requests", [
        (None, "rx:^REC\\d{6}-[A-F0-9]{6}$", 1, "vehicle", 1, "online", 1,
         "Processing", "$13.00", "2026-09-29"),
    ], "record_request_added")
    check_rows_added(judge, initial, after, "transactions", [
        (None, "rx:^REC\\d{6}-[A-F0-9]{6}$", 1, "Record Request",
         "rx:certified", "$13.00", None, "2026-09-29"),
    ], "txn_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
