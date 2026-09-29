#!/usr/bin/env python3
"""Deterministic verifier for Zara--1 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_1.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--1"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_logon", r"/us/en/logon")
    check_visited_path(judge, traj, "nav_dresses", r"/us/en/woman-dresses-l1066\.html")
    check_visited_path(judge, traj, "nav_pdp", r"midi-scarf-dress-p08100038\.html")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_wishlist", r"/us/en/wishlist")

    check_answer_money(judge, answer, "price", 229.00)
    check_answer_phrase(judge, answer, "ref", "8100/038")
    check_answer_phrase(judge, answer, "color", "Ecru")
    check_answer_number(judge, answer, "s_sku", 578162619)
    check_answer_phrase(judge, answer, "badge", "BAISI GUADAGNINO")
    check_answer_regex(judge, answer, "wish_label", r"REMOVE FROM WISHLIST")
    check_answer_money(judge, answer, "totals_qty2_sub", 816.00)
    check_answer_money(judge, answer, "totals_qty2_total", 820.95)
    check_answer_money(judge, answer, "totals_back1_sub", 587.00)
    check_answer_money(judge, answer, "totals_back1_total", 591.95)
    check_answer_money(judge, answer, "remaining_sub", 358.00)
    check_answer_money(judge, answer, "remaining_total", 362.95)
    check_answer_count_at_least(judge, answer, "wishlist4", ["DRAPED SEQUIN MIDI DRESS", "100% CASHMERE CROPPED FIT CARDIGAN", "ELONGATED SHOULDER BAG", "MIDI SCARF DRESS"], 4)
    check_answer_count_at_least(judge, answer, "wishlist_dates", ["2026-09-20", "2026-09-22", "2026-09-25", "2026-09-29"], 4)
    check_answer_ordered(judge, answer, "final3", ["DRAPED SEQUIN MIDI DRESS", "100% CASHMERE CROPPED FIT CARDIGAN", "ELONGATED SHOULDER BAG"])

    check_only_tables_changed(judge, initial, after, {"cart_items"})
    check_rows_removed(judge, initial, after, "cart_items",
                       [[1, 1, None, 578162617, 1, 1, 1, "2026-09-27"]], "scarf_row_removed")
    check_rows_added(judge, initial, after, "cart_items", [], "no_cart_rows_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
