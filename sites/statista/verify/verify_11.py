#!/usr/bin/env python3
"""Verify Statista--11.

Log in as alice.j@test.com / TestPass123!. In her download history, find the most recent download, tell me which statistic it was, and then remove it from her favorites if it is currently saved there.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--11"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_login", r"/login")
    check_visited_path(judge, traj, "visited_downloads", r"/account/downloads")
    check_visited_path(judge, traj, "visited_favorites", r"/account/favorites")
    check_visited_path(judge, traj, "visited_statistic", r"/forecasts/1474143/")
    check_answer_phrase(judge, answer, "recent_download_stat", "Market size of AI worldwide")
    check_answer_phrase(judge, answer, "download_format", "PNG")
    check_answer_phrase(judge, answer, "removed_from_favorites", "remove")
    check_only_tables_changed(judge, initial_db, after_db, {"favorites"})
    check_favorites_delta(judge, initial_db, after_db,
                        expect_added=[],
                        expect_removed=[(1, 1474143, None)])


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
