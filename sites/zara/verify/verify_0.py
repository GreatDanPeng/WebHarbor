#!/usr/bin/env python3
"""Deterministic verifier for Zara--0 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_0.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--0"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_dresses", r"/us/en/woman-dresses-l1066\.html")
    check_visited_path(judge, traj, "nav_burgundy", r"woman-dresses-l1066\.html\?[^ ]*color=Burgundy")
    check_visited_path(judge, traj, "nav_black", r"woman-dresses-l1066\.html\?[^ ]*color=Black")
    check_visited_path(judge, traj, "nav_sort_desc", r"woman-dresses-l1066\.html\?[^ ]*sort=price-desc")
    check_visited_path(judge, traj, "nav_sort_asc", r"woman-dresses-l1066\.html\?[^ ]*sort=price-asc")
    check_visited_path(judge, traj, "nav_tie1_pdp", r"z1975-midi-halter-denim-dress-p07957576\.html")
    check_visited_path(judge, traj, "nav_tie2_pdp", r"animal-print-draped-tulle-dress-p07846403\.html")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")

    check_answer_number(judge, answer, "upstream_count", 533)
    check_answer_number(judge, answer, "snapshot_count", 10)
    check_answer_phrase(judge, answer, "burgundy_left", "100% LEATHER PUFFED-BODY DRESS")
    check_answer_money(judge, answer, "burgundy_price", 459.00)
    check_answer_phrase(judge, answer, "black_left", "CHIFFON HALTER MIDI DRESS WITH TIE")
    check_answer_money(judge, answer, "tie_price", 69.90)
    check_answer_ordered(judge, answer, "tie_order", ["Z1975 DENIM MIDI HALTER DRESS", "ANIMAL PRINT DRAPED TULLE DRESS"])
    check_answer_phrase(judge, answer, "first_color", "Brown")
    check_answer_phrase(judge, answer, "first_ref", "7957/576")
    check_answer_money(judge, answer, "subtotal1", 69.90)
    check_answer_money(judge, answer, "shipping", 4.95)
    check_answer_money(judge, answer, "total1", 74.85)
    check_answer_money(judge, answer, "final_subtotal", 139.80)
    check_answer_money(judge, answer, "final_total", 144.75)
    check_answer_regex(judge, answer, "final_qty", r"Z1975 DENIM MIDI HALTER DRESS x2")

    check_only_tables_changed(judge, initial, after, {"cart_items"})
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, None, "rx:^[0-9a-f]{32}$", 565059480, 9, 35, 2, "2026-09-29"]],
                     "t0_guest_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
