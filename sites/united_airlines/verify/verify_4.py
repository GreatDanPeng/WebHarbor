#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--4 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_4.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--4"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: status by number UA2855, route status SFO-ORD, 787-8 fleet page.
    check_visited_path(judge, traj, "nav_status_number", r'/flight-status/results\?.*?number=2855')
    check_visited_path(judge, traj, "nav_status_route", r'/flight-status/results\?.*?mode=route.*?origin=SFO.*?destination=ORD')
    check_visited_path(judge, traj, "nav_fleet_78h", r'/travel-info/fleet/78H')
    # answer ground truth: UA2855 SFO 15:30 -> ORD 21:53, Boeing 787-8,
    # Wi-Fi Panasonic, 7 United First/Business rows, 3 Premium Plus rows.
    check_answer_any(judge, answer, "scheduled_departure", ["15:30"])
    check_answer_any(judge, answer, "scheduled_arrival", ["21:53"])
    check_answer_phrase(judge, answer, "aircraft_type", "787-8")
    check_answer_phrase(judge, answer, "wifi_provider", "Panasonic")
    check_answer_number(judge, answer, "polaris_rows", 7)
    check_answer_number(judge, answer, "premium_plus_rows", 3)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
