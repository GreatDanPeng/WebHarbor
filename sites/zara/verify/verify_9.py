#!/usr/bin/env python3
"""Deterministic verifier for Zara--9 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_9.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--9"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_logon", r"/us/en/logon")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_bags", r"/us/en/woman-bags-l1024\.html")
    check_visited_path(judge, traj, "nav_pdp", r"elongated-shoulder-bag-p16821710\.html")
    check_visited_path(judge, traj, "nav_red", r"elongated-shoulder-bag-p16821710\.html\?[^ ]*v1=600")
    check_visited_path(judge, traj, "nav_orders", r"/us/en/account/orders")
    check_visited_path(judge, traj, "nav_delivered", r"/us/en/account/orders/8004128041")
    check_visited_path(judge, traj, "nav_wishlist", r"/us/en/wishlist")

    check_answer_money(judge, answer, "subtotal_start", 587.00)
    check_answer_money(judge, answer, "total_start", 591.95)
    check_answer_money(judge, answer, "subtotal_boots1", 408.00)
    check_answer_money(judge, answer, "total_boots1", 412.95)
    check_answer_money(judge, answer, "subtotal_final", 278.80)
    check_answer_money(judge, answer, "total_final", 283.75)
    check_answer_regex(judge, answer, "orders_list", r"8004193147")
    check_answer_regex(judge, answer, "delivered_order", r"8004128041")
    check_answer_count_at_least(judge, answer, "delivered_lines",
                                ["SHOULDER PAD ZIP JACKET", "100% LEATHER PUFFED-BODY DRESS"], 2)
    check_answer_money(judge, answer, "delivered_unit_jacket", 79.90)
    check_answer_money(judge, answer, "delivered_unit_dress", 459.00)
    check_answer_count_at_least(judge, answer, "wishlist3", ["DRAPED SEQUIN MIDI DRESS", "100% CASHMERE CROPPED FIT CARDIGAN", "ELONGATED SHOULDER BAG"], 3)

    check_only_tables_changed(judge, initial, after, {"cart_items"})
    check_rows_added(judge, initial, after, "cart_items",
                     [[7, 1, None, 545399254, 49, 225, 2, "2026-09-29"]], "red_row_added")
    check_rows_removed(judge, initial, after, "cart_items",
                       [[1, 1, None, 578162617, 1, 1, 1, "2026-09-27"]], "scarf_row_removed")
    check_rows_changed(judge, initial, after, "cart_items",
                       [[2, 1, None, 545480431, 38, 157, 1, "2026-09-28"]], "boots_qty_1")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
