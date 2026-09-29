#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--18 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the r3 honest Playwright walks on
the fix container wh-vadm-fix3, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r3-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_18.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_ordered,
    check_answer_money_after, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Virginia DMV--18"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # REAL ID page + documents + fee chart + newsroom + REAL ID appointment
    check_visited_path(judge, traj, "nav_licenses", r"/licenses-ids(?!/)")
    check_visited_path(judge, traj, "nav_real_id", r"/licenses-ids/real-id")
    check_visited_path(judge, traj, "nav_fees", r"/vehicles/taxes-fees")
    check_visited_path(judge, traj, "nav_news", r"/news(?!/)")
    check_visited_path(judge, traj, "nav_apple_wallet", r"/news/virginia-issued-drivers-licenses-and-ids-now-available-apple")
    check_visited_path(judge, traj, "nav_news_last_page", r"/news\?pg=7")
    check_visited_path(judge, traj, "nav_wizard", r"/appointments/new")
    check_answer_money(judge, answer, "real_id_fee", 10.00)
    check_answer_any(judge, answer, "minimum_transaction", ["minimum $20", "minimum 20", "$20 minimum", "minimum of $20"])
    check_answer_any(judge, answer, "looks_like", ["star in the upper right corner", "star in the upper-right corner", "gold star"])
    check_answer_any(judge, answer, "steps_to_apply", ["two steps to apply", "two steps", "2 steps"])
    check_answer_any(judge, answer, "boarding_rule", ["board a domestic flight", "domestic flight", "board domestic flights"])
    check_answer_any(judge, answer, "documents_guide", ["dmv 141", "dmv141"])
    check_answer_any(judge, answer, "brochure", ["dmv 299", "dmv299"])
    check_answer_any(judge, answer, "apple_release_date", ["august 26, 2026", "2026-08-26", "aug 26, 2026"])
    check_answer_any(judge, answer, "newest_title", ["new dmv select brings vehicles services to page county"])
    check_answer_any(judge, answer, "oldest_title", ["2024 local heroes series features statewide first responders"])
    check_answer_any(judge, answer, "oldest_date", ["july 29, 2024", "2024-07-29"])
    check_answer_regex(judge, answer, "confirmation_number", r"VADM\d{6}-[A-F0-9]{6}")
    check_answer_regex(judge, answer, "booked_time", r"\d{1,2}:\d{2} AM")
    check_answer_any(judge, answer, "booked_date", ["2026-10-06", "october 6"])
    check_answer_any(judge, answer, "booked_service", ["real id"])
    check_only_tables_changed(judge, initial, after, {"appointments"})
    check_rows_added(judge, initial, after, "appointments", [
        (None, "rx:^VADM\\d{6}-[A-F0-9]{6}$", None, "Jordan Lee", "jordan.lee@example.com",
         "arlington", "REAL ID", "2026-10-06",
         "rx:^\\d{1,2}:\\d{2} AM$", "Confirmed", "2026-09-29"),
    ], "appt_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
