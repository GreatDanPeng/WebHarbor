#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--18 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_18.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--18"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: EWR-DEN route status, the earliest-arrival fleet page, DEN guide.
    check_visited_path(judge, traj, "nav_status", r'/flight-status/results\?.*?mode=route.*?origin=EWR.*?destination=DEN')
    check_visited_path(judge, traj, "nav_fleet", r'/travel-info/fleet/21N')
    check_visited_path(judge, traj, "nav_airport", r'/travel-info/airports/DEN')
    # answer ground truth: UA1197 16:59->19:34, UA407 18:49->21:18,
    # UA1792 20:59->23:26; earliest arrival UA1197 at 19:34. The duration the
    # status page actually lists for UA 1197 is 3h 01m (the frozen
    # great-circle block time; the naive schedule difference 19:34-16:59 =
    # 2h 35m is also accepted as an honest arithmetic reading),
    # Wi-Fi provider Viasat (A321neo); Denver is a United hub.
    check_answer_count_at_least(judge, answer, "all_three_flights",
                                ["1197", "407", "1792"], 3)
    check_answer_any(judge, answer, "ua1197_times", ["16:59"])
    check_answer_any(judge, answer, "ua1197_arrival", ["19:34"])
    check_answer_any(judge, answer, "ua407_times", ["18:49"])
    check_answer_any(judge, answer, "ua1792_times", ["20:59"])
    ok_aircraft = ("A321neo" in answer) or ("321neo" in answer)
    if ok_aircraft:
        judge.ok("aircraft_of_earliest", "Airbus A321neo")
    else:
        judge.fail("aircraft_of_earliest", "answer lacks the aircraft")
    check_answer_phrase(judge, answer, "earliest_arrival", "1197")
    check_answer_any(judge, answer, "duration", ["3h 01m", "3 hours 1", "2h 35m", "2 hours 35"])
    check_answer_phrase(judge, answer, "wifi_provider", "Viasat")
    ok_hub = ("hub" in answer.lower())
    if ok_hub:
        judge.ok("denver_hub", "Denver is a United hub")
    else:
        judge.fail("denver_hub", "answer must state Denver is a United hub")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
