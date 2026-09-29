#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--1 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_1.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--1"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_explore_tokyo", r"/explore/1")
    check_visited_path(judge, traj, "nav_attractions", r"/list/geoCategory/104388")
    check_visited_path(judge, traj, "nav_rank6", r"/place/details/956")
    check_visited_path(judge, traj, "nav_rank7", r"/place/details/36514")
    check_visited_path(judge, traj, "nav_cafes", r"/list/geoCategory/14")
    check_visited_path(judge, traj, "nav_cafe1", r"/place/details/27207")
    check_visited_path(judge, traj, "nav_cafe2", r"/place/details/376399")
    check_visited_path(judge, traj, "nav_restaurants", r"/list/geoCategory/1")
    check_visited_path(judge, traj, "nav_rest7", r"/place/details/379633")
    check_answer_phrase(judge, answer, "list_title", 'Top 49 things to do and attractions in Tokyo')
    check_answer_number(judge, answer, "upstream_count", 49)
    check_answer_ordered(judge, answer, "ranks_6_7", ['Shinjuku Gyoen National Garden', 'Ueno Park'])
    check_answer_phrase(judge, answer, "src1_site", 'Condé Nast Traveler')
    check_answer_number(judge, answer, "src1_pos", 4)
    check_answer_phrase(judge, answer, "src2_site", 'Times of India')
    check_answer_number(judge, answer, "src2_pos", 5)
    check_answer_regex(judge, answer, "src1_assoc", r"(?i)condé nast traveler\)?[^\n#]{0,14}#\s*4|#4[^\n]{0,6}on[^\n]{0,4}condé nast traveler")
    check_answer_regex(judge, answer, "src2_assoc", r"(?i)times of india\)?[^\n#]{0,14}#\s*5|#5[^\n]{0,6}on[^\n]{0,4}times of india")
    check_answer_phrase(judge, answer, "gyoen_tip", 'Visit during cherry blossom season in spring or autumn for vibrant foliage colors')
    check_answer_phrase(judge, answer, "gyoen_cat1", 'Garden')
    check_answer_phrase(judge, answer, "gyoen_cat2", 'Nature & Parks')
    check_answer_regex(judge, answer, "gyoen_coords", r"35\.6852[, ]*139\.7101")
    check_answer_phrase(judge, answer, "ueno_desc", 'Popular city park featuring ample walking paths, a lake with boat rentals, a zoo & several museums')
    check_answer_phrase(judge, answer, "cafes_title", 'The 50 best coffee shops and best cafes in Tokyo')
    check_answer_number(judge, answer, "cafes_count", 50)
    check_answer_ordered(judge, answer, "cafes_top2", ['Onibus Coffee', 'Fuglen Tokyo'])
    check_answer_regex(judge, answer, "onibus_coords", r"35\.6432[, ]*139\.6980")
    check_answer_phrase(judge, answer, "fuglen_desc", 'Cocktails, coffee & Scandinavian baked goods in a trendy, wood-paneled space with vintage decor')
    check_answer_phrase(judge, answer, "fuglen_cat1", 'Coffee shop')
    check_answer_phrase(judge, answer, "fuglen_cat2", 'Cafe')
    check_answer_phrase(judge, answer, "rest7", 'Butagumi')
    check_answer_phrase(judge, answer, "butagumi_cat1", 'Tonkatsu restaurant')
    check_answer_phrase(judge, answer, "butagumi_cat2", 'Restaurant')
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
