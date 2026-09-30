#!/usr/bin/env python3
"""Deterministic verifier for Verizon--19 (verizon).

Ground truth below is HARDCODED (frozen from the contributor's two
independent strict-caliber Playwright rounds on the r3 fix container
wh-verizon-fix3, seed md5 f2d20153c24b6945fb5203b81d7f1fb6) — never read
from tasks.jsonl. Navigation gates cover ONLY the surfaces the (r3
deepened) task text requires; answer anchors are page-verbatim with
tolerance for equally-honest renderings.
Usage: python3 verify_19.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--19"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_prepaid", r"/prepaid/")
    check_visited_path(judge, traj, "nav_gridwall", r"/smartphones/$")
    check_visited_path(judge, traj, "nav_a17_pdp", r"/smartphones/samsung-galaxy-a17-5g/$")
    check_visited_path(judge, traj, "nav_a17_configure", r"/smartphones/samsung-galaxy-a17-5g/configure")
    check_visited_path(judge, traj, "nav_cart", r"/cart/")
    check_visited_path(judge, traj, "nav_checkout", r"/checkout/")
    check_visited_path(judge, traj, "nav_order_conf", r"/order/VZW[0-9]+")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")

    # answer ground truth
    check_answer_money(judge, answer, "unl_base", 60.00)
    check_answer_money(judge, answer, "unl_autopay", 50.00)
    check_answer_money(judge, answer, "unl_3mo_price", 55.00)
    check_answer_money(judge, answer, "unl_9mo_price", 50.00)
    check_answer_regex(judge, answer, "tt_lacks",
        r"Talk & Text[^.]{0,120}(lack|only|without|no )")
    check_answer_regex(judge, answer, "voids_lock",
        r"void if lines are canceled|voided if the line is disconnected")
    check_answer_money(judge, answer, "cart_total", 70.41)
    check_answer_money(judge, answer, "est_razr_good", 330.00)
    check_answer_money(judge, answer, "est_razr_cracked", 100.00)
    row = db_one(after, "SELECT confirmation, total_monthly FROM orders WHERE id = (SELECT MAX(id) FROM orders)")
    check_answer_confirmation(judge, answer, "order_confirmation", row[0] if row else None, "VZW")
    check_answer_phrase(judge, answer, "delivery_window", "Ships between Wed, Sep 30 - Fri, Oct 9")

    # DB after-state: exact allowed delta
    check_only_tables_changed(judge, initial, after, {"orders"})
    check_rows_added(judge, initial, after, "orders",
        [[None, None, "rx:^VZW[0-9]{6}$", "processing", "2026-09-29",
          "Ships between Wed, Sep 30 - Fri, Oct 9", None, "0.00", "70.41",
          "Rosa Diaz", "rosa.diaz@example.com", "415 Pine St", "Tacoma",
          "WA", "98409"]], "order_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
