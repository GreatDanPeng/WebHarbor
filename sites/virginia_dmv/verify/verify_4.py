#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--4 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_4.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--4"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # alice.j: 173rd Airborne plate facts + AIRBRN/HOOAH availability checks
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_plate_search", r"/vehicles/license-plates/search")
    check_visited_path(judge, traj, "nav_plate_detail", r"/vehicles/license-plates/search/173rd-airborne")
    check_visited_path(judge, traj, "nav_purchase", r"/account/plates/173rd-airborne/purchase")
    check_answer_money(judge, answer, "plate_fee", 10.00)
    check_answer_any(judge, answer, "fee_period", ["annually"])
    check_answer_number(judge, answer, "char_combinations", 6)
    check_answer_any(judge, answer, "requirements", ["dd214", "letter from commanding officer"])
    check_answer_any(judge, answer, "disabled_symbol", ["disabled symbol: no", "disabled symbol no", "disabled symbol available: no", "no disabled symbol", "disabled symbol not available"])
    # AIRBRN (6 characters, within the plate's limit) and HOOAH are the two
    # messages checked in the purchase flow.
    check_answer_any(judge, answer, "airbrn_outcome", ["airbrn is available"])
    check_answer_any(judge, answer, "hooah_outcome",
                    ["hooah is not available", "hooah: not available", "not available — try a different message"])
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
