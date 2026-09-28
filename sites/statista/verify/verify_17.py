#!/usr/bin/env python3
"""Verify Statista--17.

Browse Statista's industry overview and open the Internet industry. From the statistics listed for that industry, find the one about the number of internet and social media users in the United States, report both figures for October 2025, and tell me the exact release date shown on the statistic's page.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--17"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_industry_overview", r"/markets/")
    check_visited_path(judge, traj, "visited_internet_industry", r"/markets/424/internet/")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/1044012/")
    check_answer_number(judge, answer, "internet_users", "324", 'US internet users millions')
    check_answer_number(judge, answer, "social_users", "254", 'US social media users millions')
    check_answer_phrase(judge, answer, "release_date", "Mar 18, 2026")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
