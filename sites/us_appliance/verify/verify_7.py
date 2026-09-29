#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--7 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_7.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--7"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: rebates page, Shop By Brand, the Viking and Asko brand
    # pages (audit-rail deepening).
    check_visited_path(judge, traj, "nav_rebates", r"/rebates\.html")
    check_visited_path(judge, traj, "nav_shopbybrand", r"/shopbybrand\.html")
    check_visited_path(judge, traj, "nav_asko_brand", r"/brand/asko")
    check_visited_path(judge, traj, "nav_viking_brand", r"/brand/viking")
    # answer ground truth
    check_answer_number(judge, answer, "rebate_brand_count", 21)
    check_answer_phrase(judge, answer, "expiry_date", "Expires Dec 31")
    check_answer_phrase(judge, answer, "asko_washer_dryer",
                        "Save $300 when you buy an Asko Washer and Dryer")
    check_answer_phrase(judge, answer, "asko_extended",
                        "Get an extended 5 Year Warranty on select Asko Dishwashers")
    check_answer_phrase(judge, answer, "kitchenaid_title",
                        "Save up to $3000 on KitchenAid Appliances")
    check_answer_any(judge, answer, "viking_title",
                     ["Buy One Get One or $1,000 Allowance on Viking Appliances",
                      "Save up to $700 towards installation of eligible Viking Appliances"])
    # r2 deepening: per-brand offer counts for Miele and Samsung.
    check_answer_number(judge, answer, "miele_offer_count", 5)
    check_answer_number(judge, answer, "samsung_offer_count", 5)
    check_answer_phrase(judge, answer, "rebate_flag", "Rebate Offers")
    # audit-rail deepening: GE / Electrolux / Frigidaire offer counts, one
    # Miele offer title, and the Viking / Asko brand-page product counts.
    check_answer_number(judge, answer, "ge_offer_count", 4)
    check_answer_number(judge, answer, "electrolux_offer_count", 5)
    check_answer_number(judge, answer, "frigidaire_offer_count", 4)
    check_answer_number(judge, answer, "monogram_offer_count", 2)
    check_answer_any(judge, answer, "miele_offer_title",
                     ["Save $200 off Installation on qualifying Miele Dishwashers",
                      "Save $100 on Miele Dishwashers",
                      "Save $200 on Miele Washing Machines",
                      "Get a 5 Year Warranty on Miele Little Giant Laundry",
                      "Save 5%, 7% or 10% on Miele Appliances"])
    check_answer_number(judge, answer, "asko_brand_count", 47)
    check_answer_number(judge, answer, "viking_brand_count", 347)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
