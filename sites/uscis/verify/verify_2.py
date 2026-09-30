#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--2 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_2.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--2"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the processing-times tool for I-485 at CHI/MIA/HOU/MIL, the
    # field office locator for 33101, the civil surgeon locator for 33101.
    check_visited_path(judge, traj, "nav_pt", r"/processing-times\?[^ ]*form=I-485")
    for office in ("CHI", "MIA", "HOU", "MIL"):
        check_visited_path(judge, traj, f"nav_pt_{office}",
                           rf"/processing-times\?[^ ]*form=I-485[^ ]*office={office}")
    check_visited_path(judge, traj, "nav_field_office",
                       r"/about-us/find-a-uscis-office/field-offices[^ ]*zip=33101")
    check_visited_path(judge, traj, "nav_surgeon",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=33101")
    # answer ground truth: office-level ranges must be attributed correctly
    check_answer_phrase(judge, answer, "chi_range", "35.5 Months to 13.5 Months")
    check_answer_phrase(judge, answer, "chi_pub", "November 14, 2018")
    check_answer_phrase(judge, answer, "chi_srd", "January 10, 2017")
    check_answer_phrase(judge, answer, "mia_range", "25.5 Months to 11.5 Months")
    check_answer_phrase(judge, answer, "mia_srd", "January 02, 2017")
    check_answer_phrase(judge, answer, "hou_range", "26.5 Months to 21 Months")
    check_answer_phrase(judge, answer, "hou_pub", "September 27, 2018")
    check_answer_phrase(judge, answer, "hou_srd", "October 10, 2016")
    check_answer_phrase(judge, answer, "mil_range", "23.5 Months to 10.5 Months")
    check_answer_phrase(judge, answer, "mil_pub", "November 07, 2018")
    check_answer_count_at_least(judge, answer, "fastest_upper", ["Miami", "11.5"], 1)
    check_answer_phrase(judge, answer, "chi_inquiry", "submit an inquiry about your case online")
    check_answer_phrase(judge, answer, "chi_cat_employment", "23.5 Months to 13.5 Months")
    check_answer_phrase(judge, answer, "chi_cat_family", "35.5 Months to 13.5 Months")
    check_answer_phrase(judge, answer, "mia_office_street", "8801 NW 7th Avenue")
    check_answer_phrase(judge, answer, "surgeon_name", "PHYSICIANS ASSOCIATES, P.A.")
    check_answer_phrase(judge, answer, "surgeon_street", "606 WEST FLAGLER STREET")
    check_answer_any(judge, answer, "surgeon_dist", ["0.6 miles", "0.6"])
    check_answer_number(judge, answer, "spanish_count", 5)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
