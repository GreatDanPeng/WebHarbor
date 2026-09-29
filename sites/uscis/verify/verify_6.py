#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--6 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_6.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--6"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the fee calculator for N-400/I-912/N-600, the N-400 form
    # page, the fee-waiver guidance, the poverty guidelines, the civics test.
    for nid, name in (("97352", "n400"), ("97335", "i912"), ("97356", "n600")):
        check_visited_path(judge, traj, f"nav_fee_{name}",
                           rf"/feecalculator\?[^ ]*form={nid}")
    check_visited_path(judge, traj, "nav_n400", r"/n-400")
    check_visited_path(judge, traj, "nav_fee_waiver",
                       r"/forms/filing-fees/additional-information-on-filing-a-fee-waiver")
    check_visited_path(judge, traj, "nav_poverty",
                       r"/forms/filing-fees/poverty-guidelines")
    check_visited_path(judge, traj, "nav_civics",
                       r"/citizenship-resource-center/naturalization-test-and-study-resources/2025-civics-test")
    # answer ground truth
    check_answer_money(judge, answer, "n400_paper", 760)
    check_answer_money(judge, answer, "n400_online", 710)
    check_answer_money(judge, answer, "n400_400fpg", 380)
    check_answer_number(judge, answer, "n400_military", 0)
    check_answer_number(judge, answer, "i912_fee", 0)
    check_answer_money(judge, answer, "n600_paper", 1385)
    check_answer_money(judge, answer, "n600_online", 1335)
    check_answer_phrase(judge, answer, "i912_used_for", "fee waiver")
    check_answer_count_at_least(judge, answer, "criteria",
                                ["means-tested benefit", "150%", "extreme financial hardship"], 3)
    check_answer_any(judge, answer, "means_tested_1", ["Medicaid"])
    check_answer_any(judge, answer, "means_tested_2",
                     ["SNAP", "Supplemental Nutrition Assistance Program"])
    check_answer_money(judge, answer, "poverty_h4", 45000)
    check_answer_phrase(judge, answer, "civics_resource", "128 Civics Test Questions")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
