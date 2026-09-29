#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--7 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_7.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_phrase, check_read_only, check_rows_added,
    check_rows_changed, check_only_tables_changed, check_screenshots,
    check_seed_contract, check_trajectory_identity, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "United Airlines--7"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: dave signs in, check-in flow, boarding pass.
    check_visited_path(judge, traj, "nav_signin", r'/signin')
    check_visited_path(judge, traj, "nav_checkin", r'/checkin')
    check_visited_path(judge, traj, "nav_checkin_flow", r'/checkin/HD19RK')
    check_visited_path(judge, traj, "nav_boarding_pass", r'/checkin/HD19RK/boarding-pass')
    # answer ground truth: seat 12A, boarding group Group 1 (Premier Platinum),
    # gate C12, boarding 14:50 (40 min before the 15:30 departure), Boeing 787-8.
    check_answer_phrase(judge, answer, "seat", "12A")
    check_answer_phrase(judge, answer, "boarding_group", "Group 1")
    check_answer_any(judge, answer, "gate", ["C12"])
    check_answer_any(judge, answer, "boarding_time", ["14:50"])
    check_answer_phrase(judge, answer, "aircraft", "787-8")
    check_only_tables_changed(judge, initial, after, {"passengers"})
    check_rows_changed(judge, initial, after, "passengers",
                       [[4, 4, "Dave", "Thomas", None, None, None,
                         "5153868213", "12A", 1, "Group 1"]],
                       "checked_in_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
