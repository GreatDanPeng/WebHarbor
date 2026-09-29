#!/usr/bin/env python3
"""Deterministic verifier for Verizon--13 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_13.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--13"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_change_plan", r"/account/lines/8/change-plan")
    check_visited_path(judge, traj, "nav_usage", r"/account/usage/")
    check_visited_path(judge, traj, "nav_prepaid", r"/prepaid/")
    check_visited_path(judge, traj, "nav_bills", r"/account/bills/$")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")

    # answer ground truth
    check_answer_phrase(judge, answer, "current_plan", "Unlimited Plus")
    check_answer_money(judge, answer, "current_cost", 70.00)
    check_answer_count_at_least(judge, answer, "plan_options",
        ["Simplicity Plan — $30.00/mo", "Talk & Text — $35.00/mo",
         "15 GB — $45.00/mo", "Unlimited — $60.00/mo",
         "Unlimited Plus — $70.00/mo"], 5)
    check_answer_regex(judge, answer, "confirm_msg", r"Plan for Dana changed to Unlimited")
    check_answer_money(judge, answer, "new_cost", 60.00)
    check_answer_money(judge, answer, "new_hotspot_cap", 5.00)
    check_answer_money(judge, answer, "new_data_cap", 60.00)
    check_answer_money(judge, answer, "loyalty_3mo", 5.00)
    check_answer_money(judge, answer, "loyalty_9mo_add", 5.00)
    check_answer_money(judge, answer, "loyalty_11mo_total", 10.00)
    check_answer_money(judge, answer, "sep_total", 114.08)
    check_answer_phrase(judge, answer, "sep_status", "due")
    check_answer_money(judge, answer, "est_good", 610.00)

    # DB after-state: exact allowed delta
    check_only_tables_changed(judge, initial, after, {"lines", "usage"})
    check_rows_changed(judge, initial, after, "lines",
        [[8, 4, "Dana", None, None, 4, "active", None]], "line_plan")
    check_rows_changed(judge, initial, after, "usage",
        [[8, 8, "Sep 2026", "26.4", "60.00", "7.2", "5", 261, 949]], "usage_caps")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
