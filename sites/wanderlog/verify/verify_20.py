#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--20 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_20.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--20"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_explore", r"/explore/1")
    check_visited_path(judge, traj, "nav_attractions", r"/list/geoCategory/104388")
    check_visited_path(judge, traj, "nav_rank8", r"/place/details/31866")
    check_visited_path(judge, traj, "nav_cafes", r"/list/geoCategory/14")
    check_visited_path(judge, traj, "nav_cafe3", r"/place/details/119197")
    check_visited_path(judge, traj, "nav_hotels", r"/list/geoCategory/136770")
    check_visited_path(judge, traj, "nav_top_hotel", r"/place/details/79682")
    check_visited_path(judge, traj, "nav_restaurants", r"/list/geoCategory/1")
    check_answer_phrase(judge, answer, "dest_line", 'Japan · region · popularity 251,550')
    check_answer_count_at_least(judge, answer, "chips", ['Attractions', 'Cafes', 'Hotels', 'Restaurants'], 4)
    check_answer_phrase(judge, answer, "nearby1", 'Chiyoda')
    check_answer_phrase(judge, answer, "nearby2", 'Chuo')
    check_answer_phrase(judge, answer, "fifth_attr", 'Tokyo Tower')
    check_answer_phrase(judge, answer, "fifth_rest", 'The Pizza Bar On 38th')
    check_answer_phrase(judge, answer, "attr_title", 'Top 49 things to do and attractions in Tokyo')
    check_answer_phrase(judge, answer, "attr8", 'Ghibli Museum')
    check_answer_phrase(judge, answer, "attr9", 'Fish Market Tsukiji Outer Market')
    check_answer_phrase(judge, answer, "ghibli_desc", 'Whimsical museum dedicated to the famed animation studio with a play area, theater & rooftop garden')
    check_answer_phrase(judge, answer, "cafes_title", 'The 50 best coffee shops and best cafes in Tokyo')
    check_answer_phrase(judge, answer, "cafe3", 'THE ROASTERY BY NOZY COFFEE')
    check_answer_regex(judge, answer, "cafe3_coords", r"35\.6656[, ]*139\.7048")
    check_answer_phrase(judge, answer, "hotels_title", 'The 50 best hotels in Tokyo')
    check_answer_phrase(judge, answer, "top_hotel", 'Mandarin Oriental, Tokyo')
    check_answer_phrase(judge, answer, "top_hotel_desc", 'Luxe quarters with city views in a chic high-rise hotel offering 10 restaurants & an upscale spa')
    check_answer_phrase(judge, answer, "top_hotel_src", 'Travel + Leisure')
    check_answer_number(judge, answer, "top_hotel_src_pos", 12)
    check_answer_phrase(judge, answer, "rest_title", 'Where to eat: the 50 best restaurants in Tokyo')
    check_answer_phrase(judge, answer, "rest_top", 'Narisawa')
    check_answer_phrase(judge, answer, "rest_src", 'Eater')
    check_answer_number(judge, answer, "rest_src_pos", 21)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
