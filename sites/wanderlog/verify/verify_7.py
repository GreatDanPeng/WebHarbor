#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--7 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Usage: python3 verify_7.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Wanderlog--7"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_trip", r"/plan/icelandring")
    check_visited_path(judge, traj, "nav_budget", r"/plan/icelandring/budget")
    check_answer_money(judge, answer, "total", 2204.5)
    check_answer_money(judge, answer, "bob_paid", 1105.5)
    check_answer_money(judge, answer, "dana_paid", 1099.0)
    check_answer_phrase(judge, answer, "settlement", 'Dana Kim owes Bob Chen $3.25')
    check_answer_money(judge, answer, "transport_total", 890.0)
    check_answer_money(judge, answer, "fuel", 87.3)
    check_answer_money(judge, answer, "parking", 12.5)
    check_answer_phrase(judge, answer, "expense_date", '2026-11-07')
    check_answer_money(judge, answer, "new_total", 2304.3)
    check_answer_money(judge, answer, "new_dana_paid", 1186.3)
    check_answer_money(judge, answer, "new_bob_paid", 1118.0)
    check_answer_phrase(judge, answer, "new_settlement", 'Bob Chen owes Dana Kim $34.15')
    check_only_tables_changed(judge, initial, after, {'expenses', 'trips'})
    check_rows_added(judge, initial, after, "expenses",
                      [(None, 3, "Fuel", 8730, "Transport", 20, "2026-11-07", "[18, 20]"),
                    (None, 3, "Airport parking", 1250, "Transport", 18,
                    "2026-11-07", "[18, 20]")], "db_both_added")
    check_rows_changed(judge, initial, after, "trips",
                       [(3, None, None, None, None, None, None, None, None, None, None, None,
                  "2026-09-29")], "db_trip_touched")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
