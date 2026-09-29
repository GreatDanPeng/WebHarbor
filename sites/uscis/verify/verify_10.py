#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--10 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_10.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--10"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the field office locator for 77002/77046, the appointment
    # tool, Case Status Online for both Houston receipts, the fee calculator
    # I-90 record.
    for z in ("77002", "77046"):
        check_visited_path(judge, traj, f"nav_field_{z}",
                           rf"/about-us/find-a-uscis-office/field-offices[^ ]*zip={z}")
    check_visited_path(judge, traj, "nav_appointment", r"/appointment")
    check_visited_path(judge, traj, "nav_casestatus", r"/casestatus")
    check_visited_path(judge, traj, "nav_feecalculator",
                       r"/feecalculator\?[^ ]*form=97259")
    # answer ground truth
    check_answer_phrase(judge, answer, "designation", "HOU")
    check_answer_phrase(judge, answer, "office_name", "Houston")
    check_answer_phrase(judge, answer, "street", "810 Gears Road")
    check_answer_phrase(judge, answer, "district", "DAL")
    check_answer_phrase(judge, answer, "same_office_77046", "Houston")
    for i, svc in enumerate(["ADIT Stamp", "Emergency Advance Parole (EAP)",
                             "Immigration Judge Grant", "Other"]):
        check_answer_phrase(judge, answer, f"online_service_{i + 1}", svc)
    check_answer_phrase(judge, answer, "asylum_group", "Asylum Seekers And NACARA Applicants")
    check_answer_phrase(judge, answer, "asylum_office", "Arlington Asylum Office")
    check_answer_any(judge, answer, "international_note",
                     ["international USCIS office", "U.S. embassy or consulate"])
    check_answer_any(judge, answer, "case1_form", ["I-90"])
    check_answer_phrase(judge, answer, "case1_status", "New Card Is Being Produced")
    check_answer_any(judge, answer, "case2_form", ["I-131"])
    check_answer_phrase(judge, answer, "case2_status", "Case Was Received")
    check_answer_money(judge, answer, "i90_paper", 465)
    check_answer_money(judge, answer, "i90_online", 415)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
