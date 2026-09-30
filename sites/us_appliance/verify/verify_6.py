#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--6 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_6.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--6"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: deals page, biggest-cut product page, both on-sale
    # category pages with the on-sale facet applied.
    check_visited_path(judge, traj, "nav_deals", r"/hugepricecuts\.html")
    check_visited_path(judge, traj, "nav_biggest_cut_product", r"/hbc163ess")
    check_visited_path(judge, traj, "nav_frdore_onsale", r"/frdore\.html\?[^ ]*on_sale=1")
    check_visited_path(judge, traj, "nav_dishwasher_onsale", r"/dishwasher\.html\?[^ ]*on_sale=1")
    # audit-rail deepening: the Gas Ranges on-sale grid (sorted by price).
    check_visited_path(judge, traj, "nav_gasranges_onsale",
                       r"/gas-ranges\.html\?[^ ]*on_sale=1")
    # answer ground truth
    check_answer_phrase(judge, answer, "sale_headline", "Huge Fall Sale")
    check_answer_phrase(judge, answer, "rules_note",
                        "Manufacturer rules prevent us from showing the lowest prices until item is in cart")
    check_answer_count_at_least(judge, answer, "featured_brands",
                                ["LG", "Frigidaire", "GE", "KitchenAid"], 4)
    check_answer_phrase(judge, answer, "biggest_cut_name", "HBC163ESS")
    check_answer_money(judge, answer, "biggest_cut_now", 2095)
    check_answer_money(judge, answer, "biggest_cut_was", 3299)
    check_answer_money(judge, answer, "biggest_cut_savings", 1204)
    check_answer_number(judge, answer, "products_shown", 24)
    check_answer_number(judge, answer, "french_door_onsale", 217)
    check_answer_number(judge, answer, "dishwashers_onsale", 44)
    # audit-rail deepening: the biggest-cut product's ZIP availability answers
    # and the sorted on-sale Gas Ranges grid.
    check_answer_phrase(judge, answer, "biggest_cut_zip_48083",
                        "QUICKSHIP - Ships in 1-2 business days")
    check_answer_any(judge, answer, "biggest_cut_zip_96762",
                     ["We offer delivery to the continental United States only",
                      "continental United States only"])
    check_answer_number(judge, answer, "gas_ranges_onsale", 78)
    check_answer_phrase(judge, answer, "gas_onsale_cheapest_name", "NX60A6111SS")
    check_answer_money(judge, answer, "gas_onsale_cheapest_price", 774)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
