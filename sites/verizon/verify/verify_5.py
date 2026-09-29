#!/usr/bin/env python3
"""Deterministic verifier for Verizon--5 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_5.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--5"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_gridwall_moto_asc", r"/smartphones/\?brand=Motorola&sort=price-asc")
    check_visited_path(judge, traj, "nav_motog_pdp", r"/smartphones/motorola-moto-g-2026/$")
    check_visited_path(judge, traj, "nav_motog_configure", r"/smartphones/motorola-moto-g-2026/configure")
    check_visited_path(judge, traj, "nav_cart", r"/cart/")
    check_visited_path(judge, traj, "nav_checkout", r"/checkout/")
    check_visited_path(judge, traj, "nav_order", r"/order/VZW[0-9]+")

    # answer ground truth
    check_answer_number(judge, answer, "moto_count", 9)
    check_answer_any(judge, answer, "cheapest_motorola",
        ["Motorola moto g - 2026", "moto g - 2026"])
    check_answer_money(judge, answer, "motog_retail", 279.99)
    check_answer_phrase(judge, answer, "motog_battery", "Up to 69hrs")
    row = db_one(after, "SELECT confirmation, total_monthly, delivery_by, items FROM orders WHERE id = (SELECT MAX(id) FROM orders)")
    check_answer_confirmation(judge, answer, "order_confirmation", row[0] if row else None, "VZW")
    check_answer_money(judge, answer, "order_monthly", 54.77)
    check_answer_phrase(judge, answer, "order_delivery", "Wed, Sep 30 - Fri, Oct 9")
    check_answer_money(judge, answer, "vmp_cost", 17.00)
    check_answer_phrase(judge, answer, "order_plan", "Simplicity Plan")

    # DB after-state: exact allowed delta
    check_only_tables_changed(judge, initial, after, {"orders"})
    check_rows_added(judge, initial, after, "orders",
        [[None, None, "rx:^VZW[0-9]{6}$", "processing", "2026-09-29",
          "Ships between Wed, Sep 30 - Fri, Oct 9", None, "0.00", "54.77",
          "Jordan Pratt", "jordan.pratt@example.com", "88 Pine Street",
          "Seattle", "WA", "98101"]], "order_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
