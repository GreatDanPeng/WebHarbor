#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--3 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_3.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--3"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_plans", r"/plans")
    check_visited_path(judge, traj, "nav_plan", r"/plan/parisinspring")
    check_visited_path(judge, traj, "nav_septime", r"/place/details/114863")
    check_visited_path(judge, traj, "nav_restaurants", r"/list/geoCategory/74215")
    check_visited_path(judge, traj, "nav_sacre", r"/place/details/1534")
    check_visited_path(judge, traj, "nav_budget", r"/plan/parisinspring/budget")
    check_visited_path(judge, traj, "nav_checklist", r"/plan/parisinspring/checklist")
    check_visited_path(judge, traj, "nav_settings", r"/plan/parisinspring/settings")
    check_visited_path(judge, traj, "nav_shared", r"/trip/parisinspringv")
    check_visited_path(judge, traj, "nav_collab", r"/u/bob\.c")
    check_answer_phrase(judge, answer, "d1_first", "Musée d'Orsay")
    check_answer_phrase(judge, answer, "d1_time", '10:00')
    check_answer_number(judge, answer, "d1_duration", 120)
    check_answer_phrase(judge, answer, "septime_note", 'Reserved — tasting menu.')
    check_answer_phrase(judge, answer, "collab", 'Bob Chen')
    check_answer_any(judge, answer, "collab_status", ['accepted', 'Accepted'])
    check_answer_phrase(judge, answer, "dates_start", '2027-04-10')
    check_answer_phrase(judge, answer, "dates_end", '2027-04-13')
    check_answer_number(judge, answer, "travelers", 2)
    check_answer_any(judge, answer, "privacy", ['Link', 'link'])
    check_answer_phrase(judge, answer, "septime_cat1", 'Fine dining restaurant')
    check_answer_phrase(judge, answer, "septime_cat2", 'Bistro')
    check_answer_phrase(judge, answer, "septime_list", 'Where to eat: the 50 best restaurants in Paris')
    check_answer_number(judge, answer, "septime_rank", 1)
    check_answer_phrase(judge, answer, "septime_src", 'The Infatuation')
    check_answer_number(judge, answer, "septime_src_pos", 7)
    check_answer_phrase(judge, answer, "sacre_cat1", 'Basilica')
    check_answer_phrase(judge, answer, "sacre_cat2", 'Sights & Landmarks')
    check_answer_money(judge, answer, "alice_paid", 1704.2)
    check_answer_money(judge, answer, "bob_paid", 232.5)
    check_answer_phrase(judge, answer, "settlement", 'Bob Chen owes Alice Johnson $735.85')
    check_answer_phrase(judge, answer, "packing_progress", '3 of 5 packed')
    check_answer_phrase(judge, answer, "share_link", 'parisinspringv')
    check_answer_number(judge, answer, "bob_geos", 17)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
