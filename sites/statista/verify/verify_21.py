#!/usr/bin/env python3
"""Verify Statista--21.

I want to contact Statista about a report purchase. Using their contact form, send an inquiry with the name 'Dana White', the email dana.white@example.com, and a question about volume licensing for the video gaming report. Confirm what the site tells you after submitting, and also tell me the current price of that video gaming report.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--21"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_contact", r"/contact/")
    check_visited_path(judge, traj, "visited_gaming_report", r"/study/123559/")
    check_answer_phrase(judge, answer, "inquiry_name", "Dana White")
    check_answer_phrase(judge, answer, "inquiry_email", "dana.white@example.com")
    check_answer_phrase(judge, answer, "confirmation", "sent")
    check_answer_number(judge, answer, "gaming_report_price", "495", 'video gaming report price')
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
