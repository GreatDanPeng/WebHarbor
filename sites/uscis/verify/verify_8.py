#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--8 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_8.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_any, check_answer_count_at_least, check_answer_money,
    check_answer_number, check_answer_ordered, check_answer_phrase,
    check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "USCIS.gov--8"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the civil surgeon locator for 60601 with female and male
    # filters, then ZIP 02108 with the same two filters.
    check_visited_path(judge, traj, "nav_surgeon",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=60601")
    check_visited_path(judge, traj, "nav_surgeon_female",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=60601[^ ]*gender=Female")
    check_visited_path(judge, traj, "nav_surgeon_male",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=60601[^ ]*gender=Male")
    check_visited_path(judge, traj, "nav_surgeon_boston",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=02108")
    check_visited_path(judge, traj, "nav_surgeon_boston_female",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=02108[^ ]*gender=Female")
    check_visited_path(judge, traj, "nav_surgeon_boston_male",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=02108[^ ]*gender=Male")
    # answer ground truth
    check_answer_number(judge, answer, "result_count", 10)
    check_answer_phrase(judge, answer, "first_name", "PASSPORT HEALTH: CHICAGO")
    check_answer_phrase(judge, answer, "first_addr", "111 W WASHINGTON STREET")
    check_answer_phrase(judge, answer, "first_phone", "312-641-6228")
    check_answer_any(judge, answer, "first_dist", ["0.4 miles", "0.4"])
    check_answer_phrase(judge, answer, "second_name", "PRISM HOLISTIC CARE LTD")
    check_answer_phrase(judge, answer, "second_street", "33 W GRAND STREET")
    check_answer_phrase(judge, answer, "second_doctor", "DR. MEHBUB KAPADIA")
    check_answer_phrase(judge, answer, "second_phone", "800-325-1812")
    check_answer_number(judge, answer, "female_count", 4)
    check_answer_phrase(judge, answer, "first_female", "DR. CYNTHIA ROSS")
    check_answer_phrase(judge, answer, "female_practice", "CONCENTRA / URGENT CARE")
    check_answer_number(judge, answer, "male_count", 5)
    check_answer_phrase(judge, answer, "boston_name", "ARENA CARE AND WELLNESS LLC")
    check_answer_phrase(judge, answer, "boston_street", "50 CONGRESS STREET")
    check_answer_phrase(judge, answer, "boston_doctor", "DR. OMKAR VAIDYA")
    check_answer_phrase(judge, answer, "boston_phone", "617-513-8568")
    check_answer_number(judge, answer, "boston_female_count", 5)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
