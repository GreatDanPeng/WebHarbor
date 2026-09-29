#!/usr/bin/env python3
"""Deterministic verifier for Zara--3 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_3.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--3"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_girl", r"/us/en/kids-girl-dresses-jumpsuits-l360\.html")
    check_visited_path(judge, traj, "nav_plaid", r"plaid-a-line-dress-p06096811\.html")
    check_visited_path(judge, traj, "nav_burgundy", r"kids-girl-dresses-jumpsuits-l360\.html\?[^ ]*color=Burgundy")
    check_visited_path(judge, traj, "nav_ruffled", r"ruffled-romantic-dress-p05598702\.html")
    check_visited_path(judge, traj, "nav_boy", r"/us/en/kids-boy-coats-jackets-l231\.html")
    check_visited_path(judge, traj, "nav_sort", r"kids-boy-coats-jackets-l231\.html\?[^ ]*sort=price-asc")
    check_visited_path(judge, traj, "nav_jacket", r"ultralight-water-repellent-jacket-p03918761\.html")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_search", r"/us/en/search\?[^ ]*searchTerm=PINAFORE")

    check_answer_number(judge, answer, "girl_upstream", 46)
    check_answer_number(judge, answer, "girl_snapshot", 10)
    check_answer_money(judge, answer, "plaid_price", 45.90)
    check_answer_phrase(judge, answer, "plaid_ref", "6096/811")
    check_answer_money(judge, answer, "plaid_total", 50.85)
    check_answer_phrase(judge, answer, "burgundy_left", "RUFFLED ROMANTIC DRESS")
    check_answer_money(judge, answer, "burgundy_price", 49.90)
    check_answer_regex(judge, answer, "ruffled_avail", r"COMING SOON")
    check_answer_number(judge, answer, "boy_upstream", 55)
    check_answer_phrase(judge, answer, "boy_cheapest", "ULTRALIGHT WATER REPELLENT JACKET")
    check_answer_money(judge, answer, "final_subtotal", 79.80)
    check_answer_money(judge, answer, "final_total", 84.75)
    check_answer_count_at_least(judge, answer, "pinafore", ["PLEATED PINAFORE DRESS", "TWILL POCKET PINAFORE"], 2)

    check_only_tables_changed(judge, initial, after, {"cart_items"})
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, None, "rx:^[0-9a-f]{32}$", 545484369, 154, 801, 2, "2026-09-29"]],
                     "t3_guest_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
