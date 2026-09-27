#!/usr/bin/env python3
"""Verify Statista--16.

I follow energy markets. Find Statista's statistic with weekly oil prices for Brent, the OPEC basket and WTI, switch it to the table view, and report the most recent week's Brent price, the WTI price for the same week, and the OPEC basket price for that week.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--16"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=weekly\+oil\+prices\+Brent")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/326017/")
    check_visited_path(judge, traj, "visited_table_view", r"/statistics/326017/[^?]*\?chart=table")
    check_answer_phrase(judge, answer, "recent_week", "Jul 21")
    check_answer_number(judge, answer, "brent_price", "91.47", 'Brent price')
    check_answer_number(judge, answer, "wti_price", "84.91", 'WTI price')
    check_answer_number(judge, answer, "opec_price", "88.5", 'OPEC basket price')
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
