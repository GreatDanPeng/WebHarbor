#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--3 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the reviewer's independent
Playwright honest walks on the review container wh-vadm-review, seed md5
e20897642a951494ced5ad6393a78ad7) — never read from tasks.jsonl.
Usage: python3 verify_3.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_ordered,
    check_answer_phrase, check_answer_regex, check_read_only,
    check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Virginia DMV--3"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # alice.j: College plates -> Virginia Tech -> buy Go Hokies with HOKIE4
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_plates_search", r"/vehicles/license-plates/search")
    check_visited_path(judge, traj, "nav_college_filter", r"/vehicles/license-plates/search\?category=College")
    check_visited_path(judge, traj, "nav_vt_search", r"/vehicles/license-plates/search\?[^ ]*virginia\+tech")
    check_visited_path(judge, traj, "nav_plate_detail", r"/vehicles/license-plates/search/virginia-tech-go-hokies")
    check_visited_path(judge, traj, "nav_purchase", r"/account/plates/virginia-tech-go-hokies/purchase")
    check_answer_money(judge, answer, "plate_fee", 25.00)
    check_answer_any(judge, answer, "personalization", ["personalization available: yes", "yes, personalization", "personalization: yes", "supports personalization", "personalization yes", "available: yes"])
    check_answer_any(judge, answer, "type_codes", ["hokie", "hokhp"])
    check_answer_money(judge, answer, "personalized_fee", 10.00)
    check_answer_money(judge, answer, "revenue_transfer", 15.00)
    check_answer_number(judge, answer, "revenue_threshold", 1000)
    check_answer_money(judge, answer, "total_charged", 35.00)
    check_answer_regex(judge, answer, "receipt_number", r"PLT\d{6}-[A-F0-9]{6}")
    check_only_tables_changed(judge, initial, after, {"transactions", "vehicles"})
    check_rows_added(judge, initial, after, "transactions", [
        (None, "rx:^PLT\\d{6}-[A-F0-9]{6}$", 1, "Plate Purchase",
         "rx:Virginia Tech - Go Hokies", "$35.00", None, "2026-09-29"),
    ], "txn_added")
    check_rows_changed(judge, initial, after, "vehicles", [
        (2, None, None, None, None, None, None, None, None, None, None, None, None, None, None, "virginia-tech-go-hokies"),
    ], "plate_assigned")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
