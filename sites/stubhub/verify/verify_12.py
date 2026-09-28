#!/usr/bin/env python3
"""Verify StubHub--12.

Create a new StubHub account with a realistic name and email and a password of your choice. Then buy the cheapest available single ticket to the October 11 49ers at Seahawks game with instant download delivery, paying with any valid test card. Report the order reference and final total, and confirm the order appears in the new account's purchase history.
"""
from verify_lib import (Judge, check_answer_any, check_answer_number, check_answer_phrase,
                        check_answer_regex, check_answer_one_of, check_read_only,
                        check_only_tables_changed, check_table_deltas, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier)

TASK_ID = "StubHub--12"

from verify_lib import table_diff


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_register", r"/secure/register")
    check_visited_path(judge, traj, "visited_49ers_event", r"/seattle-seahawks-seattle-tickets-10-11-2026/event/160436498")
    check_visited_path(judge, traj, "visited_listing", r"/event/160436498/listing/1189")
    check_visited_path(judge, traj, "checkout_review", r"/secure/checkout/review")
    check_visited_path(judge, traj, "checkout_payment", r"/secure/checkout/payment")
    check_visited_path(judge, traj, "checkout_confirmation", r"/secure/checkout/confirmation/41801303")
    check_visited_path(judge, traj, "visited_purchase_history", r"/secure/myaccount/purchases")
    
    check_answer_number(judge, answer, "order_reference", 41801303)
    check_answer_number(judge, answer, "final_total", "369.95")
    judge.check("order_in_history_confirmed",
                "appears" in answer.casefold() and "history" in answer.casefold(),
                "answer must confirm the order appears in the purchase history")
    added_u, _, _ = table_diff(initial_db, after_db, "users")
    judge.check("new_user_created", len(added_u) == 1, f"exactly one new user: {list(added_u)}")
    new_uid = next(iter(added_u))[0] if added_u else None
    added_o, _, _ = table_diff(initial_db, after_db, "orders")
    judge.check("new_order_created", len(added_o) == 1, f"exactly one new order: {list(added_o)}")
    for key, row in added_o.items():
        judge.check("order_row_exact",
                   row["order_number"] == "41801303" and row["user_id"] == new_uid
                   and row["event_id"] == 128 and row["listing_id"] == 1189
                   and row["quantity"] == 1 and row["delivery_method"] == "instant"
                   and row["delivery_fee"] == 0.0 and row["processing_fee"] == 2.95
                   and row["total"] == 369.95 and row["status"] == "Confirmed",
                   f"order must be the single 49ers ticket at $369.95: {dict(row)}")
    _, _, changed_l = table_diff(initial_db, after_db, "listings")
    judge.check("listing_1189_sold",
                (1189,) in changed_l and changed_l[(1189,)][1]["is_sold"] == 1,
                "listing 1189 must be marked sold")
    added_c, _, _ = table_diff(initial_db, after_db, "payment_cards")
    judge.check("new_card_created", len(added_c) == 1
                and next(iter(added_c.values()))["user_id"] == new_uid,
                f"the new user's payment card: {list(added_c)}")
    added_n, _, _ = table_diff(initial_db, after_db, "notifications")
    judge.check("notification_created", len(added_n) == 1
                and next(iter(added_n.values()))["user_id"] == new_uid,
                f"one order notification for the new user: {list(added_n)}")
    check_only_tables_changed(judge, initial_db, after_db, ("users", "orders", "listings", "payment_cards", "notifications"))


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
