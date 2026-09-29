#!/usr/bin/env python3
"""Deterministic verifier for Verizon--3 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_3.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--3"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_gridwall_samsung_asc", r"/smartphones/\?brand=Samsung&sort=price-asc")
    check_visited_path(judge, traj, "nav_a17_pdp", r"/smartphones/samsung-galaxy-a17-5g/$")
    check_visited_path(judge, traj, "nav_a17_configure", r"/smartphones/samsung-galaxy-a17-5g/configure")
    check_visited_path(judge, traj, "nav_cart", r"/cart/")
    check_visited_path(judge, traj, "nav_gridwall_apple", r"/smartphones/\?brand=Apple")
    check_visited_path(judge, traj, "nav_17e_pdp", r"/smartphones/apple-iphone-17e/$")
    check_visited_path(judge, traj, "nav_17e_configure", r"/smartphones/apple-iphone-17e/configure")

    # answer ground truth
    check_answer_number(judge, answer, "samsung_count", 7)
    check_answer_phrase(judge, answer, "cheapest_name", "Samsung Galaxy A17 5G")
    check_answer_money(judge, answer, "cheapest_full_retail", 249.99)
    check_answer_money(judge, answer, "cheapest_36mo", 6.94)
    check_answer_phrase(judge, answer, "dear_name", "Z Fold8 Ultra")
    check_answer_money(judge, answer, "dear_full_retail", 2099.99)
    check_answer_phrase(judge, answer, "cheapest_storage", "128 GB")
    check_answer_any(judge, answer, "cheapest_rating",
        ["4.2 out of 5 rating (3500 reviews)", "4.2 (3.5K reviews)",
         "4.2 out of 5 (3500 reviews)"])
    check_answer_phrase(judge, answer, "cheapest_ship", "Free shipping by Thursday with new line")
    check_answer_money(judge, answer, "cart_total", 49.41)
    check_answer_phrase(judge, answer, "apple_name", "iPhone 17e")
    check_answer_money(judge, answer, "apple_full_retail", 699.99)
    check_answer_money(judge, answer, "combined_total", 98.85)

    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
