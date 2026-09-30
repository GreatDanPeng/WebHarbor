#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--2 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_2.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "USAppliance--2"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: both product pages and the cart.
    check_visited_path(judge, traj, "nav_jgbs66_product", r"/jgbs66rekss\.html")
    check_visited_path(judge, traj, "nav_bosch_product", r"/shs53cd5n")
    check_visited_path(judge, traj, "nav_cart", r"/cart\.php")
    # answer ground truth
    check_answer_money(judge, answer, "subtotal_3items", 2795)
    check_answer_any(judge, answer, "shipping_3items", ["FREE", "$0"])
    check_answer_money(judge, answer, "subtotal_after", 823)
    check_answer_money(judge, answer, "shipping_after", 99)
    check_answer_money(judge, answer, "inhome_upgrade", 199)
    check_answer_absent(judge, answer, "no_stale_shipping",
                        "shipping is free after the dishwasher removal and qty-1 change")
    check_only_tables_changed(judge, initial, after, ('cart_items',))
    # DB: exactly one cart row left (the range at qty 1), nothing else.
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, r"rx:^[0-9a-f]{32}$", None, 21476, 1, 0]],
                     "db_cart_final_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
