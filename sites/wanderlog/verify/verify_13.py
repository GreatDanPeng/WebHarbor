#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--13 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_13.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--13"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_search_lilies", r"/search\?[^ ]*q=lilies")
    check_visited_path(judge, traj, "nav_profile", r"/u/alilies")
    check_visited_path(judge, traj, "nav_guide", r"/view/uzyvvtuwtc")
    check_visited_path(judge, traj, "nav_commenter1", r"/u/alice\.j")
    check_visited_path(judge, traj, "nav_commenter2", r"/u/carol\.d")
    check_visited_path(judge, traj, "nav_search_rachel", r"/search\?[^ ]*q=rachel")
    check_visited_path(judge, traj, "nav_rachel1", r"/u/rachelirl_")
    check_visited_path(judge, traj, "nav_rachel2", r"/u/peachy2391")
    check_visited_path(judge, traj, "nav_iceland_guide", r"/view/nwhizniizm")
    check_visited_path(judge, traj, "nav_dana", r"/u/dana\.k")
    check_answer_phrase(judge, answer, "display_name", 'elisa')
    check_answer_phrase(judge, answer, "username", 'alilies')
    check_answer_number(judge, answer, "geos", 214)
    check_answer_number(judge, answer, "countries", 38)
    check_answer_number(judge, answer, "followers", 70)
    check_answer_number(judge, answer, "following", 714)
    check_answer_any(judge, answer, "pro_badge", ['Pro', 'pro'])
    check_answer_number(judge, answer, "guides_listed", 1)
    check_answer_number(judge, answer, "views", 177509)
    check_answer_number(judge, answer, "likes", 771)
    check_answer_phrase(judge, answer, "edited", '2026-05-12')
    check_answer_phrase(judge, answer, "first_section", 'Notre Dame and Eiffel Tower')
    check_answer_phrase(judge, answer, "comment1", 'Alice Johnson')
    check_answer_phrase(judge, answer, "comment1_date", '2026-09-18')
    check_answer_phrase(judge, answer, "comment2", 'Carol Davis')
    check_answer_phrase(judge, answer, "comment2_date", '2026-09-21')
    check_answer_number(judge, answer, "commenter1_geos", 42)
    check_answer_number(judge, answer, "commenter2_geos", 23)
    check_answer_number(judge, answer, "rachel_matches", 2)
    check_answer_phrase(judge, answer, "rachel1", 'Rachel IRL')
    check_answer_phrase(judge, answer, "rachel2", 'Rachel Lang')
    check_answer_number(judge, answer, "rachel1_geos", 140)
    check_answer_number(judge, answer, "rachel2_geos", 46)
    check_answer_number(judge, answer, "iceland_views", 1605)
    check_answer_number(judge, answer, "dana_geos", 9)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
