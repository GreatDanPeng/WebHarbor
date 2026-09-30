#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--11 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_11.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--11"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: FAQ, the shipping answer's delivery link, the freedelivery
    # page, and the warranty answer's More Details page (audit-rail fix: the
    # /us-appliance-warranties.html landing now exists upstream-verbatim).
    check_visited_path(judge, traj, "nav_faq", r"/faq\.html")
    check_visited_path(judge, traj, "nav_freedelivery", r"/freedelivery\.html")
    check_visited_path(judge, traj, "nav_warranty_details",
                       r"/us-appliance-warranties\.html")
    # answer ground truth
    check_answer_phrase(judge, answer, "shipping_free", "YES")
    check_answer_number(judge, answer, "faq_threshold", 999)
    check_answer_number(judge, answer, "cancellation_window", 48)
    check_answer_number(judge, answer, "price_match_pct", 110)
    check_answer_count_at_least(judge, answer, "no_delivery_places",
                                ["Alaska", "Hawaii", "Puerto Rico",
                                 "US Virgin Islands", "FPO/APO"], 2)
    # r2 deepening: warranty handler + installation-not-included answers.
    check_answer_phrase(judge, answer, "warranty_handler", "manufacturer")
    check_answer_phrase(judge, answer, "installation_included",
                        "not part of our delivery")
    check_answer_money(judge, answer, "inhome_upgrade_price", 199)
    check_answer_number(judge, answer, "delivery_options_compared", 2)
    # audit-rail deepening: brand-new-or-refurbished answer, order-tracking
    # answer, and the warranty More Details page's offer.
    check_answer_phrase(judge, answer, "refurbished_answer",
                        "We only sell brand-new appliances sealed in the original manufacturer packaging")
    check_answer_phrase(judge, answer, "order_tracking_answer",
                        "we will send you tracking information")
    check_answer_count_at_least(judge, answer, "order_arrival_answer",
                                ["affiliated National Shippers",
                                 "UPS or FEDEX",
                                 "shipping partner will contact you"], 1)
    check_answer_phrase(judge, answer, "warranty_details_page",
                        "Learn More about US Appliance warranties")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
