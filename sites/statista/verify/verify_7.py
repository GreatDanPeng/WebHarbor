#!/usr/bin/env python3
"""Verify Statista--7.

Register a new free Statista account with the email casey.r@test.com (username casey_r, password CasePass123!). Then find the statistic about global CO2 emissions and report the emission level for the most recent year shown, and confirm the statistic appears in your new account after saving it to favorites.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--7"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_register", r"/register")
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=global\+CO2\+emissions")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/276629/")
    check_visited_path(judge, traj, "visited_table_view", r"/statistics/276629/[^?]*\?chart=table")
    check_visited_path(judge, traj, "visited_favorites", r"/account/favorites")
    check_answer_number(judge, answer, "recent_year_emissions", "38.11", '2025 CO2 level')
    check_answer_phrase(judge, answer, "recent_year", "2025")
    check_answer_phrase(judge, answer, "registered_username", "casey_r")
    check_answer_phrase(judge, answer, "saved_confirmation", "favorites")
    check_only_tables_changed(judge, initial_db, after_db, {"favorites", "users"})
    check_new_user(judge, initial_db, after_db,
                    "casey.r@test.com", "casey_r", "Casey_R")
    check_favorites_delta(judge, initial_db, after_db,
                        expect_added=[(5, 276629, None)],
                        expect_removed=[])


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
