#!/usr/bin/env python3
"""Deterministic verifier for Zara--7 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_7.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--7"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_locator", r"/us/en/z-stores-st1404\.html")
    check_visited_path(judge, traj, "nav_zip90401", r"z-stores-st1404\.html\?[^ ]*q=90401")
    check_visited_path(judge, traj, "nav_sm_store", r"stores-locator/zara-santa-monica-california-santa-monica-promenade-s3322")
    check_visited_path(judge, traj, "nav_zip94108", r"z-stores-st1404\.html\?[^ ]*q=94108")
    check_visited_path(judge, traj, "nav_sf_store", r"stores-locator/zara-san-francisco-california-250-post-st-san-francisco-s3441")
    check_visited_path(judge, traj, "nav_zip10003", r"z-stores-st1404\.html\?[^ ]*q=10003")
    check_visited_path(judge, traj, "nav_flatiron", r"stores-locator/zara-new-york-new-york-5th-av-flatiron-s3037")
    check_visited_path(judge, traj, "nav_ca_filter", r"z-stores-st1404\.html\?[^ ]*state=CALIFORNIA")
    check_visited_path(judge, traj, "nav_sc_store", r"stores-locator/zara-costa-mesa-california-south-coast-plaza-mall-s3265")

    check_answer_phrase(judge, answer, "zip90401_store", "SANTA MONICA PROMENADE")
    check_answer_phrase(judge, answer, "sm_phone", "8332472473")
    check_answer_phrase(judge, answer, "sm_sat", "10:00 - 21:00")
    check_answer_phrase(judge, answer, "sm_mon", "11:00 - 20:00")
    check_answer_phrase(judge, answer, "zip94108_store", "250 POST ST SAN FRANCISCO")
    check_answer_regex(judge, answer, "sf_type", r"STREET")
    check_answer_phrase(judge, answer, "sf_sun", "11:00 - 19:00")
    check_answer_phrase(judge, answer, "sf_tz", "US/Pacific")
    check_answer_regex(judge, answer, "zip10003_store", r"5TH\s+AV FLATIRON")
    check_answer_phrase(judge, answer, "fa_mon", "10:00 - 21:00")
    check_answer_regex(judge, answer, "fa_status", r"OPEN")
    check_answer_phrase(judge, answer, "sc_city", "COSTA MESA")
    check_answer_phrase(judge, answer, "sc_sun", "11:00 - 19:00")
    check_answer_regex(judge, answer, "latest_mon", r"SANTA MONICA PROMENADE")

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
