#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--19 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_19.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--19"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # CDL HAZMAT research + fee chart + appointment wizard
    check_visited_path(judge, traj, "nav_cdl", r"/licenses-ids/cdl(?!/)")
    check_visited_path(judge, traj, "nav_hazmat", r"/licenses-ids/cdl/hazmat")
    check_visited_path(judge, traj, "nav_cdl_applying", r"/licenses-ids/cdl/applying")
    check_visited_path(judge, traj, "nav_fees", r"/vehicles/taxes-fees")
    check_visited_path(judge, traj, "nav_know_exam", r"/licenses-ids/exams/know-exam")
    check_visited_path(judge, traj, "nav_wizard", r"/appointments/new")
    check_answer_money(judge, answer, "hazmat_fee", 83.00)
    check_answer_money(judge, answer, "twic_reduced_fee", 41.00)
    check_answer_any(judge, answer, "twic_condition", ["expiring more than 1 year and 5 days out",
                                                       "more than 1 year and 5 days",
                                                       "valid twic card expiring more than 1 year"])
    check_answer_any(judge, answer, "twic_comparability", ["expire no later than", "no later than the current expiration date of the twic",
                                                           "no later than the twic"])
    check_answer_number(judge, answer, "min_age", 21)
    check_answer_any(judge, answer, "background_form", ["dl 70", "dl70"])
    check_answer_any(judge, answer, "cdl_form", ["dl 2p", "dl2p"])
    check_answer_money(judge, answer, "cdl_per_year", 8.00)
    check_answer_money(judge, answer, "cdl_minimum", 20.00)
    check_answer_money(judge, answer, "missed_appointment_fee", 50.00)
    check_answer_money(judge, answer, "endorsement_per_year", 1.00)
    check_answer_money(judge, answer, "learners_permit_fee", 3.00)
    check_answer_any(judge, answer, "hazmat_exam_language", ["only in english", "english only"])
    check_answer_regex(judge, answer, "morning_slot", r"\d{1,2}:\d{2} AM")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
