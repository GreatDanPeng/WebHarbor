#!/usr/bin/env python3
"""Verify Statista--20.

Log in as david.k@test.com / TestPass123! (a Starter Account). Open Statista's topic page on artificial intelligence worldwide and report the global AI market size and the generative AI market size for 2025 from its key insights, then save the topic's editor's pick statistic about the AI market to his favorites.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--20"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_login", r"/login")
    check_visited_path(judge, traj, "visited_topic", r"/topics/3104/")
    check_visited_path(judge, traj, "visited_pick_statistic", r"/forecasts/1474143/")
    check_visited_path(judge, traj, "visited_favorites", r"/account/favorites")
    check_answer_number(judge, answer, "global_ai_market", "617.62", 'global AI market size')
    check_answer_number(judge, answer, "gen_ai_market", "63", 'generative AI market size')
    check_answer_phrase(judge, answer, "saved_confirmation", "favorites")
    check_only_tables_changed(judge, initial_db, after_db, {"favorites"})
    check_favorites_delta(judge, initial_db, after_db,
                        expect_added=[(4, 1474143, None)],
                        expect_removed=[])


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
