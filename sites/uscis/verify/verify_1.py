#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--1 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_1.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--1"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: Case Status Online, the field office locator for 60601 and
    # 60605, the All Forms catalog N-400 details page, the glossary.
    check_visited_path(judge, traj, "nav_casestatus", r"/casestatus")
    check_visited_path(judge, traj, "nav_field_office",
                       r"/about-us/find-a-uscis-office/field-offices[^ ]*zip=60601")
    check_visited_path(judge, traj, "nav_field_office2",
                       r"/about-us/find-a-uscis-office/field-offices[^ ]*zip=60605")
    check_visited_path(judge, traj, "nav_n400", r"/n-400")
    check_visited_path(judge, traj, "nav_glossary", r"/tools/glossary")
    # answer ground truth
    check_answer_any(judge, answer, "form_type", ["N-400, Application for Naturalization",
                                                  "Form N-400"])
    check_answer_phrase(judge, answer, "current_status", "Interview Was Scheduled")
    check_answer_any(judge, answer, "status_updated", ["2026-09-20", "09/20/2026"])
    check_answer_any(judge, answer, "interview_date", ["10/21/2026"])
    check_answer_phrase(judge, answer, "interview_location", "USCIS Chicago Field Office")
    check_answer_phrase(judge, answer, "interview_street", "101 West Ida B. Wells Drive")
    check_answer_count_at_least(judge, answer, "documents",
                                ["green card", "state ID", "re-entry permits"], 3)
    check_answer_phrase(judge, answer, "office_name", "Chicago")
    check_answer_phrase(judge, answer, "office_district", "CHI")
    check_answer_any(judge, answer, "edition_date", ["01/20/25", "January 20, 2025"])
    check_answer_count_at_least(judge, answer, "pdfs",
                                ["Form N-400", "Instructions for Form N-400", "G-1151"], 2)
    check_answer_phrase(judge, answer, "naturalization_def",
                        "How a person not born in the United States voluntarily becomes a U.S. citizen")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
