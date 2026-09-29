#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--9 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_9.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--9"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_trip", r"/plan/nycfoodcrawl")
    check_visited_path(judge, traj, "nav_settings", r"/plan/nycfoodcrawl/settings")
    check_visited_path(judge, traj, "nav_share_link", r"/trip/nycfoodcrawlv")
    check_visited_path(judge, traj, "nav_rubirosa", r"/place/details/115803")
    check_visited_path(judge, traj, "nav_restaurants", r"/list/geoCategory/74988")
    check_answer_any(judge, answer, "privacy_before", ['Private', 'private'])
    check_answer_phrase(judge, answer, "share_link", 'nycfoodcrawlv')
    check_answer_number(judge, answer, "spans", 3)
    check_answer_any(judge, answer, "privacy_after", ['Link', 'link'])
    check_answer_phrase(judge, answer, "new_section", 'Day 4 · Dec 7')
    check_answer_phrase(judge, answer, "shared_title", 'New York City Food Crawl')
    check_answer_phrase(judge, answer, "d2_first", 'Grand Central Oyster Bar')
    check_answer_phrase(judge, answer, "d2_first_time", '12:00')
    check_answer_phrase(judge, answer, "d2_second", 'Eleven Madison Park')
    check_answer_phrase(judge, answer, "d2_second_time", '17:30')
    check_answer_phrase(judge, answer, "d3_note", 'Tie-dye pizza.')
    check_answer_phrase(judge, answer, "rubirosa_cat1", 'Pizza restaurant')
    check_answer_phrase(judge, answer, "rubirosa_cat2", 'Gluten-free restaurant')
    check_answer_number(judge, answer, "rubirosa_rank", 9)
    check_answer_phrase(judge, answer, "rubirosa_src", 'Travel + Leisure')
    check_answer_number(judge, answer, "rubirosa_src_pos", 3)
    check_only_tables_changed(judge, initial, after, {'trips', 'trip_sections'})
    check_rows_changed(judge, initial, after, "trips",
                       [(4, None, None, None, None, None, None, "2026-12-07", None, None,
                  "link", None, "2026-09-29")] , "db_privacy_link")
    check_rows_added(judge, initial, after, "trip_sections",
                      [(None, 4, "Day 4 · Dec 7", 4, 4)], "db_section_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
