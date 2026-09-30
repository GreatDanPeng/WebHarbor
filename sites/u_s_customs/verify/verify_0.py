#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--0 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_0.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--0"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation gates: BWT tool with Mexican border + delay sort, top crossing
    # detail, the list again, and the same-port commercial crossing detail.
    check_visited_path(judge, traj, "nav_bwt_mexico_delay",
                       r"/bwt\?.*(border=mexico.*sort=delay|sort=delay.*border=mexico)")
    check_visited_path(judge, traj, "nav_otay_passenger", r"/bwt/crossing/250601")
    check_visited_path(judge, traj, "nav_back_to_list", r"/bwt(\?|$)")
    check_visited_path(judge, traj, "nav_otay_commercial", r"/bwt/crossing/250602")
    # answer ground truth
    check_answer_phrase(judge, answer, "top_crossing", "Otay Mesa")
    check_answer_phrase(judge, answer, "top_crossing_lane", "Passenger")
    check_answer_number(judge, answer, "top_std_delay", 185)
    check_answer_number(judge, answer, "std_lanes_open", 3)
    check_answer_phrase(judge, answer, "lane_update_time", "10:00 am")
    check_answer_number(judge, answer, "ready_delay", 120)
    check_answer_phrase(judge, answer, "port_hours", "24 hrs/day")
    check_answer_phrase(judge, answer, "second_crossing", "San Ysidro")
    check_answer_number(judge, answer, "second_std_delay", 150)
    check_answer_number(judge, answer, "commercial_std_delay", 40)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
