#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--17 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_17.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_ordered,
    check_answer_money_after, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Virginia DMV--17"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # insurance requirements research chain
    check_visited_path(judge, traj, "nav_vehicles", r"/vehicles(?!/)")
    check_visited_path(judge, traj, "nav_coverage", r"/vehicles/insurance-coverage")
    check_visited_path(judge, traj, "nav_insurance", r"/vehicles/insurance-requirements")
    check_visited_path(judge, traj, "nav_verification", r"/online-services/insurance")
    check_visited_path(judge, traj, "nav_payment_plan", r"/licenses-ids/payment-plan-program")
    check_visited_path(judge, traj, "nav_registration", r"/vehicles/registration")
    check_visited_path(judge, traj, "nav_roanoke_search", r"/all-locations\?q=Roanoke")
    check_visited_path(judge, traj, "nav_appointments", r"/appointments(?!/)")
    check_answer_money(judge, answer, "limit_person", 50000)
    check_answer_money(judge, answer, "limit_accident", 100000)
    check_answer_money(judge, answer, "limit_property", 25000)
    check_answer_money(judge, answer, "old_limit_person", 30000)
    check_answer_money(judge, answer, "old_limit_accident", 60000)
    check_answer_money(judge, answer, "old_limit_property", 20000)
    check_answer_any(judge, answer, "monitoring", ["electronically", "electronic verification",
                                                    "carriers send dmv updates"])
    check_answer_count_at_least(judge, answer, "verification_needs",
                                ["title number", "last 4 digits", "policy number",
                                 "insurance company name"], 3)
    check_answer_count_at_least(judge, answer, "cancel_during_registration",
        ["reinsure the vehicle", "reinsure", "deactivate the plates", "deactivate",
         "surrender the plates", "surrender"], 2)
    check_answer_money(judge, answer, "noncompliance_fee", 600)
    check_answer_any(judge, answer, "sr22", ["sr-22", "sr22"])
    check_answer_any(judge, answer, "sr22_years", ["three years", "3 years"])
    check_answer_any(judge, answer, "ach_answer", ["does not offer automatic ach", "no ach",
                                                   "not offer automated clearing house"])
    check_answer_any(judge, answer, "for_hire_note", ["for-hire vehicles require higher insurance limits",
                                                      "for-hire vehicles require higher limits",
                                                      "higher insurance limits"])
    check_answer_count_at_least(judge, answer, "visit_options",
                                ["appointment", "e-ticket", "walk-in"], 3)
    check_answer_any(judge, answer, "roanoke_office", ["roanoke"])
    check_answer_phrase(judge, answer, "roanoke_address", "5220 Valleypark Drive")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
