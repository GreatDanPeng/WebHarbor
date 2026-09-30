#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--17 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_17.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--17"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: a QuickShip product page (from the home QuickShip rail),
    # the second QuickShip item, the cart, and checkout (audit-rail
    # deepening).
    check_visited_any(judge, traj, "nav_quickship_product", [r"/tc5001wn\.html", r"/tc5003wn\.html"])
    check_visited_path(judge, traj, "nav_second_quickship", r"/frss2623as\.html")
    check_visited_path(judge, traj, "nav_cart", r"/cart\.php")
    check_visited_path(judge, traj, "nav_checkout", r"/checkout")
    # answer ground truth
    check_answer_phrase(judge, answer, "quickship_name", "TC5003WN")
    check_answer_money(judge, answer, "quickship_price", 1499)
    check_answer_phrase(judge, answer, "zip_48083",
                        "Good news — this item is available for delivery to your area")
    check_answer_any(judge, answer, "zip_96762",
                     ["We offer delivery to the continental United States only",
                      "continental United States only"])
    check_answer_phrase(judge, answer, "freeshipp_order_today",
                        "Order This Item Today And Get Free Standard Shipping")
    check_answer_money(judge, answer, "freeshipp_inhome", 199)
    check_answer_any(judge, answer, "cart_shipping_line", ["FREE", "$0"])
    check_answer_money(judge, answer, "cart_first_subtotal", 1499)
    # deepening: the second QuickShip item (FRSS2623AS, Now $1,208 / Was
    # $1,243) and the qty-2 first item -> subtotal 2x$1,499 + $1,208 =
    # $4,206 with free shipping; checkout prices Standard FREE / In-Home
    # $199 per order.
    check_answer_phrase(judge, answer, "second_quickship_name", "FRSS2623AS")
    check_answer_money(judge, answer, "second_quickship_price", 1208)
    check_answer_any(judge, answer, "second_quickship_was",
                     ["1,243", "Was $1,243.00"])
    check_answer_money(judge, answer, "cart_final_subtotal", 4206)
    check_answer_any(judge, answer, "cart_final_shipping", ["FREE", "$0"])
    check_answer_phrase(judge, answer, "checkout_standard",
                        "Standard Delivery")
    check_answer_any(judge, answer, "checkout_standard_price", ["FREE", "$0"])
    check_answer_phrase(judge, answer, "checkout_inhome",
                        "In-Home Delivery")
    check_answer_money(judge, answer, "checkout_inhome_price", 199)
    check_only_tables_changed(judge, initial, after, ('cart_items',))
    # DB: exactly two cart rows (the washer at qty 2 + the fridge at qty 1).
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, r"rx:^[0-9a-f]{32}$", None, 26475, 2, 0],
                      [None, r"rx:^[0-9a-f]{32}$", None, 20337, 1, 0]],
                     "db_cart_final_rows")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
