#!/usr/bin/env python3
"""Deterministic verifier for Zara--13 (zara).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-zara-review, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_13.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--13"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)

    # navigation: register, WOMAN DRESSES, the dress PDP (XS), bag, checkout, confirm
    check_visited_path(judge, traj, "nav_register", r"/us/en/logon\?[^ ]*mode=register")
    check_visited_path(judge, traj, "nav_dresses", r"/us/en/woman-dresses-l1066\.html")
    check_visited_path(judge, traj, "nav_pdp", r"midi-scarf-dress-p08100038\.html")
    check_visited_path(judge, traj, "nav_checkout", r"/us/en/shop/checkout")
    check_visited_path(judge, traj, "nav_confirm", r"/us/en/shop/confirm/80050000005")
    # answer ground truth
    check_answer_regex(judge, answer, "order_number", r"80050000005")
    check_answer_money(judge, answer, "total", 233.95)
    check_answer_phrase(judge, answer, "line_name", "MIDI SCARF DRESS")
    check_answer_any(judge, answer, "line_color", ["Ecru"])
    check_answer_phrase(judge, answer, "line_size", "XS")
    # after-state: +1 user (registered), +1 order, +1 order item; bag consumed
    check_only_tables_changed(judge, initial, after, {"users", "orders", "order_items"})
    check_rows_added(judge, initial, after, "users",
                     [[5, "rx:.+@.+[.].+", "rx:[A-Za-z ]+", "rx:^[$]2b[$]12[$][./A-Za-z0-9]{53}$", 0, "2026-09-29"]],
                     "registered_user")
    check_rows_added(judge, initial, after, "orders",
                     [[5, 5, "80050000005", "placed", "2026-09-29", 495, 22900, 23395, "9999", None]],
                     "order_row")
    check_rows_added(judge, initial, after, "order_items",
                     [[None, 5, 578162617, "Ecru", "XS", "MIDI SCARF DRESS", 22900, 1]],
                     "order_item_row")



if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
