#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--9 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_9.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--9"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: free delivery page, the FAQ, and the GE JGBS66REKSS
    # product page (audit-rail deepening).
    check_visited_path(judge, traj, "nav_freedelivery", r"/freedelivery\.html")
    check_visited_path(judge, traj, "nav_faq", r"/faq\.html")
    check_visited_path(judge, traj, "nav_jgbs66_product", r"/jgbs66rekss\.html")
    # answer ground truth
    check_answer_number(judge, answer, "free_threshold", 999)
    check_answer_number(judge, answer, "fee_under", 99)
    check_answer_money(judge, answer, "inhome_price", 199)
    check_answer_phrase(judge, answer, "inhome_includes",
                        "brought inside and placed in an accessible room of your choice")
    check_answer_count_at_least(judge, answer, "delivery_times",
                                ["business days", "1-2", "3-5", "5-10", "7-14", "weeks"], 1)
    check_answer_money(judge, answer, "rate_microwave", 99)
    check_answer_money(judge, answer, "rate_accessories", 9)
    check_answer_phrase(judge, answer, "rate_small", "5.99")
    check_answer_phrase(judge, answer, "po_box_rule", "We do not deliver to P.O. Boxes")
    check_answer_count_at_least(judge, answer, "additional_charges",
                                ["stairs", "narrow", "hookup", "disconnect",
                                 "haul-away", "additional delivery charges"], 1)
    check_answer_any(judge, answer, "no_delivery_place",
                     ["Alaska", "Hawaii", "Puerto Rico"])
    check_answer_phrase(judge, answer, "sales_tax", "sales tax")
    # r2 deepening: FAQ return-policy cancellation window + order-arrival
    # small-item carriers.
    check_answer_number(judge, answer, "faq_cancellation_window", 48)
    check_answer_phrase(judge, answer, "faq_cancellation_window_phrase", "48 hours")
    check_answer_phrase(judge, answer, "small_item_carriers", "UPS or FEDEX")
    # audit-rail deepening: the product page's Free Shipping panel and
    # Check Availability answers for both ZIPs.
    check_answer_phrase(judge, answer, "product_freeshipp",
                        "Order This Item Today And Get Free Standard Shipping")
    check_answer_phrase(judge, answer, "product_zip_48083",
                        "Good news — this item is available for delivery to your area")
    check_answer_any(judge, answer, "product_zip_96762",
                     ["We offer delivery to the continental United States only",
                      "continental United States only"])
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
