#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--17."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (Judge, check_answer_absent, check_answer_any,
                        check_answer_count_at_least, check_answer_money,
                        check_answer_number, check_answer_phrase,
                        check_only_tables_changed, check_read_only,
                        check_rows_added, check_rows_changed,
                        check_seed_contract, check_screenshots,
                        check_trajectory_identity, check_visited_any,
                        check_visited_path, final_answer, run_verifier)


def checks(judge, traj, initial, after):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, "UPS--17")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_account", r"/account")
    check_visited_path(judge, traj, "nav_detail", r"/track/detail/1Z58F0E70312456012$")
    check_visited_path(judge, traj, "nav_change_delivery", r"/track/detail/1Z58F0E70312456012/change-delivery")
    check_visited_path(judge, traj, "nav_intercept_article", r"/support/article/ups-delivery-intercept")
    check_answer_number(judge, answer, "account_shipments", "4")
    check_answer_count_at_least(judge, answer, "account_statuses",
                               ["delivered", "exception", "out for delivery",
                                "awaiting customer pickup"], 4)
    check_answer_phrase(judge, answer, "scheduled_delivery", "2026-09-28")
    check_answer_phrase(judge, answer, "change_option_hold", "hold for pickup")
    check_answer_phrase(judge, answer, "change_option_address", "deliver to another address")
    check_answer_phrase(judge, answer, "change_option_reschedule", "reschedule delivery")
    check_answer_phrase(judge, answer, "out_for_delivery_facility", "maspeth")
    check_answer_phrase(judge, answer, "confirmation_text", "held for pickup at")
    check_answer_money(judge, answer, "intercept_web_fee", 18.00)
    # DB: exactly one hold change on the out-for-delivery shipment
    check_only_tables_changed(judge, initial, after,
                              {"shipments", "tracking_events", "tracking_changes"})
    check_rows_added(judge, initial, after, "tracking_changes",
                     [(None, 1, "hold", "255850", "2026-09-28")],
                     "db_change_row")
    check_rows_added(judge, initial, after, "tracking_events",
                     [(None, 1, None, "2026-09-28", "—", "Hold for Pickup Requested",
                       "New York, NY",
                       "rx:^Delivery changed: the package will be held for pickup at "
                       "The Ups Store, 337 10Th Ave, New York, NY 10001[.]",
                       None)], "db_hold_event")
    hold = after.execute(
        "SELECT hold_location_id, hold_by FROM shipments "
        "WHERE tracking_number='1Z58F0E70312456012'").fetchone()
    if hold != ("255850", "2026-10-05"):
        judge.fail("db_shipment_hold", f"hold={hold!r}")
    else:
        judge.ok("db_shipment_hold", f"hold_location_id={hold[0]}, hold_by={hold[1]}")


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--17", checks))
