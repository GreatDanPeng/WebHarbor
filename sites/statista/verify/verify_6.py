#!/usr/bin/env python3
"""Verify Statista--6.

The ride-hailing market is booming and I want its outlook. Navigate Statista's Market Insights to the worldwide ride-hailing market page and report the projected 2026 revenue, the projected market volume by 2030, and which country is expected to generate the most revenue.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--6"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_outlook", r"/outlook/")
    check_visited_path(judge, traj, "visited_mobility_segment", r"/outlook/mobility-markets/")
    check_visited_path(judge, traj, "visited_ridehailing_market", r"/outlook/mmo/shared-mobility/ride-hailing/worldwide/")
    check_answer_number(judge, answer, "revenue_2026", "188.60", '2026 revenue')
    check_answer_number(judge, answer, "volume_2030", "229.98", '2030 market volume')
    check_answer_phrase(judge, answer, "top_country", "China")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
