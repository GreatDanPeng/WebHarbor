#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--4 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_4.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--4"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_vwp", r"/travel/international-visitors/visa-waiver-program")
    check_visited_path(judge, traj, "nav_esta_page", r"/travel/international-visitors/esta")
    check_visited_any(judge, traj, "nav_esta_check",
                      [r"/esta/check($|\?.*passport_number=DE29384756)"])
    check_answer_number(judge, answer, "vwp_countries", 42)
    check_answer_number(judge, answer, "max_stay_days", 90)
    check_answer_phrase(judge, answer, "germany_listed", "Germany")
    check_answer_money(judge, answer, "esta_fee", 40.27)
    check_answer_phrase(judge, answer, "epassport", "e-Passport")
    check_answer_phrase(judge, answer, "app_number", "ESTA-88291045")
    check_answer_phrase(judge, answer, "app_status", "Authorization Approved")
    check_answer_phrase(judge, answer, "app_expiry", "2028-08-20")
    check_answer_phrase(judge, answer, "admissibility", "does not determine")
    check_answer_phrase(judge, answer, "who_determines", "officers determine admissibility")
    check_answer_any(judge, answer, "when_to_apply",
                     ["as soon as they begin preparing travel plans",
                      "prior to purchasing", "as soon as travel plans begin",
                      "before purchasing", "before buying"])
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
