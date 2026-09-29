#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--2 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_2.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--2"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_bwt_sysidro", r"/bwt\?.*q=[^#]*ysidro")
    check_visited_path(judge, traj, "nav_sysidro_main", r"/bwt/crossing/250401")
    check_visited_path(judge, traj, "nav_ports_landing", r"/contact/ports")
    check_visited_path(judge, traj, "nav_ports_california", r"/about/contact/ports/CA")
    check_visited_path(judge, traj, "nav_sysidro_port", r"/(contact/ports|about/contact/ports/port)/san-ysidro-class-california-2504")
    check_visited_path(judge, traj, "nav_pedwest", r"/bwt/crossing/250407")
    check_answer_phrase(judge, answer, "crossing_cbx", "Cross Border Express")
    check_answer_phrase(judge, answer, "crossing_pedwest", "PedWest")
    check_answer_number(judge, answer, "main_std_delay", 150)
    check_answer_number(judge, answer, "main_std_lanes", 6)
    check_answer_number(judge, answer, "main_ready_delay", 120)
    check_answer_number(judge, answer, "main_ready_lanes", 11)
    check_answer_number(judge, answer, "main_nexus_delay", 30)
    check_answer_number(judge, answer, "main_nexus_lanes", 11)
    check_answer_number(judge, answer, "main_ped_delay", 60)
    check_answer_number(judge, answer, "main_ped_lanes", 16)
    check_answer_number(judge, answer, "port_code", 2504)
    check_answer_phrase(judge, answer, "port_phone", "+1 619-428-2188")
    check_answer_number(judge, answer, "pedwest_delay", 15)
    check_answer_number(judge, answer, "pedwest_lanes", 4)
    check_answer_phrase(judge, answer, "pedwest_hours", "6 am-2 pm")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
