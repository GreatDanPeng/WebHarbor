#!/usr/bin/env python3
"""Deterministic verifier for Verizon--9 (verizon).

Ground truth below is HARDCODED (frozen from the contributor's two
independent strict-caliber Playwright rounds on the r3 fix container
wh-verizon-fix3, seed md5 f2d20153c24b6945fb5203b81d7f1fb6) — never read
from tasks.jsonl. Navigation gates cover ONLY the surfaces the (r3
deepened) task text requires; answer anchors are page-verbatim with
tolerance for equally-honest renderings.
Usage: python3 verify_9.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_number_absent, check_answer_ordered, check_answer_phrase,
    check_answer_regex, check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, db_one, final_answer, run_verifier,
)

TASK_ID = "Verizon--9"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_bills", r"/account/bills/$")
    check_visited_path(judge, traj, "nav_sep_bill", r"/account/bills/3/")
    check_visited_path(judge, traj, "nav_aug_bill", r"/account/bills/2/")
    check_visited_path(judge, traj, "nav_jul_bill", r"/account/bills/1/")
    check_visited_path(judge, traj, "nav_pay", r"/account/pay/")
    check_visited_path(judge, traj, "nav_payment_conf", r"/payment/PMT[0-9]+")
    check_visited_path(judge, traj, "nav_bills_after", r"/account/bills/")
    check_visited_path(judge, traj, "nav_sep_bill_echo", r"/account/bills/3/")
    check_visited_path(judge, traj, "nav_usage", r"/account/usage/")
    check_visited_path(judge, traj, "nav_autopay", r"/account/autopay/")

    # answer ground truth
    check_answer_count_at_least(judge, answer, "sep_charges",
        ["Simplicity Plan — Alice", "Device payment — Alice",
         "Verizon Mobile Protect — Alice", "Simplicity Plan — Mike",
         "Device payment — Mike", "Taxes, surcharges and fees"], 6)
    check_answer_money(judge, answer, "protection_amount", 17.00)
    check_answer_regex(judge, answer, "protection_line", r"protection[^.]{0,40}Alice|Alice[^.]{0,40}protection")
    check_answer_money(judge, answer, "aug_total", 160.62)
    check_answer_money(judge, answer, "jul_total", 160.62)
    check_answer_regex(judge, answer, "totals_unchanged",
        r"(did not change|unchanged|same|stayed)")
    check_answer_regex(judge, answer, "aug_jul_protection",
        r"(same|both|each|also)[^.]{0,200}Aug(ust)?|Aug(ust)?[^.]{0,200}(same|both|each|also)")
    check_answer_regex(judge, answer, "jul_protection",
                       r"Jul(y)?[^.]{0,200}protection|protection[^.]{0,200}Jul(y)?")
    row = db_one(after, "SELECT confirmation, amount, method FROM payments WHERE id = (SELECT MAX(id) FROM payments)")
    check_answer_confirmation(judge, answer, "pmt_confirmation", row[0] if row else None, "PMT")
    check_answer_money(judge, answer, "pmt_amount", 50.00)
    check_answer_phrase(judge, answer, "pmt_method", "Bank account (ACH ending 8891)")
    check_answer_phrase(judge, answer, "sep_new_status", "paid")
    check_answer_regex(judge, answer, "payment_echo", r"Payments applied")
    check_answer_regex(judge, answer, "more_data", r"Alice[^.]{0,80}(more|31\.4)")

    # DB after-state: exact allowed delta
    check_only_tables_changed(judge, initial, after, {"payments", "bills"})
    check_rows_added(judge, initial, after, "payments",
        [[None, 1, 3, "50", "Bank account (ACH ending 8891)",
          "rx:^PMT[0-9]{6}$", "2026-09-29"]], "payment_row")
    check_rows_changed(judge, initial, after, "bills",
        [[3, 1, "Sep 2026", "2026-10-13", "160.62", "paid", None]], "bill_status")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
