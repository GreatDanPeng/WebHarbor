#!/usr/bin/env python3
"""Deterministic verifier for Zara--20 (zara).

Ground truth below is HARDCODED (frozen from the r2 reviewer's two independent
Playwright rounds on the re-review container wh-zara-rereview, seed md5
9aafa4129f038e48bf85fb7ed1fbaa1e) — never read from tasks.jsonl.
Usage: python3 verify_20.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Zara--20"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_jeans", r"/us/en/man-jeans-l659\.html")
    check_visited_path(judge, traj, "nav_black", r"man-jeans-l659\.html\?[^ ]*color=Black")
    check_visited_path(judge, traj, "nav_price", r"man-jeans-l659\.html\?[^ ]*price-max=4000")
    check_visited_path(judge, traj, "nav_pdp", r"lightweight-regular-fit-jeans-p09306301\.html")
    check_visited_path(judge, traj, "nav_ecru", r"lightweight-regular-fit-jeans-p09306301\.html\?[^ ]*v1=712")
    check_visited_path(judge, traj, "nav_charcoal", r"lightweight-regular-fit-jeans-p09306301\.html\?[^ ]*v1=823")
    check_visited_path(judge, traj, "nav_lightblue", r"lightweight-regular-fit-jeans-p09306301\.html\?[^ ]*v1=406")
    check_visited_path(judge, traj, "nav_bag", r"/us/en/shop")
    check_visited_path(judge, traj, "nav_search", r"/us/en/search\?[^ ]*searchTerm=DISTRESSED")
    check_visited_path(judge, traj, "nav_distressed", r"distressed-flare-fit-jeans-p08062380\.html")

    check_answer_number(judge, answer, "jeans_upstream", 115)
    check_answer_number(judge, answer, "jeans_snapshot", 10)
    check_answer_count_at_least(judge, answer, "black_names", ["PRINTED LOOSE FIT JEANS", "BASIC SLIM FIT JEANS", "LOOSE FIT JEANS"], 3)
    check_answer_money(judge, answer, "under40_price", 35.94)
    check_answer_count_at_least(judge, answer, "three_colors", ["Light blue", "Ecru", "charcoal gray"], 3)
    check_answer_regex(judge, answer, "cg34", r"34 \(US 34\) IN STOCK")
    check_answer_count_at_least(judge, answer, "lb_nostock", ["32 (US 32)", "34 (US 34)"], 2)
    check_answer_money(judge, answer, "ecru_doubled_sub", 71.88)
    check_answer_money(judge, answer, "ecru_doubled_total", 76.83)
    check_answer_number(judge, answer, "distressed_matches", 2)
    check_answer_phrase(judge, answer, "distressed_jeans", "DISTRESSED FLARE FIT JEANS")
    check_answer_money(judge, answer, "final_subtotal", 151.78)
    check_answer_money(judge, answer, "final_total", 156.73)

    check_only_tables_changed(judge, initial, after, {"cart_items"})
    check_rows_added(judge, initial, after, "cart_items",
                     [[None, None, "rx:^[0-9a-f]{32}$", 555487955, 104, 481, 2, "2026-09-29"],
                      [None, None, "rx:^[0-9a-f]{32}$", 575979403, 89, 381, 1, "2026-09-29"]],
                     "t20_guest_rows")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
