#!/usr/bin/env python3
"""Deterministic verifier for Zara--21 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_21.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--21"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_logon", r"/us/en/logon")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_orders", r"/us/en/account/orders")
    check_visited_path(judge, traj, "nav_order_detail", r"/us/en/account/orders/8004384012")
    check_visited_path(judge, traj, "nav_account", r"/us/en/account")
    check_visited_path(judge, traj, "nav_addresses", r"/us/en/account/addresses")
    check_visited_path(judge, traj, "nav_wishlist", r"/us/en/wishlist")
    check_visited_path(judge, traj, "nav_newsletter", r"/newsletter")

    check_answer_money(judge, answer, "start_subtotal", 258.80)
    check_answer_money(judge, answer, "start_total", 263.75)
    check_answer_money(judge, answer, "perfume2_subtotal", 298.70)
    check_answer_money(judge, answer, "bag3_subtotal", 398.50)
    check_answer_money(judge, answer, "final_subtotal", 229.50)
    check_answer_money(judge, answer, "final_total", 234.45)
    check_answer_regex(judge, answer, "order_number", r"8004384012")
    check_answer_regex(judge, answer, "order_status", r"[Rr]eturned")
    check_answer_money(judge, answer, "order_total", 339.00)
    check_answer_regex(judge, answer, "order_card", r"5296")
    check_answer_phrase(judge, answer, "member_since", "2026-09-03")
    check_answer_phrase(judge, answer, "wishlist_empty", "empty")
    check_answer_regex(judge, answer, "newsletter", r"dana-news@zara\.example")

    check_only_tables_changed(judge, initial, after, {"cart_items", "newsletter_signups"})
    check_rows_removed(judge, initial, after, "cart_items",
                       [[6, 4, None, 570988059, 21, 93, 1, "2026-09-29"]], "polo_removed")
    check_rows_changed(judge, initial, after, "cart_items",
                       [[4, 4, None, 556189100, 166, 845, 2, "2026-09-28"],
                        [5, 4, None, 545399254, 48, 224, 3, "2026-09-28"]], "qty_updates")
    check_rows_added(judge, initial, after, "cart_items", [], "no_cart_rows_added")
    check_rows_added(judge, initial, after, "newsletter_signups",
                     [[1, "dana-news@zara.example", "WOMAN", "2026-09-29"]], "newsletter_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
