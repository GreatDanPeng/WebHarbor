#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--18 (uscis).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-uscis-review, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_18.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_office_range_map,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "USCIS.gov--18"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: login, address form, forms catalog AR-11 search.
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_address", r"/account/address")
    check_visited_path(judge, traj, "nav_forms", r"/forms[^ ]*AR-11")
    # answer ground truth
    check_answer_phrase(judge, answer, "addr_confirmed", "500 W Madison St")
    check_answer_phrase(judge, answer, "addr_city", "Chicago, IL 60661")
    check_answer_number(judge, answer, "days", 10)
    check_answer_count_at_least(judge, answer, "exempt_groups",
                                ["A and G visa holders",
                                 "visa waiver visitors"], 2)
    # DB: exactly bob.c's user row changed (address), nothing else.
    check_only_tables_changed(judge, initial, after, {"users"})
    check_rows_changed(judge, initial, after, "users",
                       [[2, "bob.c@test.com", None, None, None,
                         "500 W Madison St", "Chicago", "IL", "60661", None]],
                       "db_bob_address")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
