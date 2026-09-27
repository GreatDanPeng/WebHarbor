#!/usr/bin/env python3
"""Verify Statista--14.

I heard inflation differs a lot by region. Find Statista's statistic comparing annual inflation rates across global regions in 2025 and report which region had the highest inflation and its rate, plus the rate for the European Union. Also tell me the survey time period the statistic covers and its exact release date.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--14"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=inflation\+rate\+selected\+global\+regions")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/256626/")
    check_answer_phrase(judge, answer, "highest_region", "Sub-Saharan Africa")
    check_answer_number(judge, answer, "highest_rate", "12.48", 'highest inflation rate')
    check_answer_number(judge, answer, "eu_rate", "2.46", 'EU inflation rate')
    check_answer_phrase(judge, answer, "survey_start", "01/01/2025")
    check_answer_phrase(judge, answer, "update_date", "Apr 15, 2026")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
