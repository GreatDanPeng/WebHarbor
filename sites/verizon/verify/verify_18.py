#!/usr/bin/env python3
"""Deterministic verifier for Verizon--18 (verizon).

Ground truth below is HARDCODED (frozen from the contributor's two
independent strict-caliber Playwright rounds on the r3 fix container
wh-verizon-fix3, seed md5 f2d20153c24b6945fb5203b81d7f1fb6) — never read
from tasks.jsonl. Navigation gates cover ONLY the surfaces the (r3
deepened) task text requires; answer anchors are page-verbatim with
tolerance for equally-honest renderings.
Usage: python3 verify_18.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_number_absent, check_answer_ordered, check_answer_phrase,
    check_answer_regex, check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, db_one, final_answer, run_verifier,
)

TASK_ID = "Verizon--18"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_gridwall", r"/smartphones/$")
    check_visited_path(judge, traj, "nav_18p_pdp", r"/smartphones/apple-iphone-18-pro/$")
    check_visited_path(judge, traj, "nav_18p_configure", r"/smartphones/apple-iphone-18-pro/configure")
    check_visited_path(judge, traj, "nav_cart_1", r"/cart/")
    check_visited_path(judge, traj, "nav_s26u_pdp", r"/smartphones/samsung-galaxy-s26-ultra/$")
    check_visited_path(judge, traj, "nav_s26u_configure", r"/smartphones/samsung-galaxy-s26-ultra/configure")
    check_visited_path(judge, traj, "nav_cart_2", r"/cart/")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")

    # answer ground truth
    check_answer_money(judge, answer, "ip_36mo", 33.33)
    check_answer_money(judge, answer, "ip_full_retail", 1199.99)
    check_answer_count_at_least(judge, answer, "ip_storage",
        ["256 GB", "512 GB", "1 TB", "2 TB"], 4)
    check_answer_phrase(judge, answer, "ip_battery", "Typical use: Up to 24 hours")
    check_answer_phrase(judge, answer, "ip_screen", "Super Retina XDR")
    check_answer_any(judge, answer, "ip_rating",
        ["4.2 out of 5 rating (93 reviews)", "4.2 (93 reviews)",
         "4.2 out of 5 (93 reviews)"])
    check_answer_money(judge, answer, "su_36mo", 36.11)
    check_answer_money(judge, answer, "su_full_retail", 1299.99)
    check_answer_count_at_least(judge, answer, "su_storage", ["256 GB", "512 GB"], 2)
    check_answer_phrase(judge, answer, "su_battery", "Up to 30.62 hrs")
    check_answer_any(judge, answer, "su_screen",
        ["QHD+ Dynamic AMOLED 2x Display", "Dynamic AMOLED 2x"])
    check_answer_any(judge, answer, "su_rating",
        ["4.8 out of 5 rating (18000 reviews)", "4.8 (18K reviews)",
         "4.8 out of 5 (18000 reviews)", "4.8 (18000 reviews)"])
    check_answer_regex(judge, answer, "reviews_verdict",
        r"S26 Ultra reviews better|reviews better[^.]{0,20}S26 Ultra|S26 Ultra[^.]{0,30}better")
    check_answer_regex(judge, answer, "storage_verdict",
        r"tie|neither|equal|same")
    check_answer_money(judge, answer, "ip_cart_line", 79.99)
    check_answer_money(judge, answer, "su_cart_line", 84.16)
    check_answer_money(judge, answer, "combined_total", 164.15)
    check_answer_money(judge, answer, "est_18pm_good", 730.00)

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
