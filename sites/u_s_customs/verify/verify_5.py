#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--5 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_5.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--5"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_i94_request", r"/i94/request")
    check_answer_phrase(judge, answer, "alice_number", "269745632011")
    check_answer_phrase(judge, answer, "alice_class", "VWP B-1")
    check_answer_phrase(judge, answer, "alice_entry", "2026-06-14")
    check_answer_phrase(judge, answer, "alice_until", "2026-09-12")
    check_answer_phrase(judge, answer, "alice_poe", "Washington Dulles International Airport")
    check_answer_phrase(judge, answer, "bob_number", "269745641088")
    check_answer_phrase(judge, answer, "bob_class", "US Citizen")
    check_answer_phrase(judge, answer, "bob_entry", "2026-09-03")
    check_answer_phrase(judge, answer, "bob_poe", "San Ysidro")
    check_answer_phrase(judge, answer, "wrong_dob_message", "No I-94 record found")
    check_answer_phrase(judge, answer, "carol_class", "VWP B-2")
    check_answer_phrase(judge, answer, "carol_until", "2026-06-20")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
