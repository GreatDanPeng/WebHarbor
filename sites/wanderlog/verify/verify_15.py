#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--15 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_15.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--15"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_guides", r"/guides")
    check_visited_path(judge, traj, "nav_guide", r"/view/zlcocpeivp")
    check_visited_path(judge, traj, "nav_author", r"/u/delicious_dogfish")
    check_visited_path(judge, traj, "nav_commenter", r"/u/dana\.k")
    check_answer_number(judge, answer, "views", 14675)
    check_answer_number(judge, answer, "likes_before", 226)
    check_answer_number(judge, answer, "likes_after", 227)
    check_answer_phrase(judge, answer, "author_display", 'Brandon Jackson')
    check_answer_phrase(judge, answer, "author_username", 'delicious_dogfish')
    check_answer_any(judge, answer, "distinction", ['Verified', 'verified'])
    check_answer_phrase(judge, answer, "comment_body", 'Adding the Pantheon stop from this list to my Rome trip.')
    check_answer_phrase(judge, answer, "comment_date", '2026-09-29')
    check_answer_number(judge, answer, "author_geos", 4)
    check_answer_number(judge, answer, "author_countries", 3)
    check_answer_number(judge, answer, "commenter_geos", 9)
    check_answer_phrase(judge, answer, "public_trip", 'Rome Essentials')
    check_only_tables_changed(judge, initial, after, {'comments', 'likes', 'guides'})
    check_rows_added(judge, initial, after, "likes",
                      [(None, 38438, 19)], "db_like_added")
    check_rows_changed(judge, initial, after, "guides",
                       [(38438, None, None, None, None, None, None, None, None, 227, None,
                    None, None, None)], "db_like_count")
    check_rows_added(judge, initial, after, "comments",
                      [(None, 38438, 19, "Adding the Pantheon stop from this list to my "
                        "Rome trip.", "2026-09-29")], "db_comment_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
