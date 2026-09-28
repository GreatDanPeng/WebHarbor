#!/usr/bin/env python3
"""Verify Statista--1.

My marketing team wants the ranking of the most popular social networks worldwide by monthly active users. Report the top network and its user count in millions, then download the statistic as a PNG with your account and tell me where in my Statista account I can retrieve the download later.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--1"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=most\+popular\+social\+networks")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/272014/")
    check_visited_path(judge, traj, "visited_downloads", r"/account/downloads")
    check_answer_phrase(judge, answer, "top_network", "Facebook")
    check_answer_number(judge, answer, "mau_millions", "3,070", 'monthly active users')
    check_answer_phrase(judge, answer, "download_format", "PNG")
    check_answer_phrase(judge, answer, "retrieval_location", "download")
    check_only_tables_changed(judge, initial_db, after_db, {"download_events", "users"})
    check_new_user(judge, initial_db, after_db,
                    "review.agent1@test.com", "review_agent1", "Review_Agent1")
    check_download_added(judge, initial_db, after_db,
                        user_id=5, stat_id=272014,
                        report_id=None, fmt="png")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
