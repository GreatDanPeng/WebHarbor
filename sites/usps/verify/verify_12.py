#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--12 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_12.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_answer_regex, check_attributed_money, check_only_tables_changed,
    check_read_only, check_rows_added, check_screenshots,
    check_seed_contract, check_section_phrase, check_trajectory_identity,
    check_visited_any, check_visited_path, final_answer, run_verifier,
)

TASK_ID = "USPS.com--12"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_store", r"/store")
    # r2 truth-move #9 (fix F-9): the task path now browses the All Stamps
    # union page directly (BCR is reachable there), so the fixture walk
    # includes /store/stamps-all.
    check_visited_path(judge, traj, "nav_stamps_all", r"/store/stamps-all")
    check_answer_phrase(judge, answer, "christmas_stamps",
                        "Christmas Cookies Stamps")
    check_answer_money(judge, answer, "christmas_price", 16.40)
    check_answer_money(judge, answer, "bcr_price", 20.00)
    check_answer_phrase(judge, answer, "most_expensive", "Sarah Orne Jewett")
    check_answer_money(judge, answer, "most_expensive_price", 28.00)
    check_answer_number(judge, answer, "cookies_sku", 686104)
    # r2 deepening (fix F-3): BCR SKU, most-expensive SKU, Diwali and
    # U.S. Flag prices, and the All Stamps product count.
    check_answer_number(judge, answer, "bcr_sku", 555304)
    check_answer_number(judge, answer, "most_expensive_sku", 130204)
    check_answer_money(judge, answer, "diwali_price", 16.40)
    check_answer_money(judge, answer, "usflag_price", 16.40)
    check_answer_number(judge, answer, "all_stamps_count", 19)
    # audit deepening (ordinal 57): Hanukkah price, New Releases count,
    # and the Collectibles & Gifts category.
    check_answer_money(judge, answer, "hanukkah_price", 16.40)
    check_answer_number(judge, answer, "new_releases_count", 18)
    check_visited_path(judge, traj, "nav_gifts", r"/store/gifts-collectors")
    check_answer_phrase(judge, answer, "dcp_name", "Complete DCP Set")
    check_answer_money(judge, answer, "dcp_price", 337.15)
    check_answer_number(judge, answer, "dcp_sku", 992621)
    check_answer_money(judge, answer, "barbie_price", 8.20)
    check_answer_number(judge, answer, "barbie_sku", 582504)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
