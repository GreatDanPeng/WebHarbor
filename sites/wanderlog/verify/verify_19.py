#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--19 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_19.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--19"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_guides_london", r"/guides\?[^ ]*[Ll]ondon")
    check_visited_path(judge, traj, "nav_guide1", r"/view/dxpkirpjls")
    check_visited_path(judge, traj, "nav_tate", r"/place/details/28109")
    check_visited_path(judge, traj, "nav_attractions", r"/list/geoCategory/104642")
    check_visited_path(judge, traj, "nav_author1", r"/u/taraabraham")
    check_visited_path(judge, traj, "nav_guide2", r"/view/wnglqezund")
    check_visited_path(judge, traj, "nav_author2", r"/u/LizzyS")
    check_answer_number(judge, answer, "n_matches", 2)
    check_answer_phrase(judge, answer, "most_title", 'Slices of London')
    check_answer_number(judge, answer, "most_views", 42922)
    check_answer_number(judge, answer, "most_likes", 424)
    check_answer_phrase(judge, answer, "author1", 'taraabraham')
    check_answer_phrase(judge, answer, "edited1", '2022-04-02')
    check_answer_phrase(judge, answer, "tate_desc", 'Modern-art gallery with international works on display, plus a cafe with panoramic river views')
    check_answer_number(judge, answer, "tate_rank", 10)
    check_answer_phrase(judge, answer, "tate_src", 'Lonely Planet')
    check_answer_number(judge, answer, "tate_src_pos", 2)
    check_answer_number(judge, answer, "author1_geos", 0)
    check_answer_number(judge, answer, "author1_countries", 0)
    check_answer_phrase(judge, answer, "other_title", 'London Guide')
    check_answer_phrase(judge, answer, "author2", 'LizzyS')
    check_answer_number(judge, answer, "views2", 33965)
    check_answer_phrase(judge, answer, "edited2", '2024-09-14')
    check_answer_phrase(judge, answer, "first_section", 'Neighborhoods')
    check_answer_number(judge, answer, "author2_geos", 265)
    check_answer_number(judge, answer, "author2_followers", 3)
    check_answer_number(judge, answer, "author2_following", 980)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
