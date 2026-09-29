#!/usr/bin/env python3
"""Deterministic verifier for Verizon--2 (verizon).

Ground truth below is HARDCODED (frozen from the contributor's two
independent strict-caliber Playwright rounds on the r3 fix container
wh-verizon-fix3, seed md5 f2d20153c24b6945fb5203b81d7f1fb6) — never read
from tasks.jsonl. Navigation gates cover ONLY the surfaces the (r3
deepened) task text requires; answer anchors are page-verbatim with
tolerance for equally-honest renderings.
Usage: python3 verify_2.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--2"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_prepaid", r"/prepaid/")
    check_visited_any(judge, traj, "nav_plans",
                       [r"/plans/$", r"/plans/unlimited/$"])
    check_visited_path(judge, traj, "nav_p11_pdp", r"/smartphones/google-pixel-11/$")
    check_visited_path(judge, traj, "nav_p11_configure", r"/smartphones/google-pixel-11/configure")
    check_visited_path(judge, traj, "nav_cart", r"/cart/")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")
    check_visited_path(judge, traj, "nav_support", r"/support/$")
    check_visited_path(judge, traj, "nav_return_policy", r"/support/return_policy/")

    # answer ground truth
    check_answer_money(judge, answer, "tt_autopay", 30.00)
    check_answer_money(judge, answer, "g15_autopay", 35.00)
    check_answer_phrase(judge, answer, "cheapest_5guw_name", "Unlimited")
    check_answer_money(judge, answer, "cheapest_5guw_base", 60.00)
    check_answer_money(judge, answer, "cheapest_5guw_autopay", 50.00)
    check_answer_any(judge, answer, "cheapest_5guw_hotspot",
        ["5 GB Mobile Hotspot", "Mobile Hotspot: 5 GB", "hotspot 5 GB"])
    check_answer_count_at_least(judge, answer, "cheapest_5guw_feature",
        ["Includes 5G Ultra Wideband", "Unlimited talk, text and data"], 1)
    check_answer_money(judge, answer, "simplicity_1line", 30.00)
    check_answer_money(judge, answer, "cart_p11", 97.49)
    check_answer_money(judge, answer, "est_10a_cracked", 45.00)
    check_answer_money(judge, answer, "est_10a_good", 160.00)
    # return policy: wireless-device restocking fee + return window
    check_answer_regex(judge, answer, "restocking_fee",
        r"restocking fee[^.]{0,120}\$50|\$50[^.]{0,120}restocking|restocking fee of \$50")
    check_answer_money(judge, answer, "restocking_amount", 50.00)
    check_answer_regex(judge, answer, "return_window", r"30[ -]day|30 days")

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
