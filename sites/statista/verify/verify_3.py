#!/usr/bin/env python3
"""Verify Statista--3.

Log in with the benchmark account bob.c@test.com / TestPass123!. Using his account, find the statistic on renewable energy capacity by country, tell me which country leads in installed capacity and its gigawatt figure, then add the statistic to his favorites.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--3"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_login", r"/login")
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=renewable\+energy\+capacity")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/267233/")
    check_visited_path(judge, traj, "visited_favorites", r"/account/favorites")
    check_answer_phrase(judge, answer, "leading_country", "China")
    check_answer_number(judge, answer, "capacity_gw", "2,258.02", 'installed capacity in GW')
    check_answer_phrase(judge, answer, "mentions_favorites", "favorites")
    check_only_tables_changed(judge, initial_db, after_db, {"favorites"})
    check_favorites_delta(judge, initial_db, after_db,
                        expect_added=[(2, 267233, None)],
                        expect_removed=[])


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
