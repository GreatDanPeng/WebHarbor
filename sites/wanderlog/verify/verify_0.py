#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--0 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_0.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--0"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_guides", r"/guides")
    check_visited_path(judge, traj, "nav_sort_places", r"/guides\?[^ ]*sort=places")
    check_visited_path(judge, traj, "nav_guide", r"/view/nlcviusycz")
    check_visited_path(judge, traj, "nav_profile", r"/u/pham2ez")
    check_visited_path(judge, traj, "nav_iceland_search", r"/guides\?[^ ]*q=Iceland")
    check_visited_path(judge, traj, "nav_iceland_guide", r"/view/znordifcrv")
    check_visited_path(judge, traj, "nav_iceland_author", r"/u/achillesvig")
    check_visited_path(judge, traj, "nav_sort_recent", r"/guides\?[^ ]*sort=recent")
    check_visited_path(judge, traj, "nav_recent_guide", r"/view/vayytsqzpq")
    check_answer_phrase(judge, answer, "guide_title", 'Japan: Video Game Guide')
    check_answer_phrase(judge, answer, "author_display", '2e')
    check_answer_phrase(judge, answer, "author_username", 'pham2ez')
    check_answer_number(judge, answer, "views", 228597)
    check_answer_number(judge, answer, "likes", 2862)
    check_answer_count_at_least(judge, answer, "animal_cafes", ['Asakusa Mameshiba Cafe', 'HARRY HARAJUKU terrace', 'mipig cafe Harajuku'], 3)
    check_answer_any(judge, answer, "distinction", ['Verified', 'verified'])
    check_answer_phrase(judge, answer, "comment_name", 'Bob Chen')
    check_answer_phrase(judge, answer, "comment_date", '2026-09-15')
    check_answer_number(judge, answer, "prof_geos", 92)
    check_answer_number(judge, answer, "prof_countries", 14)
    check_answer_number(judge, answer, "iceland_matches", 2)
    check_answer_phrase(judge, answer, "iceland_edited", '2026-09-17')
    check_answer_phrase(judge, answer, "iceland_author", 'achillesvig')
    check_answer_number(judge, answer, "iceland_author_geos", 184)
    check_answer_phrase(judge, answer, "recent_top", 'First timer | Tokyo: A 7-Day Itinerary')
    check_answer_phrase(judge, answer, "recent_author", 'Marutravelsjapan')
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
