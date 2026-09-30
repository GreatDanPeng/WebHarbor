#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--0 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_0.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--0"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: login, dashboard (My Progress), Case Status Online for both
    # receipts, the field office locator (profile ZIP 22202), and the
    # processing-times tool (I-485 at WAS).
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_dashboard", r"/account(?!/)")
    check_visited_path(judge, traj, "nav_casestatus", r"/casestatus")
    check_visited_path(judge, traj, "nav_field_office",
                       r"/about-us/find-a-uscis-office/field-offices[^ ]*zip=22202")
    check_visited_path(judge, traj, "nav_processing",
                       r"/processing-times\?[^ ]*form=I-485[^ ]*office=WAS")
    # answer ground truth
    check_answer_any(judge, answer, "case1_form", ["I-485"])
    check_answer_phrase(judge, answer, "case1_status", "Case Is Being Actively Reviewed")
    check_answer_any(judge, answer, "case1_updated", ["2026-08-30", "08/30/2026"])
    check_answer_any(judge, answer, "case2_form", ["I-765"])
    check_answer_phrase(judge, answer, "case2_status", "New Card Is Being Produced")
    check_answer_any(judge, answer, "case2_updated", ["2026-09-18", "09/18/2026"])
    check_answer_phrase(judge, answer, "processing_office", "Washington")
    check_answer_any(judge, answer, "further_along", ["SRC2210567890", "I-765"])
    check_answer_phrase(judge, answer, "field_office_name", "Washington")
    check_answer_phrase(judge, answer, "field_office_street", "2675 Prosperity Avenue")
    check_answer_phrase(judge, answer, "pt_range", "20 Months to 11 Months")
    check_answer_phrase(judge, answer, "pt_pub", "August 29, 2018")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
