#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--1."""
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
    check_trajectory_identity(judge, traj, "UPS--1")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_detail", r"/track/detail/1Z58F0E70291534227$")
    check_visited_path(judge, traj, "nav_status_article", r"/support/article/understanding-tracking-status")
    check_visited_path(judge, traj, "nav_change_delivery", r"/track/detail/1Z58F0E70291534227/change-delivery")
    check_visited_path(judge, traj, "nav_intercept_article", r"/support/article/ups-delivery-intercept")
    check_answer_phrase(judge, answer, "status", "exception")
    check_answer_phrase(judge, answer, "exception_reason_k1",
                        "the address information provided by the sender is incorrect")
    check_answer_any(judge, answer, "exception_reason_k2",
                     ["sender has been notified", "delivery is pending corrected address"])
    check_answer_phrase(judge, answer, "scheduled_delivery", "2026-09-25")
    check_answer_phrase(judge, answer, "article_cause",
                        "unexpected error that may result in a change in the scheduled delivery date")
    check_answer_phrase(judge, answer, "article_reason_noted",
                        "shipment progress section")
    check_answer_phrase(judge, answer, "change_option_hold", "hold for pickup")
    check_answer_phrase(judge, answer, "change_option_address", "deliver to another address")
    check_answer_phrase(judge, answer, "change_option_reschedule", "reschedule delivery")
    check_answer_money(judge, answer, "intercept_web_fee", 18.00)
    check_answer_money(judge, answer, "intercept_phone_fee", 21.00)
    check_answer_phrase(judge, answer, "shipper_name", "harbor lane apparel")
    check_answer_phrase(judge, answer, "shipper_city", "portland")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--1", checks))
