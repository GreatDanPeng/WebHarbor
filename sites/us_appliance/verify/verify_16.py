#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--16 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_16.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "USAppliance--16"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: registration, product page, cart, checkout, confirmation.
    check_visited_any(judge, traj, "nav_register", [r"/login\.php\?action=create_account", r"action=create_account"])
    check_visited_path(judge, traj, "nav_jgbs66_product", r"/jgbs66rekss\.html")
    check_visited_path(judge, traj, "nav_cart", r"/cart\.php")
    check_visited_any(judge, traj, "nav_checkout", [r"/checkout", r"Place Order"])
    check_visited_path(judge, traj, "nav_confirmation", r"/order-confirmation/10009")
    # answer ground truth
    check_answer_number(judge, answer, "order_number", 10009)
    check_answer_money(judge, answer, "order_total", 1022)
    check_only_tables_changed(judge, initial, after, ('users', 'orders', 'order_items', 'order_events'))
    # DB: the new user, the order (In-Home), its item, its placed event.
    check_rows_added(judge, initial, after, "users",
                     [[None, "morgan.t@example.com", None, "Morgan Torres", None,
                       r"rx:^20\d\d-\d\d-\d\d$"]], "db_user_row")
    check_rows_added(judge, initial, after, "orders",
                     [[None, "10009", None, "morgan.t@example.com", "Morgan Torres",
                       "9 Elm St", "Columbus", "OH", "43215", None, "Processing",
                       "In-Home Delivery", 199.0, 823.0, 0.0, 1022.0, None, None,
                       r"rx:^20\d\d-\d\d-\d\d$", None, ""]], "db_order_row")
    check_rows_added(judge, initial, after, "order_items",
                     [[None, None, 21476,
                       "GE JGBS66REKSS 30\" Free-Standing Gas Range with Edge to Edge Cooktop - Stainless Steel",
                       1, 823.0]], "db_order_item_row")
    check_rows_added(judge, initial, after, "order_events",
                     [[None, None, "Order Placed", r"rx:^20\d\d-\d\d-\d\d$",
                       "We received your order."]], "db_order_event_row")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
