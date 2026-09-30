#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--13 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_13.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USAppliance--13"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: buying guides, refrigerator guide, French Door category,
    # WRF560SEHZ product page.
    check_visited_path(judge, traj, "nav_guides", r"/buyingguide\.html")
    check_visited_path(judge, traj, "nav_fridge_guide", r"/guides/refrigerator\.html")
    check_visited_path(judge, traj, "nav_frdore", r"/frdore\.html")
    check_visited_path(judge, traj, "nav_wrf560_product", r"/wrf560sehz")
    # audit-rail deepening: the Wall Oven Buying Guide (upstream slug
    # wallovon, preserved verbatim).
    check_visited_path(judge, traj, "nav_walloven_guide", r"/guides/wallovon\.html")
    # answer ground truth
    check_answer_number(judge, answer, "guide_count", 9)
    check_answer_any(judge, answer, "advice_hours", ["8am-6pm", "8am - 6pm"])
    check_answer_phrase(judge, answer, "toll_free", "877-628-9913")
    check_answer_phrase(judge, answer, "first_section_heading", "Types of Refrigerators")
    check_answer_phrase(judge, answer, "third_section_heading", "Key Features to Consider")
    check_answer_count_at_least(judge, answer, "fridge_types",
                                ["Top Freezer", "French Door", "Bottom Freezer",
                                 "Side by Side", "Built-In"], 2)
    check_answer_number(judge, answer, "french_door_count", 318)
    check_answer_money(judge, answer, "wrf560_price", 1898)
    check_answer_count_at_least(judge, answer, "wrf560_feature",
                                ["fingerprint", "20 cu", "French door", "humidity"], 1)
    # audit-rail deepening: the WRF560SEHZ ZIP 48083 availability answer and
    # the Wall Oven guide's first numbered section heading.
    check_answer_phrase(judge, answer, "wrf560_zip_48083",
                        "QUICKSHIP - Ships in 1-2 business days")
    check_answer_phrase(judge, answer, "walloven_first_heading", "Wall Oven Types")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
