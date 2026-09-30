#!/usr/bin/env python3
"""Deterministic verifier for Zara--5 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_5.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--5"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_search", r"/us/en/search\?[^ ]*searchTerm=TRENCH")
    check_visited_path(judge, traj, "nav_first_pdp", r"plaid-trench-coat-with-belt-p08073247\.html")
    check_visited_path(judge, traj, "nav_logon", r"/us/en/logon")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_checkout", r"/us/en/shop/checkout")
    check_visited_path(judge, traj, "nav_confirm", r"/us/en/shop/confirm/80030000005")
    check_visited_path(judge, traj, "nav_orders", r"/us/en/account/orders")

    check_answer_number(judge, answer, "upstream_total", 49)
    check_answer_phrase(judge, answer, "top_color", "Beige")
    check_answer_money(judge, answer, "range_min", 49.90)
    check_answer_money(judge, answer, "range_max", 199.00)
    check_answer_phrase(judge, answer, "first_name", "PLAID BELTED TRENCH COAT")
    check_answer_money(judge, answer, "first_price", 129.00)
    check_answer_phrase(judge, answer, "first_color", "Brown-Blue")
    check_answer_money(judge, answer, "bag_subtotal", 174.90)
    check_answer_money(judge, answer, "bag_total", 179.85)
    check_answer_money(judge, answer, "doubled_subtotal", 220.80)
    check_answer_regex(judge, answer, "order_number", r"80030000005")
    check_answer_money(judge, answer, "order_total", 225.75)
    check_answer_regex(judge, answer, "card_last4", r"1111")
    check_answer_phrase(judge, answer, "address", "1104 Wilshire Blvd")
    check_answer_regex(judge, answer, "order_status", r"[Pp]laced")

    check_only_tables_changed(judge, initial, after, {"cart_items", "orders", "order_items"})
    check_rows_removed(judge, initial, after, "cart_items",
                       [[3, 3, None, 549296705, 133, 673, 1, "2026-09-28"]], "plaid_row_removed")
    check_rows_added(judge, initial, after, "orders",
                     [[5, 3, "80030000005", "placed", "2026-09-29", 495, 22080, 22575, "1111", None]],
                     "order_row")
    check_rows_added(judge, initial, after, "cart_items", [], "no_cart_rows_added")
    check_rows_added(judge, initial, after, "order_items",
                     [[7, 5, 549296705, "Ecru / Blue", "8-9 years (51,6 INCHES)", "PLAID A-LINE DRESS", 4590, 2],
                      [8, 5, 559622788, "Brown-Blue", "S", "PLAID BELTED TRENCH COAT", 12900, 1]],
                     "order_item_rows")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
