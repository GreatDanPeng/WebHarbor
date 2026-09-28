#!/usr/bin/env python3
"""Verify Statista--4.

My team needs premium statistics and one report download. Compare Statista's account plans and tell me which plan is the cheapest that includes premium statistics, what the Professional Account costs per year, and which plans can download reports. Then register a free account for the email frank.miller@test.com (username frank_m) so we can start with the free statistics today.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--4"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_pricing", r"/pricing/")
    check_visited_path(judge, traj, "visited_register", r"/register")
    check_visited_path(judge, traj, "visited_account", r"/account")
    check_answer_phrase(judge, answer, "cheapest_premium_plan", "Starter")
    check_answer_number(judge, answer, "starter_price", "199", 'Starter price')
    check_answer_number(judge, answer, "professional_yearly", "2,388", 'Professional yearly')
    check_answer_phrase(judge, answer, "personal_plan", "Personal")
    check_answer_phrase(judge, answer, "professional_plan", "Professional")
    check_answer_phrase(judge, answer, "registered_email", "frank.miller@test.com")
    check_only_tables_changed(judge, initial_db, after_db, {"users"})
    check_new_user(judge, initial_db, after_db,
                    "frank.miller@test.com", "frank_m", "Frank_M")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
