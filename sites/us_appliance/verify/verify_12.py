#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--12 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_12.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--12"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the GE product page, the cart page (r2), and the price
    # match page.
    check_visited_path(judge, traj, "nav_jgbs66_product", r"/jgbs66rekss\.html")
    check_visited_path(judge, traj, "nav_cart", r"/cart\.php")
    check_visited_path(judge, traj, "nav_price_match", r"/price-match-request\.html")
    # answer ground truth
    check_answer_money(judge, answer, "jgbs66_price", 823)
    # r2 deepening: cart subtotal / shipping charge / free-delivery
    # qualification (single $823 range is under the $999 threshold).
    check_answer_money(judge, answer, "cart_subtotal", 823)
    check_answer_money(judge, answer, "cart_shipping_charge", 99)
    check_answer_any(judge, answer, "free_delivery_qualification",
                     ["not qualify", "does not qualify", "doesn't qualify",
                      "not eligible", "under $999", "ship for $99",
                      "ships for $99"])
    check_answer_phrase(judge, answer, "price_match_promise",
                        "match 110% of the difference")
    # audit-rail deepening: the product page's ZIP 48083 availability answer
    # and the Free Shipping panel's ordering-today promise.
    check_answer_phrase(judge, answer, "product_zip_48083",
                        "Good news — this item is available for delivery to your area")
    check_answer_phrase(judge, answer, "product_freeshipp",
                        "Order This Item Today And Get Free Standard Shipping")
    check_answer_phrase(judge, answer, "confirmation_heading", "Request Received")
    check_answer_phrase(judge, answer, "summary_product",
                        'GE JGBS66REKSS 30" Gas Range')
    # r2 deepening: the honest walk now leaves BOTH a cart row and the price
    # match request row (previously only price_match_requests).
    check_only_tables_changed(judge, initial, after,
                              ('cart_items', 'price_match_requests'))
    # DB: exactly one cart row (the range at qty 1).
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, r"rx:^[0-9a-f]{32}$", None, 21476, 1, 0]],
                     "db_cart_row")
    # DB: exactly one price match request row.
    check_rows_added(judge, initial, after, "price_match_requests",
                     [[None, "Alex Rivera", "alex.r@example.com", None,
                       'GE JGBS66REKSS 30" Gas Range', "Big Box Store", 799.0,
                       None, r"rx:^20\d\d-\d\d-\d\d$"]], "db_price_match_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
