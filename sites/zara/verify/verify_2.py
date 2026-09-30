#!/usr/bin/env python3
"""Deterministic verifier for Zara--2 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_2.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--2"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_bags", r"/us/en/woman-bags-l1024\.html")
    check_visited_path(judge, traj, "nav_price_filter", r"woman-bags-l1024\.html\?[^ ]*price-max=6000")
    check_visited_path(judge, traj, "nav_pdp", r"elongated-shoulder-bag-p16821710\.html")
    check_visited_path(judge, traj, "nav_red", r"elongated-shoulder-bag-p16821710\.html\?[^ ]*v1=600")
    check_visited_path(judge, traj, "nav_oval", r"oval-shoulder-bag-p16214810\.html")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")

    check_answer_number(judge, answer, "upstream_count", 178)
    check_answer_number(judge, answer, "snapshot_count", 10)
    check_answer_count_at_least(judge, answer, "under60", ["ELONGATED SHOULDER BAG", "METALLIC APPLIQU", "OVAL SHOULDER BAG", "FRINGE SHOULDER BAG", "FRINGED SHOULDER BAG"], 4)
    check_answer_money(judge, answer, "elongated_price", 49.90)
    check_answer_ordered(judge, answer, "three_colors", ["Two-tone", "Red", "Black"])
    check_answer_number(judge, answer, "red_sku", 545399255)
    check_answer_number(judge, answer, "black_sku", 545399257)
    check_answer_money(judge, answer, "red_subtotal", 49.90)
    check_answer_money(judge, answer, "red_total", 54.85)
    check_answer_money(judge, answer, "oval_price", 59.90)
    check_answer_phrase(judge, answer, "oval_ref", "6214/810")
    check_answer_money(judge, answer, "final_subtotal", 99.80)
    check_answer_money(judge, answer, "final_total", 104.75)

    check_only_tables_changed(judge, initial, after, {"cart_items"})
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, None, "rx:^[0-9a-f]{32}$", 545399254, 49, 225, 2, "2026-09-29"]],
                     "t2_guest_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
