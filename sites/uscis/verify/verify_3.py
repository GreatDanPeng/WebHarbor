#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--3 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_3.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--3"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the processing-times tool for N-400 at SEA/CHI/LOS, the
    # field office locator for 98101, the fee calculator N-336 record.
    check_visited_path(judge, traj, "nav_pt", r"/processing-times\?[^ ]*form=N-400")
    for office in ("SEA", "CHI", "LOS"):
        check_visited_path(judge, traj, f"nav_pt_{office}",
                           rf"/processing-times\?[^ ]*form=N-400[^ ]*office={office}")
    check_visited_path(judge, traj, "nav_field_office",
                       r"/about-us/find-a-uscis-office/field-offices[^ ]*zip=98101")
    check_visited_path(judge, traj, "nav_feecalculator",
                       r"/feecalculator\?[^ ]*form=97351")
    # answer ground truth
    check_answer_phrase(judge, answer, "sea_range", "21 Months to 15.5 Months")
    check_answer_phrase(judge, answer, "sea_pub", "April 05, 2019")
    check_answer_phrase(judge, answer, "sea_srd", "August 03, 2017")
    check_answer_phrase(judge, answer, "sea_inquiry", "submit an inquiry about your case online")
    check_answer_phrase(judge, answer, "sea_cat_label", "160A")
    check_answer_phrase(judge, answer, "sea_cat_range", "21 Months to 15.5 Months")
    check_answer_phrase(judge, answer, "chi_range", "18 Months to 9 Months")
    check_answer_phrase(judge, answer, "chi_pub", "April 05, 2019")
    check_answer_phrase(judge, answer, "los_range", "17 Months to 10.5 Months")
    check_answer_phrase(judge, answer, "los_pub", "December 18, 2018")
    check_answer_count_at_least(judge, answer, "fastest_upper", ["Chicago", "9 Months to"], 1)
    check_answer_phrase(judge, answer, "seattle_office", "Seattle")
    check_answer_phrase(judge, answer, "seattle_street", "12500 Tukwila International Boulevard")
    check_answer_money(judge, answer, "n336_paper", 830)
    check_answer_money(judge, answer, "n336_online", 780)
    check_answer_money(judge, answer, "n565_paper", 555)
    check_answer_money(judge, answer, "n565_online", 505)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
