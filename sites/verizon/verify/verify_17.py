#!/usr/bin/env python3
"""Deterministic verifier for Verizon--17 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_17.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_number_absent, check_answer_ordered, check_answer_phrase,
    check_answer_regex, check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, db_one, final_answer, run_verifier,
)

TASK_ID = "Verizon--17"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_login", r"/account/login")
    check_visited_path(judge, traj, "nav_orders", r"/account/orders/$")
    check_visited_path(judge, traj, "nav_order_detail", r"/account/orders/VZW200038/")
    check_visited_path(judge, traj, "nav_bills", r"/account/bills/$")
    check_visited_path(judge, traj, "nav_usage", r"/account/usage/")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")
    check_visited_path(judge, traj, "nav_account", r"/account/$")

    # answer ground truth
    check_answer_phrase(judge, answer, "order_number", "VZW200038")
    check_answer_phrase(judge, answer, "order_device", "Galaxy A17 5G")
    check_answer_phrase(judge, answer, "order_color", "Navy Blue")
    check_answer_phrase(judge, answer, "order_storage", "128 GB")
    check_answer_phrase(judge, answer, "order_status", "In transit")
    check_answer_phrase(judge, answer, "order_delivery", "Arriving by Thu, Oct 1")
    check_answer_phrase(judge, answer, "order_placed", "2026-09-25")
    check_answer_money(judge, answer, "order_monthly", 36.94)
    check_answer_money(judge, answer, "aug_total", 118.17)
    check_answer_regex(judge, answer, "aug_paid", r"Aug[^;]{0,60}paid|paid[^;]{0,60}Aug")
    check_answer_money(judge, answer, "sep_total", 118.17)
    check_answer_phrase(judge, answer, "sep_status", "due")
    check_answer_money(judge, answer, "bob_data", 18.90)
    check_answer_money(judge, answer, "bob_hotspot", 2.40)
    check_answer_money(judge, answer, "bob_hotspot_cap", 10.00)
    check_answer_money(judge, answer, "p11p_mint", 540.00)
    check_answer_money(judge, answer, "p11p_cracked", 140.00)
    check_answer_phrase(judge, answer, "account_number", "5306-7788")
    check_answer_phrase(judge, answer, "account_kind", "postpaid")

    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
