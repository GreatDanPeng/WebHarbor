#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--18 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_18.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--18"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: range search (content tab), range guide, product tab.
    check_visited_path(judge, traj, "nav_search", r"/search\.php\?[^ ]*search_query=range")
    check_visited_any(judge, traj, "nav_content_tab",
                      [r"section=content", r"News & Information"])
    check_visited_path(judge, traj, "nav_range_guide", r"/guides/range\.html")
    check_visited_any(judge, traj, "nav_product_tab",
                      [r"/search\.php\?[^ ]*search_query=range[^ ]*(&section=product)?(&sort=priceasc)?"])
    # audit-rail deepening: the price-descending sort and the Refrigerator
    # Buying Guide.
    check_visited_any(judge, traj, "nav_sort_pricedesc",
                      [r"sort=pricedesc", r"Price%3A\+Descending"])
    check_visited_path(judge, traj, "nav_fridge_guide", r"/guides/refrigerator\.html")
    # answer ground truth
    check_answer_number(judge, answer, "content_result_count", 4)
    check_answer_phrase(judge, answer, "range_guide_title", "Range Buying Guide")
    check_answer_phrase(judge, answer, "guide_first_heading", "Fuel Types")
    check_answer_count_at_least(judge, answer, "range_types",
                                ["Electric", "Gas", "Dual-Fuel", "Induction",
                                 "Double Ovens"], 1)
    # r2 deepening: fuel types listed in the guide's first section, one gas
    # pro or con, and the cheapest-result kind/fuel analysis.
    check_answer_count_at_least(judge, answer, "guide_fuel_types",
                                ["Electric", "Gas", "Dual-Fuel", "Induction"], 3)
    check_answer_any(judge, answer, "gas_pro_or_con",
                     ["Instant heat", "immediate temperature control",
                      "Visible flame", "Works during power outages",
                      "Requires a gas line", "less even",
                      "Harder to clean", "monitor heat"])
    check_answer_number(judge, answer, "product_result_count", 1428)
    check_answer_phrase(judge, answer, "cheapest_name", "Gas Range Installation Kit")
    check_answer_phrase(judge, answer, "cheapest_price", "29.95")
    check_answer_any(judge, answer, "cheapest_kind",
                    ["installation accessory", "an accessory", "not an actual range",
                     "accessory rather than a range"])
    check_answer_phrase(judge, answer, "cheapest_serves_fuel", "Gas")
    # audit-rail deepening: the most expensive result after the descending
    # sort and the Refrigerator guide's first heading.
    check_answer_phrase(judge, answer, "most_expensive_name", "VDR56046GQSSBB")
    check_answer_money(judge, answer, "most_expensive_price", 27389)
    # the audit-rail wording asks the agent to OPEN the most expensive result.
    check_visited_path(judge, traj, "nav_most_expensive_product",
                       r"vdr56046gqssbb")
    check_answer_phrase(judge, answer, "fridge_guide_first_heading",
                        "Types of Refrigerators")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
