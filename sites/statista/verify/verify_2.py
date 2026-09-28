#!/usr/bin/env python3
"""Verify Statista--2.

I need to compare how big the world's largest economies are for a client deck. Find Statista's statistic ranking countries by projected nominal GDP, note the GDP of the top economy and of Germany in trillion U.S. dollars, state which of the two is larger and by how many trillion, and save the statistic to your Statista favorites so the deck's sources are traceable.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--2"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=countries\+with\+the\+largest\+nominal\+GDP")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/268173/")
    check_visited_path(judge, traj, "visited_register", r"/register")
    check_visited_path(judge, traj, "visited_favorites", r"/account/favorites")
    check_answer_phrase(judge, answer, "top_economy", "United States")
    check_answer_number(judge, answer, "top_gdp", "32.38", 'top economy GDP')
    check_answer_phrase(judge, answer, "germany_named", "Germany")
    check_answer_number(judge, answer, "germany_gdp", "5.45", 'Germany GDP')
    check_answer_number(judge, answer, "difference", "26.93", 'difference in trillion')
    check_only_tables_changed(judge, initial_db, after_db, {"favorites", "users"})
    check_new_user(judge, initial_db, after_db,
                    "review.agent2@test.com", "review_agent2", "Review_Agent2")
    check_favorites_delta(judge, initial_db, after_db,
                        expect_added=[(5, 268173, None)],
                        expect_removed=[])


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
