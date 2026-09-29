#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--5 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_5.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--5"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_plan", r"/plan/parisinspring")
    check_visited_path(judge, traj, "nav_add_place", r"/plan/parisinspring/add")
    check_answer_phrase(judge, answer, "first_before", "Musée d'Orsay")
    check_answer_number(judge, answer, "stops_before", 3)
    check_answer_phrase(judge, answer, "confirmation", 'Place removed from the itinerary.')
    check_answer_phrase(judge, answer, "new_first", "Musée d'Orsay")
    check_answer_phrase(judge, answer, "new_first_time", '10:00')
    check_answer_number(judge, answer, "remaining", 2)
    check_answer_phrase(judge, answer, "now_second", 'Eiffel Tower')
    check_answer_ordered(judge, answer, "final_order", ["Musée d'Orsay", 'Eiffel Tower', 'Arc de Triomphe'])
    check_answer_any(judge, answer, "collab_badge", ['accepted', 'Accepted'])
    check_answer_absent(judge, answer, "removed_gone", "Sainte-Chapelle")
    check_only_tables_changed(judge, initial, after, {'trips', 'trip_entries'})
    check_rows_removed(judge, initial, after, "trip_entries",
                        [(2, 1, 165, "Stained glass is best with afternoon light.",
                         "14:30", 60, 2, 17)], "db_entry_removed")
    check_rows_changed(judge, initial, after, "trip_entries",
                       [(3, 1, 161, None, "17:30", 90, 2, 17)], "db_entry_renumbered")
    check_rows_added(judge, initial, after, "trip_entries",
                      [(None, 1, 164, "Quick photo stop", "11:00", 60, 3, 17)], "db_entry_added")
    check_rows_changed(judge, initial, after, "trips",
                       [(1, None, None, None, None, None, None, None, None, None, None, None,
                   "2026-09-29")] , "db_trip_touched")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
