#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--10 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_10.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--10"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # alice.j: no-payment renewal previews + full fee-surface audit
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_renew", r"/account/vehicles/1/renew")
    check_visited_path(judge, traj, "nav_preview_1yr", r"/account/vehicles/1/renew\?years=1")
    check_visited_path(judge, traj, "nav_preview_2yr", r"/account/vehicles/1/renew\?years=2")
    check_visited_path(judge, traj, "nav_preview_3yr", r"/account/vehicles/1/renew\?years=3")
    check_visited_path(judge, traj, "nav_license_renew", r"/account/license/renew")
    check_visited_path(judge, traj, "nav_license_preview", r"/account/license/renew\?years=8")
    check_visited_path(judge, traj, "nav_fees", r"/vehicles/taxes-fees")
    check_visited_path(judge, traj, "nav_registration", r"/vehicles/registration")
    check_answer_money(judge, answer, "one_year_total", 29.75)
    check_answer_money(judge, answer, "two_year_total", 56.50)
    check_answer_money(judge, answer, "three_year_total", 85.25)
    check_answer_money(judge, answer, "license_preview_total", 32.00)
    check_answer_money(judge, answer, "per_year_cost", 4.00)
    check_answer_money(judge, answer, "passenger_4000", 30.75)
    check_answer_money(judge, answer, "motorcycle", 24.75)
    check_answer_money(judge, answer, "pickup_6501", 44.75)
    check_answer_money(judge, answer, "emissions_extra", 2.00)
    check_answer_money(judge, answer, "late_fee", 10.00)
    check_answer_money(judge, answer, "replacement_title", 15.00)
    check_answer_any(judge, answer, "sales_tax", ["4.15%", "4.15 percent"])
    check_answer_money(judge, answer, "sales_tax_minimum", 75.00)
    check_answer_count_at_least(judge, answer, "multiyear_discounts", ["$3", "$4"], 2)
    check_answer_phrase(judge, answer, "fee_chart_form", "DMV 201")
    check_answer_phrase(judge, answer, "fee_chart_edition", "08/10/2026")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
