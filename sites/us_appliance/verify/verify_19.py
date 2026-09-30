#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--19 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_19.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--19"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: contact page, customer service hub, return policy page,
    # the FAQ's return/warranty/installation questions, and the Track Your
    # Order / Free Shipping / Price Match / Service Plans pages
    # (audit-rail deepening).
    check_visited_path(judge, traj, "nav_contact", r"/contactus2\.html")
    check_visited_path(judge, traj, "nav_customer_service", r"/cusser\.html")
    check_visited_path(judge, traj, "nav_return_policy", r"/returninformation\.html")
    check_visited_path(judge, traj, "nav_faq", r"/faq\.html")
    check_visited_path(judge, traj, "nav_tracking", r"/ordertracking\.html")
    check_visited_path(judge, traj, "nav_freedelivery", r"/freedelivery\.html")
    check_visited_path(judge, traj, "nav_price_match", r"/price-match-request\.html")
    check_visited_path(judge, traj, "nav_service_plans", r"/warrantyoptions\.html")
    # answer ground truth
    check_answer_phrase(judge, answer, "newsletter_confirmation",
                        "Thanks! You are signed up for deals and offers")
    check_answer_count_at_least(judge, answer, "sales_hours",
                                ["8am - 6pm EST", "9am - 6pm EST", "8am-6pm EST",
                                 "9am-6pm EST"], 2)
    check_answer_phrase(judge, answer, "phone_lines", "877-628-9913")
    check_answer_phrase(judge, answer, "mailing_address", "111 Corporate Drive")
    check_answer_phrase(judge, answer, "mailing_city_state", "Auburn Hills, MI 48326")
    check_answer_phrase(judge, answer, "fax", "(248) 364-0701")
    check_answer_count_at_least(judge, answer, "help_sections",
                                ["Ordering", "Delivery", "About Us", "Returns",
                                 "Privacy", "Contact Us", "After Sales Help"], 5)
    check_answer_phrase(judge, answer, "track_order_section", "Delivery")
    check_answer_number(judge, answer, "return_window", 30)
    check_answer_number(judge, answer, "restocking_fee", 10)
    # r2 deepening: service-department hours (the difference vs sales is no
    # longer asked by the audit-rail wording; both hour sets are checked).
    check_answer_count_at_least(judge, answer, "service_hours",
                                ["9am - 6pm EST", "9am-6pm EST", "9am - 6pm",
                                 "9 am - 6 pm"], 1)
    check_answer_number(judge, answer, "damage_report_window", 24)
    check_answer_phrase(judge, answer, "damage_report_window_phrase", "24 hours")
    check_answer_count_at_least(judge, answer, "all_sales_final_items",
                                ["overstock", "closeout", "installation parts",
                                 "clearance"], 4)
    # audit-rail deepening: the FAQ's return/warranty/installation answers
    # and the four support pages.
    check_answer_number(judge, answer, "faq_cancellation_window", 48)
    check_answer_phrase(judge, answer, "faq_warranty_handler",
                        "manufacturer will repair or replace")
    check_answer_phrase(judge, answer, "faq_installation_included",
                        "not part of our delivery")
    check_answer_phrase(judge, answer, "carrier_note",
                        "24-48 hours for the shipping company to post the tracking information in their systems")
    check_answer_phrase(judge, answer, "inhome_price_per_order",
                        "$199 / order")
    check_answer_phrase(judge, answer, "match_promise",
                        "match 110% of the difference")
    check_answer_phrase(judge, answer, "plan_offer",
                        "Service Protection plans must be purchased in conjuction with a new appliance")
    check_only_tables_changed(judge, initial, after, ('newsletter_subscribers',))
    # DB: exactly one newsletter subscriber.
    check_rows_added(judge, initial, after, "newsletter_subscribers",
                     [[None, "news.hound@example.com", r"rx:^20\d\d-\d\d-\d\d$"]],
                     "db_newsletter_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
