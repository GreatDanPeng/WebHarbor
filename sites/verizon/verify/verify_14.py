#!/usr/bin/env python3
"""Deterministic verifier for Verizon--14 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_14.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--14"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_gridwall_samsung_asc", r"/smartphones/\?brand=Samsung&sort=price-asc")
    check_visited_path(judge, traj, "nav_account", r"/account/$")
    check_visited_path(judge, traj, "nav_add_line", r"/account/add-line/")
    check_visited_any(judge, traj, "nav_plans",
                       [r"/plans/$", r"/plans/unlimited/$"])
    check_visited_path(judge, traj, "nav_plans_3lines", r"/plans/unlimited/\?lines=3")

    # answer ground truth
    check_answer_phrase(judge, answer, "cheapest_samsung", "Samsung Galaxy A17 5G")
    check_answer_money(judge, answer, "cheapest_retail", 249.99)
    check_answer_regex(judge, answer, "confirm_msg", r"New line added for Mom with Simplicity Plan")
    row = db_one(after, "SELECT phone_number FROM lines WHERE id = (SELECT MAX(id) FROM lines)")
    check_answer_confirmation(judge, answer, "mom_phone", row[0] if row else None, "(206)")
    check_answer_number(judge, answer, "lines_now", 3)
    check_answer_money(judge, answer, "plan_price", 30.00)
    check_answer_money(judge, answer, "three_lines_total", 90.00)

    # DB after-state: exact allowed delta
    check_only_tables_changed(judge, initial, after, {"lines", "usage"})
    check_rows_added(judge, initial, after, "lines",
        [[None, 1, "Mom", r"rx:^\(206\) 555-[0-9]{4}$", 18, 1, "activating",
          "2026-09-29"]], "mom_line")
    check_rows_added(judge, initial, after, "usage",
        [[None, None, "Sep 2026", "0.0", None, "0.0", "10", 0, 0]], "mom_usage")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
