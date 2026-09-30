#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--1 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_1.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--1"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: dishwasher search, advanced search (Bosch + price band), a
    # Bosch product page from those results.
    check_visited_path(judge, traj, "nav_search", r"/search\.php\?[^ ]*search_query=dishwasher")
    check_visited_path(judge, traj, "nav_adv_search",
                       r"/search\.php\?[^ ]*(mode=1|brand=Bosch|price_from=500)")
    check_visited_any(judge, traj, "nav_bosch_product",
                      [r"/duh30253uc", r"/she41cm2n", r"/she41cm5n", r"/she41cm6n"])
    # answer ground truth
    check_answer_number(judge, answer, "dishwasher_total", 384)
    check_answer_number(judge, answer, "adv_result_count", 36)
    # "the cheapest one": cheapest result is the DUH30253UC hood ($699,
    # "Dishwasher Safe Filters" keyword match); "that dishwasher" reading
    # gives SHE41CM2N/CM5N/CM6N at $729. Accept any defensible pair.
    ok_pair = False
    for name, price in (("DUH30253UC", 699), ("SHE41CM2N", 729),
                        ("SHE41CM5N", 729), ("SHE41CM6N", 729)):
        if name.lower() in answer.lower():
            check_answer_money(judge, answer, "cheapest_price", price)
            ok_pair = True
            break
    if not ok_pair:
        judge.fail("cheapest_name", "answer names none of DUH30253UC/SHE41CM2N/SHE41CM5N/SHE41CM6N")
    else:
        judge.ok("cheapest_name", "defensible cheapest named")
    check_answer_any(judge, answer, "model_code",
                     ["SHE41CM2N", "SHE41CM5N", "SHE41CM6N", "DUH30253UC"])
    check_answer_count_at_least(judge, answer, "feature",
                                ["PrecisionWash", "48 dBA", "dBA", "racks",
                                 "Dishwasher Safe Filters", "Knob Control"], 1)
    check_answer_phrase(judge, answer, "finance_offer", "15 Months Special Finance Offer")
    # audit-rail deepening: the opened product's Free Shipping panel text.
    check_answer_phrase(judge, answer, "product_freeshipp",
                        "Order This Item Today And Get Free Standard Shipping")
    # audit-rail deepening: the cheapest ACTUAL dishwasher among the filtered
    # results (SHE41CM2N / SHE41CM5N / SHE41CM6N, all $729) and the most
    # expensive result after the price-descending sort (SHP78CM2N /
    # SHP78CM6N / SPX68C75UC, all $1,499).
    ok_actual = False
    for name, price in (("SHE41CM2N", 729), ("SHE41CM5N", 729),
                        ("SHE41CM6N", 729)):
        if name.lower() in answer.lower():
            check_answer_money(judge, answer, "cheapest_actual_dishwasher_price", price)
            ok_actual = True
            break
    if not ok_actual:
        judge.fail("cheapest_actual_dishwasher_name",
                   "answer names none of SHE41CM2N/SHE41CM5N/SHE41CM6N")
    else:
        judge.ok("cheapest_actual_dishwasher_name",
                 "cheapest actual dishwasher named")
    ok_most = False
    for name in ("SHP78CM2N", "SHP78CM6N", "SPX68C75UC"):
        if name.lower() in answer.lower():
            check_answer_money(judge, answer, "most_expensive_price", 1499)
            ok_most = True
            break
    if not ok_most:
        judge.fail("most_expensive_name",
                   "answer names none of SHP78CM2N/SHP78CM6N/SPX68C75UC")
    else:
        judge.ok("most_expensive_name", "most expensive filtered result named")
    # navigation: the price-descending sort was applied too.
    check_visited_any(judge, traj, "nav_sort_pricedesc",
                      [r"sort=pricedesc", r"Price%3A\+Descending"])
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
