#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--10 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_10.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--10"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_6059b_search", r"/newsroom/publications/forms\?.*q=[^#]*6059B")
    check_visited_path(judge, traj, "nav_english_detail",
                       r"/newsroom/publications/forms/6059b-4")
    check_visited_path(judge, traj, "nav_account", r"/account")
    # the catalog reports 18 entries for 6059B (5 numbered + 13 named variants)
    check_answer_number(judge, answer, "variant_count", 18)
    check_answer_count_at_least(judge, answer, "languages", [
        "English", "Arabic", "Farsi", "Italian", "Vietnamese", "Deutsch",
        "Nederlands", "Espa", "Fran", "Polski", "Portugu", "русский",
        "Hebrew", "中文", "한국어", "日本語"], 8)
    check_answer_phrase(judge, answer, "english_date", "Jul 25 2024")
    check_answer_phrase(judge, answer, "saved_form", "6059B")
    check_answer_phrase(judge, answer, "prior_saved", "7501")
    # DB: exactly one saved_forms row added for Carol + the English variant
    check_only_tables_changed(judge, initial, after, {"saved_forms"})
    check_rows_added(judge, initial, after, "saved_forms", [
        [None, 3, 63, "2026-09-28"],
    ], "saved_form_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
