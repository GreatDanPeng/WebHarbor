#!/usr/bin/env python3
"""Deterministic verifier for Zara--15 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_15.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--15"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_bags", r"/us/en/woman-bags-l1024\.html")
    check_visited_path(judge, traj, "nav_pdp", r"elongated-shoulder-bag-p16821710\.html")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_logon", r"/us/en/logon")
    check_visited_path(judge, traj, "nav_wishlist", r"/us/en/wishlist")
    check_visited_path(judge, traj, "nav_account", r"/us/en/account")
    check_visited_path(judge, traj, "nav_newsletter", r"/newsletter")

    check_answer_money(judge, answer, "guest_subtotal", 49.90)
    check_answer_money(judge, answer, "guest_total", 54.85)
    check_answer_money(judge, answer, "doubled_subtotal", 99.80)
    check_answer_money(judge, answer, "doubled_total", 104.75)
    check_answer_phrase(judge, answer, "empty_bag", "Your bag is empty")
    check_answer_money(judge, answer, "carol_subtotal", 45.90)
    check_answer_money(judge, answer, "carol_total", 50.85)
    check_answer_money(judge, answer, "carol_doubled_subtotal", 91.80)
    check_answer_money(judge, answer, "carol_doubled_total", 96.75)
    check_answer_count_at_least(judge, answer, "carol_wishlist", ["RUFFLED ROMANTIC DRESS", "CORDUROY LONG OVERALLS"], 2)
    check_answer_number(judge, answer, "carol_orders", 0)
    check_answer_number(judge, answer, "carol_addresses", 1)
    check_answer_regex(judge, answer, "newsletter", r"carol-news@zara\.example")

    check_only_tables_changed(judge, initial, after, {"cart_items", "newsletter_signups"})
    check_rows_changed(judge, initial, after, "cart_items",
                       [[3, 3, None, 549296705, 133, 673, 2, "2026-09-28"]], "carol_plaid_doubled")
    check_rows_added(judge, initial, after, "cart_items", [], "no_cart_rows_added")
    check_rows_added(judge, initial, after, "newsletter_signups",
                     [[1, "carol-news@zara.example", "WOMAN", "2026-09-29"]], "newsletter_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
