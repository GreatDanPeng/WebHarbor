#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--10 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_10.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--10"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: testimonials pages 1-4, the GE JGBS66REKSS reviews tab,
    # the FAQ who-is question, and About Us (audit-rail deepening).
    check_visited_path(judge, traj, "nav_testimonials", r"/testimonials\.html")
    check_visited_path(judge, traj, "nav_testimonials_p2", r"/testimonials\.html\?page=2")
    check_visited_path(judge, traj, "nav_testimonials_p3", r"/testimonials\.html\?page=3")
    check_visited_path(judge, traj, "nav_testimonials_p4", r"/testimonials\.html\?page=4")
    check_visited_path(judge, traj, "nav_jgbs66_product", r"/jgbs66rekss\.html")
    check_visited_path(judge, traj, "nav_faq", r"/faq\.html")
    check_visited_path(judge, traj, "nav_about_us", r"/whyusappliance\.html")
    # answer ground truth
    check_answer_phrase(judge, answer, "total_reviews", "20,841")
    check_answer_phrase(judge, answer, "avg_rating", "4.9")
    check_answer_number(judge, answer, "pct_45", 97)
    check_answer_number(judge, answer, "founded", 1963)
    check_answer_number(judge, answer, "online_since", 1999)
    check_answer_phrase(judge, answer, "john_rating", "5")
    check_answer_any(judge, answer, "john_date", ["09-20-26", "09-20-2026"])
    check_answer_phrase(judge, answer, "john_comment",
                        "Easy to browse Web site")
    check_answer_phrase(judge, answer, "john_verified", "Verified Customer")
    check_answer_phrase(judge, answer, "page2_first_reviewer", "Calvin D")
    # r2 deepening: another page-1 review with its star rating, the page-2
    # first review's date, and the recency comparison vs John's review.
    check_answer_any(judge, answer, "other_page1_review",
                     ["Have looked everywhere for this model",
                      "Site easy to maneuver and easy purchase experience",
                      "Great experience and found part quickly",
                      "Good price, free shipping",
                      "Very quick and easy",
                      "I needed to call the company",
                      "Easy to order",
                      "Excellent shopping experience"])
    check_answer_any(judge, answer, "page2_first_date",
                     ["08-03-26", "08-03-2026", "August 3, 2026"])
    check_answer_any(judge, answer, "john_more_recent",
                     ["more recent", "more recent than", "newer than",
                      "John's review is more recent"])
    # audit-rail deepening: pages 3/4 first reviews, the product reviews
    # tab, and the FAQ who-is + About Us customer counts.
    check_answer_phrase(judge, answer, "page3_first_reviewer", "A Reviewer")
    check_answer_any(judge, answer, "page3_first_date", ["06-22-26", "06-22-2026"])
    check_answer_phrase(judge, answer, "page3_first_comment", "Fast and easy process")
    check_answer_phrase(judge, answer, "page4_first_reviewer", "Eric B.")
    check_answer_any(judge, answer, "page4_first_date", ["05-21-26", "05-21-2026"])
    check_answer_phrase(judge, answer, "page4_first_comment",
                        "It was easy to order and I like the price you gave")
    check_answer_phrase(judge, answer, "product_reviews_tab",
                        "No reviews yet for this model")
    check_answer_phrase(judge, answer, "product_freeshipp",
                        "Order This Item Today And Get Free Standard Shipping")
    check_answer_phrase(judge, answer, "product_zip_48083",
                        "Good news — this item is available for delivery to your area")
    check_answer_phrase(judge, answer, "faq_whois_customers",
                        "more than 300,000 customers")
    check_answer_phrase(judge, answer, "about_customers",
                        "hundreds of thousands customers")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
