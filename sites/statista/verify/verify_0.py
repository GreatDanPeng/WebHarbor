#!/usr/bin/env python3
"""Verify Statista--0.

I'm preparing a briefing on the global economy. Find Statista's statistic on the average inflation rate worldwide from 1980 onwards, tell me the average world inflation rate for 2025 and the value forecast for 2031, and save the statistic to your Statista favorites so I can pull it up later.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--0"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=average\+inflation\+rate\+worldwide")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/256598/")
    check_visited_path(judge, traj, "visited_table_view", r"/statistics/256598/[^?]*\?chart=table")
    check_visited_path(judge, traj, "visited_register", r"/register")
    check_visited_path(judge, traj, "visited_favorites", r"/account/favorites")
    check_answer_number(judge, answer, "inflation_2025", "4.13", '2025 average world inflation')
    check_answer_number(judge, answer, "inflation_2031", "3.2", '2031 forecast value')
    check_answer_phrase(judge, answer, "mentions_favorites", "favorites")
    check_only_tables_changed(judge, initial_db, after_db, {"favorites", "users"})
    check_new_user(judge, initial_db, after_db,
                    "review.agent0@test.com", "review_agent0", "Review_Agent0")
    check_favorites_delta(judge, initial_db, after_db,
                        expect_added=[(5, 256598, None)],
                        expect_removed=[])


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
