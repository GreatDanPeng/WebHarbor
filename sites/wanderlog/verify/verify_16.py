#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--16 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Audit sync (orch/audit/wanderlog): the task adds a seventh-restaurant coordinates question
point, so the walk must also open /place/details/797293; the nav_rest7 gate and the rest7_coords
anchor below were asserted live on the audit container wh-wanderlog-audit (same frozen seed).
Usage: python3 verify_16.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--16"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_explore_rome", r"/explore/9616")
    check_visited_path(judge, traj, "nav_restaurants", r"/list/geoCategory/74217")
    check_visited_path(judge, traj, "nav_armando", r"/place/details/370765")
    check_visited_path(judge, traj, "nav_roscioli", r"/place/details/370316")
    check_visited_path(judge, traj, "nav_rest7", r"/place/details/797293")
    check_visited_path(judge, traj, "nav_attractions", r"/list/geoCategory/104645")
    check_visited_path(judge, traj, "nav_pantheon", r"/place/details/1583")
    check_visited_path(judge, traj, "nav_hotels", r"/list/geoCategory/137027")
    check_visited_path(judge, traj, "nav_top_hotel", r"/place/details/390732")
    check_answer_phrase(judge, answer, "list_title", 'Where to eat: the 50 best restaurants in Rome')
    check_answer_number(judge, answer, "upstream", 50)
    check_answer_phrase(judge, answer, "rank6", 'SantoPalato')
    check_answer_phrase(judge, answer, "rank7", 'Retrobottega')
    check_answer_phrase(judge, answer, "r4_source", 'Eater')
    check_answer_number(judge, answer, "r4_source_pos", 1)
    check_answer_phrase(judge, answer, "armando_desc", 'A long-standing restaurant serving hearty, traditional Roman fare in a wood-paneled dining room')
    check_answer_phrase(judge, answer, "cat1", 'Roman restaurant')
    check_answer_phrase(judge, answer, "cat2", 'Italian restaurant')
    check_answer_phrase(judge, answer, "roscioli_desc", 'Bustling destination with an eatery serving Italian fare, plus a bakery, deli counter & wine shop')
    check_answer_phrase(judge, answer, "roscioli_cat1", 'Italian restaurant')
    check_answer_phrase(judge, answer, "roscioli_cat2", 'Caterer')
    check_answer_regex(judge, answer, "rest7_coords", r"41\.8891[, ]*12\.4825")
    check_answer_phrase(judge, answer, "attr_title", 'Top 48 things to do and attractions in Rome')
    check_answer_number(judge, answer, "attr_count", 48)
    check_answer_phrase(judge, answer, "attr6", 'Piazza Navona')
    check_answer_phrase(judge, answer, "attr7", 'Saint Peter’s Basilica')
    check_answer_phrase(judge, answer, "pantheon_desc", "Iconic temple built circa 118 to 125 A.D. with a dome & Renaissance tombs, including Raphael's")
    check_answer_regex(judge, answer, "pantheon_coords", r"41\.8986[, ]*12\.4769")
    check_answer_phrase(judge, answer, "hotels_title", 'The 49 best hotels in Rome')
    check_answer_number(judge, answer, "hotels_count", 49)
    check_answer_phrase(judge, answer, "top_hotel", 'Hotel de Russie')
    check_answer_phrase(judge, answer, "top_hotel_desc", 'High-end hotel featuring an acclaimed restaurant with a garden, plus a bar & a spa')
    check_answer_phrase(judge, answer, "top_hotel_src", 'Condé Nast Traveler')
    check_answer_number(judge, answer, "top_hotel_src_pos", 18)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
