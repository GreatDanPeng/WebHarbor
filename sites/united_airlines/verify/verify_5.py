#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--5 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_5.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--5"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: FCO-DEN Oct 19 search comparing all five cabins of UA178.
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=FCO.*?destination=DEN.*?depart=2026-10-19')
    # answer ground truth: UA178 fares BE $538.16 / ECO $689.95 / EPU $855.54
    # / PP $1,621.38 / BUS $2,828.80; cheapest Premium Plus = UA178 on 787-9.
    check_answer_money(judge, answer, "be_fare", 538.16)
    check_answer_money(judge, answer, "eco_fare", 689.95)
    check_answer_money(judge, answer, "epu_fare", 855.54)
    check_answer_money(judge, answer, "pp_fare", 1621.38)
    check_answer_money(judge, answer, "bus_fare", 2828.80)
    check_answer_phrase(judge, answer, "cheapest_pp_flight", "178")
    check_answer_phrase(judge, answer, "aircraft", "787-9")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
