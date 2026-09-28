#!/usr/bin/env python3
"""Verify Statista--13.

Use the search results filter for content type Reports to find Statista's in-depth market analysis of artificial intelligence. Report how many pages that report has, its release date, and its price, tell me the first chapter in its table of contents, and save the report to your Statista favorites with the account carol.d@test.com / TestPass123!.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--13"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=artificial\+intelligence")
    check_visited_path(judge, traj, "visited_reports_filter", r"content_type=Reports")
    check_visited_path(judge, traj, "visited_report", r"/study/50485/")
    check_visited_path(judge, traj, "visited_login", r"/login")
    check_visited_path(judge, traj, "visited_favorites", r"/account/favorites")
    check_answer_number(judge, answer, "pages", "295", 'AI report pages')
    check_answer_phrase(judge, answer, "release_date", "September 2025")
    check_answer_number(judge, answer, "price", "1,995", 'AI report price')
    check_answer_phrase(judge, answer, "first_toc_entry", "Description")
    check_answer_phrase(judge, answer, "saved_with_carol", "carol")
    check_only_tables_changed(judge, initial_db, after_db, {"favorites"})
    check_favorites_delta(judge, initial_db, after_db,
                        expect_added=[(3, None, 50485)],
                        expect_removed=[])


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
