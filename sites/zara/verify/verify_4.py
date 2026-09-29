#!/usr/bin/env python3
"""Deterministic verifier for Zara--4 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_4.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--4"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_search", r"/us/en/search\?[^ ]*searchTerm=JEANS")
    check_visited_path(judge, traj, "nav_first_pdp", r"basic-slim-fit-jeans-p00774333\.html")
    check_visited_path(judge, traj, "nav_charcoal", r"basic-slim-fit-jeans-p00774333\.html\?[^ ]*v1=822")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_man_jeans", r"/us/en/man-jeans-l659\.html")
    check_visited_path(judge, traj, "nav_size38", r"man-jeans-l659\.html\?[^ ]*size=38")
    check_visited_path(judge, traj, "nav_sort_desc", r"man-jeans-l659\.html\?[^ ]*sort=price-desc")
    check_visited_path(judge, traj, "nav_sort_asc", r"man-jeans-l659\.html\?[^ ]*sort=price-asc")
    check_visited_path(judge, traj, "nav_price", r"man-jeans-l659\.html\?[^ ]*price-max=5000")

    check_answer_number(judge, answer, "upstream_total", 543)
    check_answer_number(judge, answer, "blue_facet", 320)
    check_answer_number(judge, answer, "white_facet", 39)
    check_answer_money(judge, answer, "price_min", 25.90)
    check_answer_money(judge, answer, "price_max", 349.00)
    check_answer_ordered(judge, answer, "first_three", ["BASIC SLIM FIT JEANS", "PRINTED LOOSE FIT JEANS", "LIGHTWEIGHT REGULAR FIT JEANS"])
    check_answer_money(judge, answer, "first_price", 49.90)
    check_answer_phrase(judge, answer, "first_ref", "0774/333")
    check_answer_number(judge, answer, "color_count", 6)
    check_answer_number(judge, answer, "size_count", 7)
    check_answer_regex(judge, answer, "size34", r"34 \(US 34\) IN STOCK")
    check_answer_money(judge, answer, "subtotal1", 49.90)
    check_answer_money(judge, answer, "total_doubled", 104.75)
    check_answer_phrase(judge, answer, "empty_bag", "Your bag is empty")
    check_answer_number(judge, answer, "man_jeans_upstream", 115)
    check_answer_count_at_least(judge, answer, "f38", ["BASIC SLIM FIT JEANS", "STRAIGHT-FIT JEANS"], 2)
    check_answer_phrase(judge, answer, "most_expensive", "PRINTED LOOSE FIT JEANS")
    check_answer_phrase(judge, answer, "cheapest", "LIGHTWEIGHT REGULAR FIT JEANS")
    check_answer_count_at_least(judge, answer, "under50", ["LIGHTWEIGHT REGULAR FIT JEANS", "BASIC SLIM FIT JEANS"], 2)

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
