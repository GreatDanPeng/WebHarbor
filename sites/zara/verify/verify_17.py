#!/usr/bin/env python3
"""Deterministic verifier for Zara--17 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_17.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--17"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_shirts", r"/us/en/man-shirts-l737\.html")
    check_visited_path(judge, traj, "nav_black", r"man-shirts-l737\.html\?[^ ]*color=Black")
    check_visited_path(judge, traj, "nav_pdp", r"slim-fit-shirt-p04408147\.html")
    check_visited_path(judge, traj, "nav_white", r"slim-fit-shirt-p04408147\.html\?[^ ]*v1=250")
    check_visited_path(judge, traj, "nav_sand", r"slim-fit-shirt-p04408147\.html\?[^ ]*v1=711")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_jeans", r"/us/en/man-jeans-l659\.html")
    check_visited_path(judge, traj, "nav_size38", r"man-jeans-l659\.html\?[^ ]*size=38")
    check_visited_path(judge, traj, "nav_loose", r"loose-fit-jeans-p00774307\.html")
    check_visited_path(judge, traj, "nav_faded", r"loose-fit-jeans-p00774307\.html\?[^ ]*v1=833")

    check_answer_number(judge, answer, "shirts_upstream", 331)
    check_answer_number(judge, answer, "shirts_snapshot", 10)
    check_answer_phrase(judge, answer, "black_product", "SLIM FIT SHIRT")
    check_answer_money(judge, answer, "black_price", 59.90)
    check_answer_count_at_least(judge, answer, "five_colors", ["White", "Sand", "Light sky blue", "Black", "Dark brown"], 5)
    check_answer_phrase(judge, answer, "shirt_ref", "4408/147")
    check_answer_number(judge, answer, "jeans_upstream", 115)
    check_answer_count_at_least(judge, answer, "f38", ["BASIC SLIM FIT JEANS", "STRAIGHT-FIT JEANS"], 2)
    check_answer_money(judge, answer, "loose_price", 69.90)
    check_answer_number(judge, answer, "loose_colors", 8)
    check_answer_money(judge, answer, "final_subtotal", 139.80)
    check_answer_money(judge, answer, "final_total", 144.75)

    check_only_tables_changed(judge, initial, after, {"cart_items"})
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, None, "rx:^[0-9a-f]{32}$", 556140702, 97, 435, 2, "2026-09-29"]],
                     "t17_guest_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
