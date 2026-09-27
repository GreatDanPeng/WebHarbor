#!/usr/bin/env python3
"""Verify Statista--18.

I want to know which social platform grew fastest. Find Statista's statistic on year-on-year audience growth of selected social media platforms, report the platform with the highest growth and its percentage, the platform that shrank the most, and how many platforms in the chart grew by more than 15 percent.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--18"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=year-on-year\+audience\+growth")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/1294062/")
    check_answer_phrase(judge, answer, "fastest_grower", "Pinterest")
    check_answer_number(judge, answer, "growth_pct", "67.3", 'highest growth percent')
    check_answer_phrase(judge, answer, "biggest_shrinker", "X/Twitter")
    check_answer_number(judge, answer, "shrink_pct", "20.1", 'largest decline percent')
    check_answer_any(judge, answer, "over_15pct_count", ["3", "three"], 'platforms above 15 percent')
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
