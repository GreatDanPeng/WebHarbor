#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--6 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_6.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--6"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_trip", r"/plan/icelandring")
    check_visited_path(judge, traj, "nav_checklist", r"/plan/icelandring/checklist")
    check_answer_number(judge, answer, "packing_done", 3)
    check_answer_number(judge, answer, "packing_total", 4)
    check_answer_phrase(judge, answer, "undone_packing", 'Car insurance documents')
    check_answer_phrase(judge, answer, "new_item", 'Aurora forecast app')
    check_answer_number(judge, answer, "todo_done_after", 2)
    check_answer_number(judge, answer, "todo_total_after", 3)
    check_answer_phrase(judge, answer, "new_packing", 'Thermal base layers')
    check_answer_number(judge, answer, "packing_done_after", 4)
    check_answer_number(judge, answer, "packing_total_after", 5)
    check_only_tables_changed(judge, initial, after, {'checklist_items'})
    check_rows_added(judge, initial, after, "checklist_items",
                      [(None, 3, "Aurora forecast app", "todo", 1, 18, 7),
                    (None, 3, "Thermal base layers", "packing", 0, 18, 8)], "db_both_added")
    check_rows_changed(judge, initial, after, "checklist_items",
                       [(16, 3, "Car insurance documents", "packing", 1, 18, 4)], "db_packing_toggled")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
