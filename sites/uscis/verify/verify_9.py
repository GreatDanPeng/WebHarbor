#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--9 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_9.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--9"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the field office locator for 60601/60661/53201, the
    # processing-times tool for N-400 at CHI and MIL, the AAO page, the fee
    # calculator I-290B record.
    for z in ("60601", "60661", "53201"):
        check_visited_path(judge, traj, f"nav_field_{z}",
                           rf"/about-us/find-a-uscis-office/field-offices[^ ]*zip={z}")
    for office in ("CHI", "MIL"):
        check_visited_path(judge, traj, f"nav_pt_{office}",
                           rf"/processing-times\?[^ ]*form=N-400[^ ]*office={office}")
    check_visited_path(judge, traj, "nav_aao",
                       r"/administrative-appeals/aao-processing-times")
    check_visited_path(judge, traj, "nav_feecalculator",
                       r"/feecalculator\?[^ ]*form=97280")
    # answer ground truth
    check_answer_phrase(judge, answer, "designation", "CHI")
    check_answer_phrase(judge, answer, "office_name", "Chicago")
    check_answer_phrase(judge, answer, "street", "101 West Ida B. Wells Drive")
    check_answer_phrase(judge, answer, "district", "CHI")
    check_answer_regex(judge, answer, "region", r"\bC\b")
    check_answer_phrase(judge, answer, "service_center", "NSC")
    check_answer_phrase(judge, answer, "same_office_60661", "Chicago")
    check_answer_phrase(judge, answer, "mil_office", "Milwaukee")
    check_answer_count_at_least(judge, answer, "same_service_center",
                                ["NSC", "same service center"], 1)
    check_answer_phrase(judge, answer, "n400_chi_range", "18 Months to 9 Months")
    check_answer_phrase(judge, answer, "n400_chi_pub", "April 05, 2019")
    check_answer_phrase(judge, answer, "n400_mil_range", "19.5 Months to 8 Months")
    check_answer_phrase(judge, answer, "n400_mil_pub", "March 19, 2019")
    check_answer_phrase(judge, answer, "aao_goal", "180 days")
    check_answer_money(judge, answer, "i290b_fee", 800)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
