#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--16 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_16.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--16"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_ttp_overview", r"/travel/trusted-traveler-programs(\?|$)")
    check_visited_path(judge, traj, "nav_ge_page", r"/travel/trusted-traveler-programs/global-entry")
    check_visited_path(judge, traj, "nav_tsa_page", r"/travel/trusted-traveler-programs/tsa-precheck")
    check_answer_money(judge, answer, "ge_fee", 120.00)
    check_answer_number(judge, answer, "ge_years", 5)
    check_answer_money(judge, answer, "nexus_fee", 50.00)
    check_answer_money(judge, answer, "sentri_fee", 122.25)
    check_answer_money(judge, answer, "tsa_fee", 78.00)
    check_answer_count_at_least(judge, answer, "ge_benefit_programs",
                                ["NEXUS", "SENTRI"], 2)
    check_answer_phrase(judge, answer, "fast_program", "FAST")
    check_answer_phrase(judge, answer, "fast_audience", "commercial truck drivers")
    check_answer_count_at_least(judge, answer, "fast_borders", ["Canada", "Mexico"], 2)
    check_answer_phrase(judge, answer, "ge_requirement", "background check")
    check_answer_phrase(judge, answer, "tsa_eligible", "U.S. citizens")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
