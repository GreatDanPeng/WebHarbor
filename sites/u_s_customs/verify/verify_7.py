#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--7 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
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

TASK_ID = "CBP.gov--7"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_releases", r"/newsroom/media-releases/all")
    check_visited_path(judge, traj, "nav_khat_search", r"/newsroom/media-releases/all\?.*q=[^#]*khat")
    check_visited_path(judge, traj, "nav_dulles_release",
                       r"/newsroom/(national|local)-media-release/new-york-man-arrested-after-cbp-officers-seize-65-pounds-khat")
    check_visited_path(judge, traj, "nav_atlanta_release",
                       r"/newsroom/(national|local)-media-release/atlanta-cbp-officers-stop-more-4000-pounds-illegal-khat-entering-us")
    check_answer_phrase(judge, answer, "name", "Bakari Wally")
    check_answer_number(judge, answer, "age", 24)
    check_answer_phrase(judge, answer, "hometown", "Bronx")
    check_answer_number(judge, answer, "weight", 65)
    check_answer_phrase(judge, answer, "airport", "Washington Dulles International Airport")
    check_answer_phrase(judge, answer, "agency", "Metropolitan Washington Airports Authority Police")
    check_answer_phrase(judge, answer, "atlanta_pounds", "4,000")
    check_answer_phrase(judge, answer, "atlanta_airport", "Hartsfield-Jackson Atlanta International Airport")
    check_answer_count_at_least(judge, answer, "categories_local",
                                ["Local Media Release"], 1)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
