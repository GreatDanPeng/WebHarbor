#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--12 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_12.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "CBP.gov--12"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_pti", r"/trade/priority-issues(\?|$)")
    check_visited_path(judge, traj, "nav_adcvd", r"/trade/priority-issues/adcvd")
    check_visited_path(judge, traj, "nav_ipr", r"/trade/priority-issues/ipr")
    check_visited_path(judge, traj, "nav_icp",
                       r"/trade/rulings/informed-compliance-publications")
    # F-2: ACE cross-page sub-question — the Trade section's ACE page
    check_visited_path(judge, traj, "nav_ace", r"/trade/automated")
    check_answer_number(judge, answer, "pti_count", 7)
    check_answer_count_at_least(judge, answer, "pti_names", [
        "Antidumping and Countervailing Duty", "Intellectual Property Rights",
        "Import Safety", "Textiles/Wearing Apparel", "Agriculture and Quota",
        "Revenue", "Trade Agreements"], 7)
    check_answer_phrase(judge, answer, "adcvd_expansion", "Antidumping and Countervailing Duty (AD/CVD)")
    check_answer_phrase(judge, answer, "ipr_title", "Intellectual Property Rights")
    check_answer_phrase(judge, answer, "icp_series", "What Every Member of the Trade Community Should Know")
    check_answer_phrase(judge, answer, "apparel_issue", "Textiles/Wearing Apparel")
    check_answer_phrase(judge, answer, "quota_issue", "Agriculture and Quota")
    check_answer_phrase(judge, answer, "ace_expansion", "Automated Commercial Environment")
    check_answer_any(judge, answer, "ace_used_for",
                    ["Single Window", "processing imports and exports",
                     "centralized digital system", "centralized access point"])
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
