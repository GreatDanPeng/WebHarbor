#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--11 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_11.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--11"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # multi-page Trade chain: the car-import page plus the internet-purchases
    # page (F-1 redesign — no longer a single-page lookup)
    check_visited_path(judge, traj, "nav_importing_car",
                       r"/trade/basic-import-export/importing-car")
    check_visited_path(judge, traj, "nav_internet_purchases",
                       r"/trade/basic-import-export/internet-purchases")
    # car-import facts
    check_answer_phrase(judge, answer, "act_1966", "Motor Vehicle Safety Act of 1966")
    check_answer_phrase(judge, answer, "form_epa", "3520-1")
    check_answer_phrase(judge, answer, "form_dot", "HS-7")
    check_answer_number(judge, answer, "duty_rate", 3)
    check_answer_phrase(judge, answer, "agreement", "USMCA")
    check_answer_number(judge, answer, "dot_age", 25)
    check_answer_any(judge, answer, "nonresident_period", ["one year", "1 year"])
    check_answer_any(judge, answer, "end_of_period",
                    ["exported", "may not be sold", "cannot be sold"])
    # internet-purchases facts
    check_answer_money(judge, answer, "mail_threshold", 2500)
    check_answer_any(judge, answer, "over_threshold",
                    ["formal entry", "held at the mail facility", "customs broker"])
    check_answer_any(judge, answer, "declaration_form", ["CN 22", "CN 23"])
    check_answer_any(judge, answer, "who_pays_duty",
                    ["importer", "the buyer", "you", "yourself"])
    check_answer_any(judge, answer, "downloads_dutiable",
                    ["not subject to duty", "not dutiable", "are not dutiable"])
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
