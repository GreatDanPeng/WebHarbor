#!/usr/bin/env python3
"""Deterministic verifier for Verizon--12 (verizon).

Ground truth below is HARDCODED (frozen from the contributor's two
independent strict-caliber Playwright rounds on the r3 fix container
wh-verizon-fix3, seed md5 f2d20153c24b6945fb5203b81d7f1fb6) — never read
from tasks.jsonl. Navigation gates cover ONLY the surfaces the (r3
deepened) task text requires; answer anchors are page-verbatim with
tolerance for equally-honest renderings.
Usage: python3 verify_12.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--12"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_usage", r"/account/usage/")
    check_visited_any(judge, traj, "nav_plans",
                       [r"/plans/$", r"/plans/unlimited/$"])
    check_visited_path(judge, traj, "nav_plans_2lines", r"/plans/unlimited/\?lines=2")
    check_visited_path(judge, traj, "nav_gridwall", r"/smartphones/$")
    check_visited_path(judge, traj, "nav_p11p_pdp", r"/smartphones/google-pixel-11-pro/$")
    check_visited_path(judge, traj, "nav_18p_pdp", r"/smartphones/apple-iphone-18-pro/$")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")

    # answer ground truth
    check_answer_money(judge, answer, "alice_data", 31.40)
    check_answer_money(judge, answer, "alice_hotspot", 9.60)
    check_answer_money(judge, answer, "alice_cap", 10.00)
    check_answer_money(judge, answer, "mike_data", 12.20)
    check_answer_money(judge, answer, "mike_hotspot", 1.10)
    check_answer_regex(judge, answer, "closest", r"[Cc]losest[^.]{0,60}Alice|Alice[^.]{0,60}closest")
    check_answer_phrase(judge, answer, "alice_plan", "Simplicity Plan")
    check_answer_money(judge, answer, "alice_plan_cost", 30.00)
    check_answer_money(judge, answer, "two_lines_total", 60.00)
    check_answer_money(judge, answer, "p11p_retail", 1099.99)
    check_answer_money(judge, answer, "p11p_36mo", 30.55)
    check_answer_phrase(judge, answer, "p11p_battery", "Up to 34 hours")
    check_answer_any(judge, answer, "p11p_screen",
        ["6.3-inch Super Actua display", "Super Actua"])
    check_answer_any(judge, answer, "p11p_rating",
        ["3.8 out of 5 rating (71 reviews)", "3.8 (71 reviews)",
         "3.8 out of 5 (71 reviews)"])
    check_answer_money(judge, answer, "p18_24mo", 49.99)
    check_answer_phrase(judge, answer, "p18_ship", "Tue, Sep 29 - Fri, Oct 9")
    check_answer_money(judge, answer, "est_good", 650.00)

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
