#!/usr/bin/env python3
"""Deterministic verifier for Verizon--0 (verizon).

Ground truth below is HARDCODED (frozen from the contributor's two
independent strict-caliber Playwright rounds on the r3 fix container
wh-verizon-fix3, seed md5 f2d20153c24b6945fb5203b81d7f1fb6) — never read
from tasks.jsonl. Navigation gates cover ONLY the surfaces the (r3
deepened) task text requires; answer anchors are page-verbatim with
tolerance for equally-honest renderings.
Usage: python3 verify_0.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--0"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_any(judge, traj, "nav_plans",
                       [r"/plans/$", r"/plans/unlimited/$"])
    check_visited_path(judge, traj, "nav_plans_4lines", r"/plans/unlimited/\?lines=4")
    check_visited_path(judge, traj, "nav_18p_pdp", r"/smartphones/apple-iphone-18-pro/$")
    check_visited_path(judge, traj, "nav_18p_configure", r"/smartphones/apple-iphone-18-pro/configure")
    check_visited_path(judge, traj, "nav_cart", r"/cart/")
    check_visited_path(judge, traj, "nav_gridwall", r"/smartphones/")
    check_visited_path(judge, traj, "nav_p10a_pdp", r"/smartphones/google-pixel-10a/$")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")

    # answer ground truth
    # Simplicity 4-line totals + note + features + Auto Pay methods + hero
    check_answer_money(judge, answer, "total_4lines", 120.00)
    check_answer_money(judge, answer, "per_line", 30.00)
    check_answer_phrase(judge, answer, "price_note", "After AutoPay and $15/mo switch discount")
    check_answer_count_at_least(judge, answer, "features",
        ["5G Ultra Wideband", "Verizon Dollars", "Mexico & Canada talk, text & data",
         "Satellite texting", "10 GB mobile hotspot data",
         "Call filter & Verizon Family"], 3)
    check_answer_phrase(judge, answer, "autopay_methods", "ACH bank draft or the Verizon Visa Card")
    check_answer_money(judge, answer, "hero_allin", 80.00)
    # iPhone 18 Pro retail + colors + configured cart
    check_answer_money(judge, answer, "retail_18p", 1199.99)
    check_answer_count_at_least(judge, answer, "colors_18p",
        ["Burgundy", "Black", "Silver", "Glacier"], 4)
    check_answer_money(judge, answer, "cart_18p", 146.99)
    # cheapest Google phone 36-month price + rating
    check_answer_phrase(judge, answer, "cheapest_google", "Pixel 10a")
    check_answer_money(judge, answer, "cheapest_google_36mo", 13.88)
    check_answer_any(judge, answer, "cheapest_google_rating",
        ["4.2 out of 5 rating (31 reviews)", "4.2 (31 reviews)",
         "4.2 out of 5 (31 reviews)"])
    # family trade-in: Apple iPhone 17e in Mint condition
    check_answer_money(judge, answer, "est_17e_mint", 300.00)

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
