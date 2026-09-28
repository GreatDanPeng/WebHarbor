#!/usr/bin/env python3
"""Verify Statista--10.

Find Statista's topic page on TikTok. From its key insights section, report TikTok's number of global users and its brand value, and tell me the name of the report Statista offers on this topic. Then look at the editor's picks and tell me the last-update date of the TikTok penetration statistic.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--10"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=TikTok")
    check_visited_path(judge, traj, "visited_topic", r"/topics/6077/")
    check_visited_path(judge, traj, "visited_penetration_stat", r"/statistics/1299829/")
    check_answer_number(judge, answer, "global_users", "1.99", 'global users bn')
    check_answer_number(judge, answer, "brand_value", "75.67", 'brand value bn USD')
    check_answer_phrase(judge, answer, "report_named", "TikTok")
    check_answer_phrase(judge, answer, "penetration_update_date", "Jun 12, 2026")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
