#!/usr/bin/env python3
"""Deterministic verifier for Zara--10 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_10.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--10"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_logon", r"/us/en/logon")
    check_visited_path(judge, traj, "nav_bags", r"/us/en/woman-bags-l1024\.html")
    check_visited_path(judge, traj, "nav_pdp", r"elongated-shoulder-bag-p16821710\.html")
    check_visited_path(judge, traj, "nav_red", r"elongated-shoulder-bag-p16821710\.html\?[^ ]*v1=600")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_checkout", r"/us/en/shop/checkout")
    check_visited_path(judge, traj, "nav_confirm", r"/us/en/shop/confirm/80010000005")
    check_visited_path(judge, traj, "nav_orders", r"/us/en/account/orders")
    check_visited_path(judge, traj, "nav_new_order", r"/us/en/account/orders/80010000005")

    check_answer_money(judge, answer, "bag_subtotal", 636.80)
    check_answer_money(judge, answer, "bag_total", 641.75)
    check_answer_regex(judge, answer, "order_number", r"80010000005")
    check_answer_money(judge, answer, "order_total", 641.75)
    check_answer_regex(judge, answer, "card_last4", r"4242")
    check_answer_phrase(judge, answer, "address", "425 W 14th St")
    check_answer_number(judge, answer, "orders_now", 3)
    check_answer_count_at_least(judge, answer, "order_lines", ["MIDI SCARF DRESS", "LEATHER WIDE HEEL BOOTS", "ELONGATED SHOULDER BAG"], 3)

    check_only_tables_changed(judge, initial, after, {"cart_items", "orders", "order_items"})
    check_rows_removed(judge, initial, after, "cart_items",
                       [[1, 1, None, 578162617, 1, 1, 1, "2026-09-27"],
                        [2, 1, None, 545480431, 38, 157, 2, "2026-09-28"]], "bag_cleared")
    check_rows_added(judge, initial, after, "orders",
                     [[5, 1, "80010000005", "placed", "2026-09-29", 495, 63690, 64185, "4242", None]],
                     "order_row")
    check_rows_added(judge, initial, after, "cart_items", [], "no_cart_rows_added")
    check_rows_added(judge, initial, after, "order_items",
                     [[7, 5, 578162617, "Ecru", "XS", "MIDI SCARF DRESS", 22900, 1],
                      [8, 5, 545480431, "Black", "7½", "LEATHER WIDE HEEL BOOTS", 17900, 2],
                      [9, 5, 545399254, "Red", "ONE SIZE ONLY", "ELONGATED SHOULDER BAG", 4990, 1]],
                     "order_item_rows")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
