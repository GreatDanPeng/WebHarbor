#!/usr/bin/env python3
"""Deterministic verifier for Verizon--1 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_1.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--1"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_prepaid", r"/prepaid/")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")
    check_visited_path(judge, traj, "nav_gridwall_samsung_desc", r"/smartphones/\?brand=Samsung&sort=price-desc")
    check_visited_path(judge, traj, "nav_zfold8_pdp", r"/smartphones/samsung-galaxy-z-fold8/$")
    check_visited_path(judge, traj, "nav_zfold8_configure", r"/smartphones/samsung-galaxy-z-fold8/configure")
    check_visited_path(judge, traj, "nav_cart", r"/cart/")

    # answer ground truth
    # prepaid plans
    check_answer_money(judge, answer, "tt_autopay", 30.00)
    check_answer_money(judge, answer, "g15_autopay", 35.00)
    check_answer_money(judge, answer, "up_autopay", 60.00)
    check_answer_money(judge, answer, "up_base", 70.00)
    check_answer_money(judge, answer, "up_3mo_loyalty", 65.00)
    check_answer_money(judge, answer, "up_9mo_loyalty", 60.00)
    check_answer_any(judge, answer, "up_hotspot", ["25 GB premium Mobile Hotspot", "Mobile Hotspot: 25 GB", "hotspot 25 GB"])
    check_answer_count_at_least(judge, answer, "up_feature",
        ["5G Ultra Wideband", "50 GB premium network access",
         "Global Choice at no additional cost"], 1)
    check_answer_money(judge, answer, "autopay_discount", 10.00)
    check_answer_money(judge, answer, "tt_discount", 5.00)
    check_answer_phrase(judge, answer, "featured_deal", "iPhone 16e")
    check_answer_money(judge, answer, "deal_price", 349.99)
    check_answer_phrase(judge, answer, "deal_end", "9/30/26")
    check_answer_regex(judge, answer, "price_lock", r"3[- ]year price lock")
    check_answer_money(judge, answer, "est_17e_good", 240.00)
    check_answer_phrase(judge, answer, "second_samsung", "Galaxy Z Fold8")
    check_answer_number_absent(judge, answer, "second_samsung_not_ultra_hint", 2099.99)
    check_answer_money(judge, answer, "cart_monthly", 218.33)

    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
