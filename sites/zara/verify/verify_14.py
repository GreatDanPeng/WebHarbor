#!/usr/bin/env python3
"""Deterministic verifier for Zara--14 (zara).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-zara-review, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_14.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_number_absent,
    check_answer_ordered, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Zara--14"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)

    # navigation: logon, ADDRESSES (add / default / delete all through it)
    check_visited_path(judge, traj, "nav_logon", r"/us/en/logon")
    check_visited_path(judge, traj, "nav_addresses", r"/us/en/account/addresses")
    # answer ground truth
    check_answer_phrase(judge, answer, "saved_label", "HOME")
    check_answer_phrase(judge, answer, "saved_name", "Bob Chen")
    check_answer_phrase(judge, answer, "saved_line1", "1810 N Sedgwick St, Unit 3")
    check_answer_any(judge, answer, "saved_city", ["Chicago", "CHICAGO"])
    check_answer_phrase(judge, answer, "saved_zip", "60614")
    check_answer_any(judge, answer, "new_label", ["SUMMER", "Summer"])
    check_answer_count_at_least(judge, answer, "appears", ["900 Lake Shore Dr"], 1)
    check_answer_any(judge, answer, "default_now", ["SUMMER", "Summer"])
    check_answer_phrase(judge, answer, "remaining_label", "SUMMER")
    # after-state: bob's HOME row replaced by the SUMMER row (default)
    check_only_tables_changed(judge, initial, after, {"addresses"})
    check_rows_added(judge, initial, after, "addresses",
                     [[6, 2, "SUMMER", "Bob Chen", "900 Lake Shore Dr", None, "Chicago", "IL",
                       "60601", "312-555-0199", 1]], "summer_row_added")
    check_rows_removed(judge, initial, after, "addresses",
                       [[3, 2, "HOME", "Bob Chen", "1810 N Sedgwick St, Unit 3", None, "Chicago", "IL",
                         "60614", "773-555-0137", 1]], "home_row_deleted")



if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
