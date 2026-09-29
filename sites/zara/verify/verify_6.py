#!/usr/bin/env python3
"""Deterministic verifier for Zara--6 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_6.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_number_absent,
    check_answer_ordered, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Zara--6"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_locator", r"/us/en/z-stores-st1404\.html")
    check_visited_path(judge, traj, "nav_hi_filter", r"z-stores-st1404\.html\?[^ ]*state=HAWAII")
    check_visited_path(judge, traj, "nav_hi_store", r"stores-locator/zara-honolulu-hawaii-ala-moana-center-s10285")
    check_visited_path(judge, traj, "nav_ca_filter", r"z-stores-st1404\.html\?[^ ]*state=CALIFORNIA")
    check_visited_path(judge, traj, "nav_cc_store", r"stores-locator/zara-los-angeles-california-century-city-mall-s3612")
    check_visited_path(judge, traj, "nav_nv_filter", r"z-stores-st1404\.html\?[^ ]*state=NEVADA")
    check_visited_path(judge, traj, "nv_store", r"stores-locator/zara-las-vegas-nevada-fashion-show-mall-s3303")
    check_visited_path(judge, traj, "nav_ny_filter", r"z-stores-st1404\.html\?[^ ]*state=NEW\+YORK")
    check_visited_path(judge, traj, "nav_flatiron", r"stores-locator/zara-new-york-new-york-5th-av-flatiron-s3037")

    check_answer_phrase(judge, answer, "hi_store", "ALA MOANA CENTER")
    check_answer_phrase(judge, answer, "hi_tz", "US/Hawaii")
    check_answer_number(judge, answer, "ca_count", 5)
    check_answer_count_at_least(judge, answer, "ca_names", ["SOUTH COAST PLAZA MALL", "CENTURY CITY MALL", "ROSEVILLE WESTFIELD MALL", "250 POST ST SAN FRANCISCO", "SANTA MONICA PROMENADE"], 5)
    check_answer_phrase(judge, answer, "cc_sat", "10:00 - 22:00")
    check_answer_phrase(judge, answer, "nv_store", "FASHION SHOW MALL")
    check_answer_phrase(judge, answer, "nv_tz", "US/Pacific")
    check_answer_number(judge, answer, "ny_count", 2)
    check_answer_phrase(judge, answer, "flatiron_sat", "10:00 - 21:00")
    check_answer_regex(judge, answer, "latest_sat", r"CENTURY CITY MALL")

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
