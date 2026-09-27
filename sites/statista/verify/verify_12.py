#!/usr/bin/env python3
"""Verify Statista--12.

I'm researching Instagram's audience. Find the statistic on Instagram audience size by country, report the country with the largest audience and its size in millions, tell me how many countries in the chart have an audience above 100 million, and note the exact release date of the statistic.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--12"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=Instagram\+audience\+size")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/578364/")
    check_answer_phrase(judge, answer, "largest_country", "India")
    check_answer_number(judge, answer, "audience_millions", "480.55", 'Instagram audience')
    check_answer_any(judge, answer, "countries_over_100m", ["3", "three"], 'countries above 100M')
    check_answer_phrase(judge, answer, "release_date", "Oct 21, 2025")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
