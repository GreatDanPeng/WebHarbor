#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--0 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_0.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--0"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: Cooking -> Ranges -> Gas Ranges grid, sort by price applied,
    # then the GE product page.
    check_visited_path(judge, traj, "nav_gas_ranges", r"/gas-ranges\.html")
    check_visited_any(judge, traj, "nav_sort_priceasc",
                      [r"sort=priceasc", r"sort=Price%3A\+Ascending"])
    check_visited_path(judge, traj, "nav_jgbs66_product", r"/jgbs66rekss\.html")
    # answer ground truth
    check_answer_number(judge, answer, "gas_range_count", 297)
    # "Sort them by price and report the name and price of the cheapest one
    # listed" (r2 wording @35376490): single reading — the cheapest after the
    # price-ascending sort is the Frigidaire FCRG3051BS at $703. The old
    # featured-page reading (Electrolux ECFG3068AS $2,979) is no longer
    # defensible because the task explicitly requires the sort.
    check_answer_phrase(judge, answer, "cheapest_name", "FCRG3051BS")
    check_answer_money(judge, answer, "cheapest_price", 703)
    check_answer_money(judge, answer, "jgbs66_price", 823)
    check_answer_phrase(judge, answer, "promo_note", "Sale ends Sept 30")
    check_answer_count_at_least(judge, answer, "features",
                                ["steam clean", "steam-cleaning the oven",
                                 "edge to edge", "self-clean"], 1)
    check_answer_phrase(judge, answer, "zip_48083",
                        "Good news — this item is available for delivery to your area")
    check_answer_any(judge, answer, "zip_96762",
                     ["We offer delivery to the continental United States only",
                      "continental United States only"])
    # audit-rail deepening: third ZIP (90210) + the product page's Free
    # Shipping panel ordering-today promise.
    check_answer_phrase(judge, answer, "zip_90210",
                        "Good news — this item is available for delivery to your area")
    check_answer_phrase(judge, answer, "freeshipp_order_today",
                        "Order This Item Today And Get Free Standard Shipping")
    check_answer_phrase(judge, answer, "freeshipp_any_item",
                        "we will ship the entire order for free no matter how many appliances you order")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
