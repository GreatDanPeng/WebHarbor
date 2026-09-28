#!/usr/bin/env python3
"""Verify Statista--19.

I'm evaluating whether I need a paid account. Search for the statistic on global retail e-commerce sales, try to view its chart, and tell me what Statista says you need in order to see the exact figures, plus which account types include premium statistics.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--19"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=global\+retail\+e-commerce\+sales")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/379046/")
    check_visited_path(judge, traj, "visited_pricing", r"/pricing/")
    check_answer_phrase(judge, answer, "premium_requirement", "Starter")
    check_answer_phrase(judge, answer, "premium_word", "premium")
    check_answer_phrase(judge, answer, "personal_plan", "Personal")
    check_answer_phrase(judge, answer, "professional_plan", "Professional")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
