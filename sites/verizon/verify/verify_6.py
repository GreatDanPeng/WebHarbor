#!/usr/bin/env python3
"""Deterministic verifier for Verizon--6 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_6.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--6"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")
    check_visited_path(judge, traj, "nav_gridwall", r"/smartphones/")
    check_visited_path(judge, traj, "nav_s26_pdp", r"/smartphones/samsung-galaxy-s26/$")
    check_visited_path(judge, traj, "nav_s26_configure", r"/smartphones/samsung-galaxy-s26/configure")
    check_visited_path(judge, traj, "nav_cart", r"/cart/")

    # answer ground truth
    check_answer_money(judge, answer, "p11_good", 300.00)
    check_answer_money(judge, answer, "motog_good", 70.00)
    check_answer_money(judge, answer, "s26u_cracked", 190.00)
    check_answer_money(judge, answer, "combined_good", 370.00)
    check_answer_phrase(judge, answer, "good_definition", "minor wear, fully functional")
    check_answer_count_at_least(judge, answer, "credit_ways",
        ["instant credit", "account credit", "gift card"], 3)
    check_answer_money(judge, answer, "mail_days", 30.00)
    check_answer_money(judge, answer, "s26_retail", 899.99)
    check_answer_money(judge, answer, "s26_36mo", 24.99)
    check_answer_money(judge, answer, "cart", 48.74)

    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
