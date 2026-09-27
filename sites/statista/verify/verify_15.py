#!/usr/bin/env python3
"""Verify Statista--15.

Log in as carol.d@test.com / TestPass123!. She has a Professional Account: download the 'Consumer Trends 2026' report with her account, then check her download history and tell me the format of that download and the other statistic she downloaded most recently before it.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--15"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_login", r"/login")
    check_visited_path(judge, traj, "visited_report", r"/study/206237/")
    check_visited_path(judge, traj, "visited_downloads", r"/account/downloads")
    check_answer_phrase(judge, answer, "download_format", "PDF")
    check_answer_phrase(judge, answer, "prior_statistic", "renewable energy capacity")
    check_answer_phrase(judge, answer, "prior_format", "PPT")
    check_only_tables_changed(judge, initial_db, after_db, {"download_events"})
    check_download_added(judge, initial_db, after_db,
                        user_id=3, stat_id=None,
                        report_id=206237, fmt="pdf")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
