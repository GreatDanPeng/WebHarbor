#!/usr/bin/env python3
"""Deterministic verifier for Verizon--16 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_16.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_number_absent, check_answer_ordered, check_answer_phrase,
    check_answer_regex, check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, db_one, final_answer, run_verifier,
)

TASK_ID = "Verizon--16"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_support", r"/support/$")
    check_visited_path(judge, traj, "nav_troubleshoot", r"/support/troubleshoot/")
    check_visited_path(judge, traj, "nav_contact_us", r"/support/contact_us/")
    check_visited_path(judge, traj, "nav_stores", r"/stores/$")
    check_visited_path(judge, traj, "nav_wa", r"/stores/washington/$")
    check_visited_path(judge, traj, "nav_spokane", r"/stores/washington/spokane/$")

    # answer ground truth
    check_answer_count_at_least(judge, answer, "google_steps",
        ["Check the coverage map for your address",
         "Toggle Airplane mode, then restart the phone",
         "Reset network settings"], 3)
    check_answer_regex(judge, answer, "google_rec",
        r"eSIM profile may need a refresh|swap to a physical SIM")
    check_answer_regex(judge, answer, "apple_first_step",
        r"Open Settings and check Battery health")
    check_answer_regex(judge, answer, "apple_rec",
        r"battery needs service|Low Power Mode")
    check_answer_regex(judge, answer, "samsung_rec",
        r"nationwide 5G|5G UW indicator")
    check_answer_phrase(judge, answer, "tech_support_number", "800-922-0204")
    check_answer_phrase(judge, answer, "tech_support_hours", "8 AM - 12 AM PDT (Sun - Sat)")
    check_answer_number(judge, answer, "spokane_count", 11)
    check_answer_regex(judge, answer, "spokane_appts",
        r"[Ss]chedule an appointment|accepts appointments|[Aa]ppointments accepted")

    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
