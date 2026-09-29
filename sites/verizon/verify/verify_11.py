#!/usr/bin/env python3
"""Deterministic verifier for Verizon--11 (verizon).

Ground truth below is HARDCODED (frozen from the contributor's two
independent strict-caliber Playwright rounds on the r3 fix container
wh-verizon-fix3, seed md5 f2d20153c24b6945fb5203b81d7f1fb6) — never read
from tasks.jsonl. Navigation gates cover ONLY the surfaces the (r3
deepened) task text requires; answer anchors are page-verbatim with
tolerance for equally-honest renderings.
Usage: python3 verify_11.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--11"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_autopay", r"/account/autopay/")
    check_visited_path(judge, traj, "nav_bills", r"/account/bills/$")
    check_visited_path(judge, traj, "nav_sep_bill", r"/account/bills/9/")
    check_visited_path(judge, traj, "nav_aug_bill", r"/account/bills/8/")
    check_visited_path(judge, traj, "nav_usage", r"/account/usage/")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")

    # answer ground truth
    check_answer_regex(judge, answer, "before_autopay", r"Auto Pay: Off|Auto Pay Off")
    check_answer_regex(judge, answer, "before_paper", r"Paper-free billing: Off|paper-free billing Off|Paper-free billing Off")
    check_answer_money(judge, answer, "autopay_discount", 10.00)
    check_answer_count_at_least(judge, answer, "autopay_methods",
        ["bank draft", "Verizon Visa Card"], 2)
    check_answer_regex(judge, answer, "paper_free_desc",
        r"[Rr]eceives? bills and notifications by email instead of paper mail")
    check_answer_regex(judge, answer, "confirm_msg",
        r"Auto Pay and billing preferences updated")
    check_answer_regex(judge, answer, "after_autopay", r"Auto Pay: Enrolled")
    check_answer_regex(judge, answer, "after_paper", r"Paper-free billing: On")
    check_answer_money(judge, answer, "sep_total", 176.46)
    check_answer_phrase(judge, answer, "sep_due", "2026-10-13")
    check_answer_money(judge, answer, "aug_total", 176.46)
    check_answer_money(judge, answer, "jul_total", 176.46)
    check_answer_regex(judge, answer, "protection_line", r"protection[^.]{0,40}Tyler|Tyler[^.]{0,40}protection")
    check_answer_regex(judge, answer, "aug_protection",
        r"(same|both|each|also)[^.]{0,200}Aug(ust)?|Aug(ust)?[^.]{0,200}(same|both|each|also)")
    check_answer_regex(judge, answer, "most_data", r"Tyler[^.]{0,80}(most|22\.1)")
    check_answer_money(judge, answer, "est_10a_mint", 210.00)

    # DB after-state: exact allowed delta
    check_only_tables_changed(judge, initial, after, {"users"})
    check_rows_changed(judge, initial, after, "users",
        [[3, "carol.d@test.com", "Carol Davis", None, "1290-4523", "postpaid",
          None, None, None, None, 1, 1, None]], "autopay_flags")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
