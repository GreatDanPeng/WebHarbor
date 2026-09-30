#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--17 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_17.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--17"



ESTA_NUM = "ESTA-A505B32"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_vwp", r"/travel/international-visitors/visa-waiver-program")
    for step in ("disclaimers", "applicant", "personal", "travel",
                 "eligibility", "review", "pay"):
        pat = (r"/esta/apply(\?step=disclaimers)?$" if step == "disclaimers"
               else rf"/esta/apply\?step={step}")
        check_visited_path(judge, traj, f"nav_step_{step}", pat)
    check_visited_path(judge, traj, "nav_confirmation",
                       rf"/esta/confirmation/{ESTA_NUM}")
    check_visited_path(judge, traj, "nav_peace_arch", r"/bwt/crossing/300402")
    check_visited_path(judge, traj, "nav_ttp_overview", r"/travel/trusted-traveler-programs(\?|$)")
    check_answer_phrase(judge, answer, "italy_vwp", "Italy")
    check_answer_number(judge, answer, "vwp_countries", 42)
    check_answer_phrase(judge, answer, "application_number", ESTA_NUM)
    check_answer_phrase(judge, answer, "status", "Authorization Approved")
    check_answer_number(judge, answer, "peace_arch_delay", 5)
    check_answer_phrase(judge, answer, "peace_arch_hours", "24 hrs/day")
    check_answer_money(judge, answer, "ge_fee", 120.00)
    check_only_tables_changed(judge, initial, after, {"esta_applications"})
    check_rows_added(judge, initial, after, "esta_applications", [
        [None, ESTA_NUM, None, "Ricci", "Marco", "1988-06-02", None,
         "Italy", "IT778899001", None, "2031-02-15", "marco.ricci@example.com",
         None, "Milan", "Italy", "Tourism", "1201 2nd Ave, Seattle, WA",
         "Authorization Approved", 40.27, "2026-09-28", "2028-09-28"],
    ], "esta_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
