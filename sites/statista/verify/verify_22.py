#!/usr/bin/env python3
"""Verify Statista--22.

I want to know how current Statista's numbers are. Find the most recently updated statistic about worldwide inflation and the most recently updated statistic about global carbon dioxide emissions; report both last-update dates, tell me which of the two was refreshed more recently, and name the region each statistic covers.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--22"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_recent_stats", r"/recent/statistics/")
    check_visited_path(judge, traj, "visited_inflation_search", r"/serp\?q=average\+inflation\+rate\+worldwide")
    check_visited_path(judge, traj, "visited_inflation_stat", r"/statistics/256598/")
    check_visited_path(judge, traj, "visited_co2_search", r"/serp\?q=global\+carbon\+dioxide")
    check_visited_path(judge, traj, "visited_co2_stat", r"/statistics/276629/")
    check_answer_phrase(judge, answer, "inflation_update_date", "Aug 13, 2026")
    check_answer_phrase(judge, answer, "co2_update_date", "April 2026")
    check_answer_phrase(judge, answer, "region_worldwide", "Worldwide")
    check_answer_phrase(judge, answer, "more_recent", "inflation")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
