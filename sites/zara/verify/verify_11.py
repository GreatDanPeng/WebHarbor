#!/usr/bin/env python3
"""Deterministic verifier for Zara--11 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_11.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--11"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_logon", r"/us/en/logon")
    check_visited_path(judge, traj, "nav_orders", r"/us/en/account/orders")
    check_visited_path(judge, traj, "nav_delivered", r"/us/en/account/orders/8004128041")
    check_visited_path(judge, traj, "nav_shipped", r"/us/en/account/orders/8004193147")
    check_visited_path(judge, traj, "nav_account", r"/us/en/account")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_wishlist", r"/us/en/wishlist")
    check_visited_path(judge, traj, "nav_addresses", r"/us/en/account/addresses")
    check_visited_path(judge, traj, "nav_newsletter", r"/newsletter")

    check_answer_regex(judge, answer, "order_shipped", r"8004193147")
    check_answer_regex(judge, answer, "order_delivered", r"8004128041")
    check_answer_money(judge, answer, "shipped_total", 223.95)
    check_answer_money(judge, answer, "delivered_total", 538.90)
    check_answer_regex(judge, answer, "card_ending", r"4417")
    check_answer_phrase(judge, answer, "member_since", "2026-08-02")
    check_answer_number(judge, answer, "orders_count", 2)
    check_answer_number(judge, answer, "wishlist_count", 3)
    check_answer_number(judge, answer, "addresses_count", 2)
    check_answer_money(judge, answer, "doubled_subtotal", 816.00)
    check_answer_money(judge, answer, "doubled_total", 820.95)
    check_answer_phrase(judge, answer, "addr_labels", "WORK")
    check_answer_regex(judge, answer, "newsletter", r"alice-news@zara\.example")

    check_only_tables_changed(judge, initial, after, {"cart_items", "newsletter_signups"})
    check_rows_changed(judge, initial, after, "cart_items",
                       [[1, 1, None, 578162617, 1, 1, 2, "2026-09-27"]], "scarf_doubled")
    check_rows_added(judge, initial, after, "cart_items", [], "no_cart_rows_added")
    check_rows_added(judge, initial, after, "newsletter_signups",
                     [[1, "alice-news@zara.example", "WOMAN", "2026-09-29"]], "newsletter_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
