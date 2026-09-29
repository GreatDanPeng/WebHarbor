#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--2 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_2.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--2"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # dana.k: Bolt EV previews + the highway-use rule + emissions + records page
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_renew", r"/account/vehicles/5/renew")
    check_visited_path(judge, traj, "nav_preview_1yr", r"/account/vehicles/5/renew\?years=1")
    check_visited_path(judge, traj, "nav_preview_2yr", r"/account/vehicles/5/renew\?years=2")
    check_visited_path(judge, traj, "nav_preview_3yr", r"/account/vehicles/5/renew\?years=3")
    check_visited_path(judge, traj, "nav_highway_use", r"/vehicles/taxes-fees/highway-use")
    check_visited_path(judge, traj, "nav_fees", r"/vehicles/taxes-fees")
    check_visited_path(judge, traj, "nav_registration", r"/vehicles/registration")
    check_visited_path(judge, traj, "nav_emissions", r"/vehicles/registration/emissions")
    check_visited_path(judge, traj, "nav_records_order", r"/account/records")
    check_answer_phrase(judge, answer, "id_number", "ID9912345")
    check_answer_phrase(judge, answer, "id_expiration", "2026-05-09")
    check_answer_money(judge, answer, "one_year_total", 165.38)
    check_answer_money(judge, answer, "registration_line", 30.75)
    check_answer_money(judge, answer, "ev_huf_line", 135.63)
    check_answer_money(judge, answer, "internet_discount", 1.00)
    check_answer_money(judge, answer, "two_year_total", 327.76)
    check_answer_money(judge, answer, "three_year_total", 492.14)
    check_answer_any(judge, answer, "huf_threshold",
                     ["25 mpg or greater", "25 miles per gallon (mpg) or greater",
                      "fuel economy of 25 miles per gallon"])
    check_answer_count_at_least(judge, answer, "huf_exempt", ["motorcycles", "mopeds"], 2)
    check_answer_count_at_least(judge, answer, "huf_calc_basis",
                                ["mpg rating", "fuel tax rate", "average miles"], 2)
    check_answer_count_at_least(judge, answer, "multiyear_discounts",
                                ["$3", "$4"], 2)
    check_answer_count_at_least(judge, answer, "emissions_localities",
                                ["arlington", "fairfax", "loudoun", "prince william",
                                 "stafford", "manassas"], 4)
    check_answer_any(judge, answer, "inspection_validity", ["two years", "2 years"])
    check_answer_phrase(judge, answer, "bolt_title", "T5533-2248")
    check_answer_phrase(judge, answer, "bolt_vin", "1G1FY6S00L4180927")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
