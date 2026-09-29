#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--15 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_15.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--15"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the range product page, BOTH the Black and Slate variant
    # pages, and the cart (audit-rail deepening).
    check_visited_path(judge, traj, "nav_jgbs66_product", r"/jgbs66rekss\.html")
    check_visited_path(judge, traj, "nav_variant_black", r"/jgbs66dekbb")
    check_visited_path(judge, traj, "nav_variant_slate", r"/jgbs66eekes")
    check_visited_path(judge, traj, "nav_cart", r"/cart\.php")
    # answer ground truth
    check_answer_count_at_least(judge, answer, "color_options",
                                ["Black", "White", "Slate"], 3)
    check_answer_phrase(judge, answer, "sale_note", "Sale ends Sept 30")
    check_answer_phrase(judge, answer, "black_variant_name", "JGBS66DEKBB")
    check_answer_money(judge, answer, "black_variant_price", 823)
    check_answer_money(judge, answer, "slate_variant_price", 923)
    check_answer_phrase(judge, answer, "fbt_first_name", "JGBS66EEKES")
    check_answer_money(judge, answer, "fbt_first_price", 923)
    check_answer_phrase(judge, answer, "zip_48083",
                        "Good news — this item is available for delivery to your area")
    # deepened cart state: range qty 2 ($823 x 2) + the FBT slate range at
    # qty 1 ($923) -> subtotal $2,569, free shipping (over $999).
    check_answer_money(judge, answer, "cart_final_subtotal", 2569)
    check_answer_any(judge, answer, "cart_final_shipping", ["FREE", "$0"])
    check_answer_money(judge, answer, "cart_range_line_total", 1646)
    check_only_tables_changed(judge, initial, after, ('cart_items',))
    # DB: exactly two cart rows (the stainless range at qty 2 + the FBT
    # slate range at qty 1).
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, r"rx:^[0-9a-f]{32}$", None, 21476, 2, 0],
                      [None, r"rx:^[0-9a-f]{32}$", None, 21475, 1, 0]],
                     "db_cart_final_rows")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
