#!/usr/bin/env python3
"""Verify Statista--5.

Find the Statista report on consumer trends for 2026. Tell me how many pages it has, its release year, its price, and the first three chapters listed in its table of contents. We are also considering the video gaming report, so compare and tell me which of the two reports has more pages.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--5"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=consumer\+trends\+2026")
    check_visited_path(judge, traj, "visited_report", r"/study/206237/")
    check_visited_path(judge, traj, "visited_gaming_report", r"/study/123559/")
    check_answer_number(judge, answer, "pages", "37", 'Consumer Trends pages')
    check_answer_phrase(judge, answer, "release_year", "2025")
    check_answer_number(judge, answer, "price", "595", 'report price')
    check_answer_phrase(judge, answer, "chapter1", "Consumer sentiment")
    check_answer_phrase(judge, answer, "chapter2", "Consumer spending and cautious optimism")
    check_answer_phrase(judge, answer, "chapter3", "How tariffs are shaping consumption")
    check_answer_number(judge, answer, "gaming_pages", "62", 'video gaming pages')
    check_answer_phrase(judge, answer, "gaming_has_more", "video gaming")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
