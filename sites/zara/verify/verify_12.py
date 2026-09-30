#!/usr/bin/env python3
"""Deterministic verifier for Zara--12 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_12.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--12"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_logon", r"/us/en/logon")
    check_visited_path(judge, traj, "nav_wishlist", r"/us/en/wishlist")
    check_visited_path(judge, traj, "nav_dresses", r"/us/en/woman-dresses-l1066\.html")
    check_visited_path(judge, traj, "nav_scarf_pdp", r"midi-scarf-dress-p08100038\.html")
    check_visited_path(judge, traj, "nav_chiffon_pdp", r"chiffon-halter-midi-dress-with-tie-p07521308\.html")

    check_answer_count_at_least(judge, answer, "wishlist3", ["DRAPED SEQUIN MIDI DRESS", "100% CASHMERE CROPPED FIT CARDIGAN", "ELONGATED SHOULDER BAG"], 3)
    check_answer_count_at_least(judge, answer, "wishlist5", ["DRAPED SEQUIN MIDI DRESS", "100% CASHMERE CROPPED FIT CARDIGAN", "ELONGATED SHOULDER BAG", "MIDI SCARF DRESS", "CHIFFON HALTER MIDI DRESS WITH TIE"], 5)
    check_answer_ordered(judge, answer, "final4", ["DRAPED SEQUIN MIDI DRESS", "100% CASHMERE CROPPED FIT CARDIGAN", "ELONGATED SHOULDER BAG", "CHIFFON HALTER MIDI DRESS WITH TIE"])
    check_answer_phrase(judge, answer, "highest", "100% CASHMERE CROPPED FIT CARDIGAN")
    check_answer_money(judge, answer, "highest_price", 319.00)
    check_answer_regex(judge, answer, "button_label", r"REMOVE FROM WISHLIST")
    check_answer_phrase(judge, answer, "chiffon_color", "Black")

    check_only_tables_changed(judge, initial, after, {"wishlist_items"})
    check_rows_added(judge, initial, after, "wishlist_items",
                     [[8, 1, 545406123, 7, "2026-09-29"]], "chiffon_wish_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
