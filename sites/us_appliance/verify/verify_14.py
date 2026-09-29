#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--14 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_14.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--14"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: Shop By Brand, home (brand strip), Viking and Cafe brand pages.
    check_visited_path(judge, traj, "nav_shopbybrand", r"/shopbybrand\.html")
    check_visited_path(judge, traj, "nav_home", r"/(\?|$)")
    check_visited_path(judge, traj, "nav_viking_brand", r"/brand/viking")
    check_visited_path(judge, traj, "nav_cafe_brand", r"/brand/cafe")
    # audit-rail deepening: the cheapest Cafe item's product page and the
    # Samsung brand page.
    check_visited_path(judge, traj, "nav_cafe_item", r"/cmb517p2ms1\.html")
    check_visited_path(judge, traj, "nav_samsung_brand", r"/brand/samsung")
    # answer ground truth
    check_answer_phrase(judge, answer, "top_brand", "General Electric")
    check_answer_number(judge, answer, "top_brand_count", 883)
    check_answer_number(judge, answer, "samsung_count", 698)
    check_answer_number(judge, answer, "cafe_count", 434)
    check_answer_phrase(judge, answer, "strip_cafe", "Cafe")
    check_answer_absent(judge, answer, "strip_no_samsung_confusion",
                        "Samsung is not in the home brand strip")
    check_answer_number(judge, answer, "viking_brand_page_count", 347)
    check_answer_phrase(judge, answer, "cafe_cheapest_name", "CVM517P2RS1")
    check_answer_money(judge, answer, "cafe_cheapest_price", 943)
    # audit-rail deepening: one feature of the cheapest Cafe item, its ZIP
    # 48083 availability answer, and the Samsung brand-page product count.
    check_answer_phrase(judge, answer, "cafe_item_feature", "Air Fry")
    check_answer_phrase(judge, answer, "cafe_item_zip_48083",
                        "QUICKSHIP - Ships in 1-2 business days")
    check_answer_phrase(judge, answer, "cafe_item_freeshipp",
                        "Order This Item Today And Get Free Standard Shipping")
    check_answer_number(judge, answer, "samsung_brand_count", 240)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
