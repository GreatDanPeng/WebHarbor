#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--8 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_8.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--8"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: financing center, the finance offers page, the Learn More
    # page, and the GE JGBS66REKSS product page (audit-rail deepening).
    check_visited_path(judge, traj, "nav_finance_center", r"/financecenter\.html")
    check_visited_path(judge, traj, "nav_finance_offers", r"/financeoffers\.html")
    check_visited_path(judge, traj, "nav_learn_more", r"/contactus2\.html")
    check_visited_path(judge, traj, "nav_jgbs66_product", r"/jgbs66rekss\.html")
    # answer ground truth
    check_answer_phrase(judge, answer, "finance_intro",
                        "Finance your next appliance purchase with special financing promotions from leading brands")
    check_answer_phrase(judge, answer, "card_special", "Special Financing Offers")
    check_answer_any(judge, answer, "card_lease",
                     ["Progressive Leasing", "Flexible Lease To Own Options"])
    check_answer_number(judge, answer, "brands_15month", 8)
    check_answer_phrase(judge, answer, "headline_15",
                        "0% Interest If Paid In Full In 15 Months")
    check_answer_phrase(judge, answer, "not_paid_rule",
                        "Interest will be charged to your account from the purchase date")
    check_answer_count_at_least(judge, answer, "eligible_brands",
                                ["Bosch", "GE", "Cafe", "Frigidaire", "Electrolux",
                                 "KitchenAid", "Whirlpool", "Maytag"], 3)
    check_answer_phrase(judge, answer, "storewide_headline", "Storewide Special Finance Offer")
    check_answer_phrase(judge, answer, "storewide_period", "6 Months")
    check_answer_number(judge, answer, "storewide_min", 200)
    # easy-step headings: the r1 honest fixture paraphrased the on-page steps
    # ("choose your appliances, apply, get instant decision"); the pages
    # verbatim show "1. Apply Now / 2. Approval / 3. Call to Order". Both
    # readings are defensible — accept either token set (audit-rail fix for
    # an over-frozen paraphrase key).
    check_answer_count_at_least(judge, answer, "easy_steps",
                                ["Choose Your", "Apply", "Get Instant", "Shop",
                                 "Apply Now", "Approval", "Call to Order",
                                 "decision in minutes", "Account Number"], 2)
    check_answer_phrase(judge, answer, "call_to_order", "877-628-9913")
    check_answer_phrase(judge, answer, "qualifying_rule", "qualifying purchase")
    # audit-rail deepening: Progressive Leasing's offer, the Learn More
    # page's expert-advice note, and the GE product page's finance note /
    # Free Shipping panel / ZIP availability answers.
    check_answer_phrase(judge, answer, "progressive_offers", "Flexible Lease To Own Options")
    check_answer_phrase(judge, answer, "learn_more_note",
                        "Expert Advice from a real person!")
    check_answer_phrase(judge, answer, "product_finance_note",
                        "15 Months Special Finance Offer")
    check_answer_phrase(judge, answer, "product_freeshipp",
                        "Order This Item Today And Get Free Standard Shipping")
    check_answer_phrase(judge, answer, "product_zip_48083",
                        "Good news — this item is available for delivery to your area")
    check_answer_any(judge, answer, "product_zip_96762",
                     ["We offer delivery to the continental United States only",
                      "continental United States only"])
    check_answer_phrase(judge, answer, "product_zip_90210",
                        "Good news — this item is available for delivery to your area")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
