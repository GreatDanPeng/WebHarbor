#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--11 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_11.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_answer_regex, check_attributed_money, check_only_tables_changed,
    check_read_only, check_rows_added, check_screenshots,
    check_seed_contract, check_section_phrase, check_trajectory_identity,
    check_visited_any, check_visited_path, final_answer, run_verifier,
)

TASK_ID = "USPS.com--11"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_store", r"/store")
    check_visited_path(judge, traj, "nav_bcr_product", r"/store/product/breast-cancer-research-stamps")
    check_visited_path(judge, traj, "nav_new_releases", r"/store/stamps-new-releases")
    check_visited_path(judge, traj, "nav_diwali_product", r"/store/product/diwali-2026-stamps")
    check_visited_path(judge, traj, "nav_cart", r"/store/cart")
    check_visited_path(judge, traj, "nav_checkout", r"/store/checkout")
    check_answer_money(judge, answer, "bcr_price", 20.00)
    check_answer_number(judge, answer, "bcr_sku", 555304)
    check_answer_phrase(judge, answer, "bcr_format", "Sheet of 20")
    check_answer_money(judge, answer, "diwali_price", 16.40)
    check_answer_money(judge, answer, "cart_total", 69.20)
    check_answer_regex(judge, answer, "order_number", r"W[0-9A-F]{7}")
    check_answer_phrase(judge, answer, "order_email", "me@example.com")
    # audit deepening (ordinal 57): a third sheet (U.S. Flag 2026) joins
    # the cart, so the line totals and order total move with it.
    check_visited_path(judge, traj, "nav_all_stamps", r"/store/stamps-all")
    check_visited_path(judge, traj, "nav_flag_product",
                       r"/store/product/us-flag-2026-stamps")
    check_answer_money(judge, answer, "flag_price", 16.40)
    check_answer_money(judge, answer, "line_bcr", 20.00)
    check_answer_money(judge, answer, "line_diwali", 32.80)
    check_answer_money(judge, answer, "line_flag", 16.40)
    check_only_tables_changed(judge, initial, after, {"store_orders"})
    check_rows_added(judge, initial, after, "store_orders", [
        [None, "rx:^W[0-9A-F]{7}$", None, "me@example.com", "Processing",
         69.2, "2026-09-28", None],
    ], "order_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
