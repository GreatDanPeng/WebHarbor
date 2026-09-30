#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--18 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_18.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--18"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_account", r"/account")
    check_visited_any(judge, traj, "nav_esta_check",
                      [r"/esta/check($|\?.*application_number=ESTA-88452017)",
                       r"/esta/confirmation/ESTA-88452017"])
    check_visited_path(judge, traj, "nav_esta_page", r"/travel/international-visitors/esta")
    check_answer_phrase(judge, answer, "esta_number", "ESTA-88452017")
    check_answer_phrase(judge, answer, "esta_status", "Authorization Pending")
    check_answer_phrase(judge, answer, "created", "2026-09-26")
    check_answer_phrase(judge, answer, "checker_status", "Authorization Pending")
    check_answer_phrase(judge, answer, "passport_type", "e-Passport")
    check_answer_phrase(judge, answer, "passport_feature", "electronic chip")
    check_answer_any(judge, answer, "when_to_apply",
                     ["as soon as they begin preparing travel plans",
                      "prior to purchasing", "as soon as travel plans begin",
                      "before purchasing", "before buying"])
    check_answer_money(judge, answer, "esta_fee", 40.27)
    check_answer_any(judge, answer, "expiration_state",
                     ["no expiration", "not yet", "none", "—", "pending"])
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
