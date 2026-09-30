#!/usr/bin/env python3
"""Deterministic verifier for Zara--16 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_16.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--16"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_locator", r"/us/en/z-stores-st1404\.html")
    check_visited_path(judge, traj, "nav_az_filter", r"z-stores-st1404\.html\?[^ ]*state=ARIZONA")
    check_visited_path(judge, traj, "nav_hi_filter", r"z-stores-st1404\.html\?[^ ]*state=HAWAII")
    check_visited_path(judge, traj, "nav_hi_store", r"stores-locator/zara-honolulu-hawaii-ala-moana-center-s10285")
    check_visited_path(judge, traj, "nav_ny_filter", r"z-stores-st1404\.html\?[^ ]*state=NEW\+YORK")
    check_visited_path(judge, traj, "nav_garden_store", r"stores-locator/zara-garden-city-new-york-garden-roosevelt-field-mall-s351")
    check_visited_path(judge, traj, "nav_ca_filter", r"z-stores-st1404\.html\?[^ ]*state=CALIFORNIA")
    check_visited_path(judge, traj, "nav_sc_store", r"stores-locator/zara-costa-mesa-california-south-coast-plaza-mall-s3265")
    check_visited_path(judge, traj, "nav_newsletter", r"/newsletter")

    check_answer_number(judge, answer, "store_count", 25)
    check_answer_number(judge, answer, "state_count", 20)
    check_answer_number(judge, answer, "state_options", 21)
    check_answer_phrase(judge, answer, "az_store", "FASHION SQUARE MALL SCOTTSDALE")
    check_answer_phrase(judge, answer, "hi_store", "ALA MOANA CENTER")
    check_answer_number(judge, answer, "ny_count", 2)
    check_answer_phrase(judge, answer, "garden_city", "GARDEN CITY")
    check_answer_number(judge, answer, "garden_zip", 11530)
    check_answer_phrase(judge, answer, "sc_city", "COSTA MESA")
    check_answer_regex(judge, answer, "newsletter", r"store-fan@zara\.example")

    check_only_tables_changed(judge, initial, after, {"newsletter_signups"})
    check_rows_added(judge, initial, after, "newsletter_signups",
                     [[1, "store-fan@zara.example", "WOMAN", "2026-09-29"]], "newsletter_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
