#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--1 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
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

TASK_ID = "CBP.gov--1"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_bwt_blaine", r"/bwt\?.*q=[^#]*blaine")
    for pn, name in (("300401", "Pacific Highway"), ("300402", "Peace Arch"),
                     ("300403", "Point Roberts")):
        check_visited_path(judge, traj, f"nav_{name}", rf"/bwt/crossing/{pn}")
    check_answer_number(judge, answer, "blaine_count", 3)
    for name in ("Pacific Highway", "Peace Arch", "Point Roberts"):
        check_answer_phrase(judge, answer, f"crossing_{name}", name)
    check_answer_phrase(judge, answer, "hours_all", "24 hrs/day")
    check_answer_number(judge, answer, "std_delay_ph", 5)
    check_answer_number(judge, answer, "nexus_delay_ph", 5)
    check_answer_number(judge, answer, "nexus_lanes_ph", 1)
    check_answer_phrase(judge, answer, "point_roberts_status", "Update Pending")
    check_answer_count_at_least(judge, answer, "recommendation_mentions_crossing",
                                ["Pacific Highway", "Peace Arch", "Point Roberts"], 1)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
