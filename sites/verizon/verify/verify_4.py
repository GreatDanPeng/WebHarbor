#!/usr/bin/env python3
"""Deterministic verifier for Verizon--4 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_4.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--4"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_gridwall", r"/smartphones/")
    check_visited_path(judge, traj, "nav_18p_pdp", r"/smartphones/apple-iphone-18-pro/$")
    check_visited_path(judge, traj, "nav_18p_configure", r"/smartphones/apple-iphone-18-pro/configure")
    check_visited_path(judge, traj, "nav_cart", r"/cart/")
    check_visited_path(judge, traj, "nav_18pm_pdp", r"/smartphones/apple-iphone-18-pro-max/$")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")

    # answer ground truth
    check_answer_money(judge, answer, "m12", 99.99)
    check_answer_money(judge, answer, "m24", 49.99)
    check_answer_money(judge, answer, "m48", 24.99)
    check_answer_money(judge, answer, "retail", 1199.99)
    check_answer_count_at_least(judge, answer, "colors", ["Burgundy", "Black", "Silver", "Glacier"], 4)
    check_answer_count_at_least(judge, answer, "storage", ["256 GB", "512 GB", "1 TB", "2 TB"], 4)
    check_answer_phrase(judge, answer, "ship", "Tue, Sep 29 - Fri, Oct 9")
    check_answer_any(judge, answer, "rating",
        ["4.2 out of 5 rating (93 reviews)", "4.2 (93 reviews)",
         "4.2 out of 5 (93 reviews)"])
    check_answer_phrase(judge, answer, "battery_line", "Typical use: Up to 24 hours")
    check_answer_regex(judge, answer, "longest_battery", r"Pro Max[^.]{0,60}(longest|battery)|battery[^.]{0,60}Pro Max")
    check_answer_money(judge, answer, "cart", 71.99)
    check_answer_money(judge, answer, "pm_36mo", 36.11)
    check_answer_money(judge, answer, "pm_retail", 1299.99)
    check_answer_phrase(judge, answer, "pm_ship", "Mon, Oct 12 - Fri, Oct 30")
    check_answer_money(judge, answer, "est_mint", 760.00)

    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
