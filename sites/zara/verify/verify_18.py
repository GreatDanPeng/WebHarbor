#!/usr/bin/env python3
"""Deterministic verifier for Zara--18 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_18.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--18"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_perfumes", r"/us/en/beauty-perfumes-l1415\.html")
    check_visited_path(judge, traj, "nav_price", r"beauty-perfumes-l1415\.html\?[^ ]*price-max=3590")
    check_visited_path(judge, traj, "nav_radiance", r"zara-illusion-radiance-eau-de-parfum-80-ml--2-71-fl-oz--p20110961\.html")
    check_visited_path(judge, traj, "nav_serenity", r"zaraillusion-serenity-edp-80-ml--2-71-fl-oz--p20110955\.html")
    check_visited_path(judge, traj, "nav_makeup", r"/us/en/beauty-makeup-l4414\.html")
    check_visited_path(judge, traj, "nav_gloss", r"pink-rush-lip-gloss-pink-infinity-p24890306\.html")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_search", r"/us/en/search\?[^ ]*searchTerm=ILLUSION")

    check_answer_number(judge, answer, "perfumes_upstream", 176)
    check_answer_number(judge, answer, "perfumes_snapshot", 10)
    check_answer_count_at_least(judge, answer, "two_left", ["COCOA SUNSET EDP 100ML", "COCOA BLISS EDP 100 ML"], 2)
    check_answer_money(judge, answer, "shared_price", 35.90)
    check_answer_money(judge, answer, "radiance_price", 39.90)
    check_answer_number(judge, answer, "radiance_sku", 556189101)
    check_answer_number(judge, answer, "serenity_sku", 545449880)
    check_answer_money(judge, answer, "serenity_price", 39.90)
    check_answer_number(judge, answer, "makeup_upstream", 30)
    check_answer_money(judge, answer, "gloss_price", 22.90)
    check_answer_phrase(judge, answer, "gloss_color", "PINK INFINITY")
    check_answer_number(judge, answer, "illusion_matches", 2)
    check_answer_money(judge, answer, "final_subtotal", 119.70)
    check_answer_money(judge, answer, "final_total", 124.65)

    check_only_tables_changed(judge, initial, after, {"cart_items"})
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, None, "rx:^[0-9a-f]{32}$", 556189100, 166, 845, 2, "2026-09-29"],
                      [None, None, "rx:^[0-9a-f]{32}$", 545449879, 165, 844, 1, "2026-09-29"]],
                     "t18_guest_rows")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
