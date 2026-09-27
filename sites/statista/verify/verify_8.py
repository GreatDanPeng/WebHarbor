#!/usr/bin/env python3
"""Verify Statista--8.

I want to know which video game had the biggest cumulative eSports prize pool. Search Statista for the leading eSports games statistic, tell me the game and its prize pool in million U.S. dollars, and name the game in second place with its figure. Then switch the chart to the table view and confirm the prize pool of the third-placed game.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--8"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=leading\+eSports\+games")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/501853/")
    check_visited_path(judge, traj, "visited_table_view", r"/statistics/501853/[^?]*\?chart=table")
    check_answer_phrase(judge, answer, "top_game", "Counter-Strike 2")
    check_answer_number(judge, answer, "top_prize_pool", "18.97", 'top prize pool')
    check_answer_phrase(judge, answer, "second_game", "Dota 2")
    check_answer_number(judge, answer, "second_prize_pool", "16.47", 'second prize pool')
    check_answer_phrase(judge, answer, "third_game", "Fortnite")
    check_answer_number(judge, answer, "third_prize_pool", "12.91", 'third prize pool')
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
