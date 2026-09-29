#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--14 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_14.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--14"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_leaderboard", r"/leaderboard")
    check_visited_path(judge, traj, "nav_search_lizzys", r"/search\?[^ ]*q=LizzyS")
    check_visited_path(judge, traj, "nav_profile", r"/u/LizzyS")
    check_visited_path(judge, traj, "nav_guide", r"/view/tbgojyfsfr")
    check_visited_path(judge, traj, "nav_empire", r"/place/details/2352")
    check_visited_path(judge, traj, "nav_attractions", r"/list/geoCategory/105416")
    check_visited_path(judge, traj, "nav_search_maru", r"/search\?[^ ]*q=maru")
    check_visited_path(judge, traj, "nav_maru", r"/u/Marutravelsjapan")
    check_visited_path(judge, traj, "nav_maru_guide1", r"/view/vayytsqzpq")
    check_visited_path(judge, traj, "nav_maru_guide2", r"/view/okgarduipy")
    check_answer_number(judge, answer, "top_geos", 3526)
    check_answer_phrase(judge, answer, "top_geos_name", 'Muhammad Baqi El Vatikan')
    check_answer_number(judge, answer, "second_geos", 1787)
    check_answer_phrase(judge, answer, "second_name", 'Los compas Niñis')
    check_answer_number(judge, answer, "top_countries", 219)
    check_answer_count_at_least(judge, answer, "both_boards", ['los44', 'elvatikan'], 2)
    check_answer_phrase(judge, answer, "third_name", 'Ron Schwarz')
    check_answer_number(judge, answer, "third_geos", 1680)
    check_answer_number(judge, answer, "lizzy_geos", 265)
    check_answer_number(judge, answer, "lizzy_countries", 53)
    check_answer_number(judge, answer, "lizzy_guides", 2)
    check_answer_number(judge, answer, "guide_views", 93144)
    check_answer_number(judge, answer, "guide_likes", 282)
    check_answer_phrase(judge, answer, "guide_edited", '2024-01-07')
    check_answer_phrase(judge, answer, "empire_desc", 'Iconic, art deco office tower from 1931 with exhibits & observatories on the 86th & 102nd floors')
    check_answer_number(judge, answer, "empire_rank", 4)
    check_answer_phrase(judge, answer, "empire_src", 'The Culture Trip')
    check_answer_number(judge, answer, "empire_src_pos", 1)
    check_answer_number(judge, answer, "maru_geos", 74)
    check_answer_number(judge, answer, "maru_guide1_views", 3215)
    check_answer_number(judge, answer, "maru_guide2_views", 1910)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
