#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--11 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_11.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_number_absent,
    check_answer_ordered, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Wanderlog--11"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_plan", r"/plan/parisinspring")
    check_visited_path(judge, traj, "nav_map", r"/plan/parisinspring/map")
    check_visited_path(judge, traj, "nav_budget", r"/plan/parisinspring/budget")
    check_visited_path(judge, traj, "nav_pin1", r"/place/details/1522")
    check_visited_path(judge, traj, "nav_clamato", r"/place/details/24178")
    check_visited_path(judge, traj, "nav_restaurants", r"/list/geoCategory/74215")
    check_visited_path(judge, traj, "nav_shared", r"/trip/parisinspringv")
    check_visited_path(judge, traj, "nav_collab", r"/u/bob\.c")
    check_answer_number(judge, answer, "pin_count", 10)
    check_answer_phrase(judge, answer, "leg1_km", '1.4 km')
    check_answer_phrase(judge, answer, "leg1_mi", '0.9 mi')
    check_answer_regex(judge, answer, "pin1_coords", r"48\.8600[, ]*2\.3266")
    check_answer_phrase(judge, answer, "pin4_place", 'Louvre Museum')
    check_answer_phrase(judge, answer, "pin4_day", 'Day 2')
    check_answer_phrase(judge, answer, "last_pin", 'Clamato')
    check_answer_money(judge, answer, "lodging_total", 1560.0)
    check_answer_money(judge, answer, "food_total", 142.0)
    check_answer_phrase(judge, answer, "orsay_admission", '🎟')
    check_answer_phrase(judge, answer, "orsay_tip", 'Consider using a self-guided audio tour to enhance your visit and learn more about the artworks')
    check_answer_phrase(judge, answer, "clamato_cat1", 'Seafood restaurant')
    check_answer_phrase(judge, answer, "clamato_cat2", 'Bar')
    check_answer_number(judge, answer, "clamato_rank", 4)
    check_answer_phrase(judge, answer, "clamato_src", 'The Infatuation')
    check_answer_number(judge, answer, "clamato_src_pos", 12)
    check_answer_number(judge, answer, "bob_geos", 17)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
