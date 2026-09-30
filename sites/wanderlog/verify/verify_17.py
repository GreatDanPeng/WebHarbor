#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--17 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_17.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--17"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_search", r"/search\?[^ ]*q=Dana\+Kim")
    check_visited_path(judge, traj, "nav_profile", r"/u/dana\.k")
    check_visited_path(judge, traj, "nav_trip_view", r"/trip/romeessentv")
    check_visited_path(judge, traj, "nav_stop1", r"/place/details/1583")
    check_visited_path(judge, traj, "nav_attractions", r"/list/geoCategory/104645")
    check_visited_path(judge, traj, "nav_stop3", r"/place/details/1589")
    check_visited_path(judge, traj, "nav_member", r"/u/alice\.j")
    check_visited_path(judge, traj, "nav_member_trip", r"/trip/tokyowkendv")
    check_visited_path(judge, traj, "nav_meiji", r"/place/details/965")
    check_answer_phrase(judge, answer, "username", 'dana.k')
    check_answer_number(judge, answer, "geos", 9)
    check_answer_number(judge, answer, "countries", 4)
    check_answer_phrase(judge, answer, "dates_start", '2026-10-16')
    check_answer_phrase(judge, answer, "dates_end", '2026-10-18')
    check_answer_ordered(judge, answer, "d2_times", ['08:30', '11:30', '13:30'])
    check_answer_count_at_least(judge, answer, "d2_stops", ['Saint Peter’s Basilica', 'Sistine Chapel', 'Bonci Pizzarium'], 3)
    check_answer_phrase(judge, answer, "d2_note", 'Best pizza al taglio near the Vatican')
    check_answer_phrase(judge, answer, "member_dana", 'Dana Kim')
    check_answer_phrase(judge, answer, "member_alice", 'Alice Johnson')
    check_answer_money(judge, answer, "budget_total", 1556.0)
    check_answer_phrase(judge, answer, "stop1_desc", "Iconic temple built circa 118 to 125 A.D. with a dome & Renaissance tombs, including Raphael's")
    check_answer_phrase(judge, answer, "stop1_cat1", 'Historical landmark')
    check_answer_phrase(judge, answer, "stop1_cat2", 'Sights & Landmarks')
    check_answer_number(judge, answer, "stop1_rank", 1)
    check_answer_phrase(judge, answer, "stop1_src", 'Condé Nast Traveler')
    check_answer_number(judge, answer, "stop1_src_pos", 12)
    check_answer_phrase(judge, answer, "stop3_desc", 'Aqueduct-fed rococo fountain, designed by Nicola Salvi & completed in 1762, with sculpted figures')
    check_answer_number(judge, answer, "stop3_rank", 3)
    check_answer_phrase(judge, answer, "stop3_src", 'Time Out')
    check_answer_number(judge, answer, "stop3_src_pos", 7)
    check_answer_number(judge, answer, "member_geos", 42)
    check_answer_phrase(judge, answer, "member_trip", 'Tokyo Weekend')
    check_answer_phrase(judge, answer, "meiji_desc", 'Surrounded by forest, this venerable Shinto shrine features a seasonal iris garden')
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
