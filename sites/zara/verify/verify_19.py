#!/usr/bin/env python3
"""Deterministic verifier for Zara--19 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_19.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--19"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_dresses", r"/us/en/woman-dresses-l1066\.html")
    check_visited_path(judge, traj, "nav_burgundy", r"woman-dresses-l1066\.html\?[^ ]*color=Burgundy")
    check_visited_path(judge, traj, "nav_sort", r"woman-dresses-l1066\.html\?[^ ]*sort=price-desc")
    check_visited_path(judge, traj, "nav_puffed", r"100-leather-puffed-body-dress-p05479900\.html")
    check_visited_path(judge, traj, "nav_knitwear", r"/us/en/woman-knitwear-l1152\.html")
    check_visited_path(judge, traj, "nav_cardigan", r"100-cashmere-cropped-fit-cardigan-p05755900\.html")
    check_visited_path(judge, traj, "nav_shoes", r"/us/en/woman-shoes-l1251\.html")
    check_visited_path(judge, traj, "nav_boots", r"leather-wide-heel-boots-p11003810\.html")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_search", r"/us/en/search\?[^ ]*searchTerm=PUFFED")

    check_answer_phrase(judge, answer, "burgundy_left", "100% LEATHER PUFFED-BODY DRESS")
    check_answer_money(judge, answer, "burgundy_price", 459.00)
    check_answer_phrase(judge, answer, "pcolor", "Burgundy")
    check_answer_phrase(judge, answer, "pref", "5479/900")
    check_answer_regex(judge, answer, "psizes", r"coming soon")
    check_answer_number(judge, answer, "knitwear_upstream", 406)
    check_answer_money(judge, answer, "card_price", 319.00)
    check_answer_phrase(judge, answer, "card_color", "Turquoise")
    check_answer_phrase(judge, answer, "card_smallest", "XS")
    check_answer_money(judge, answer, "card_doubled_sub", 638.00)
    check_answer_number(judge, answer, "shoes_upstream", 522)
    check_answer_money(judge, answer, "boots_price", 179.00)
    check_answer_number(judge, answer, "boots_sizes", 8)
    check_answer_money(judge, answer, "final_subtotal", 817.00)
    check_answer_money(judge, answer, "final_total", 821.95)
    check_answer_number(judge, answer, "puffed_matches", 1)
    check_answer_phrase(judge, answer, "puffed_name", "100% LEATHER PUFFED-BODY DRESS")

    check_only_tables_changed(judge, initial, after, {"cart_items"})
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, None, "rx:^[0-9a-f]{32}$", 547533764, 22, 98, 2, "2026-09-29"],
                      [None, None, "rx:^[0-9a-f]{32}$", 545480431, 38, 157, 1, "2026-09-29"]],
                     "t19_guest_rows")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
