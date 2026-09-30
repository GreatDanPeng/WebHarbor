#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--12."""
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
    check_trajectory_identity(judge, traj, "UPS--12")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_detail", r"/track/detail/1ZW362F70355812012$")
    check_visited_path(judge, traj, "nav_change_delivery", r"/track/detail/1ZW362F70355812012/change-delivery")
    check_visited_path(judge, traj, "nav_intercept_article", r"/support/article/ups-delivery-intercept")
    check_visited_path(judge, traj, "nav_locator", r"/locations\?zip=30301")
    check_answer_phrase(judge, answer, "change_option_hold", "hold for pickup")
    check_answer_phrase(judge, answer, "change_option_address", "deliver to another address")
    check_answer_phrase(judge, answer, "change_option_reschedule", "reschedule delivery")
    check_answer_money(judge, answer, "intercept_web_fee", 18.00)
    check_answer_money(judge, answer, "intercept_phone_fee", 21.00)
    check_answer_count_at_least(judge, answer, "intercept_actions",
                                ["return to sender", "deliver to another address",
                                 "reschedule delivery", "will call"], 3)
    check_answer_phrase(judge, answer, "closest_ap_name", "cvs store # 10043")
    check_answer_phrase(judge, answer, "closest_ap_street", "235 peachtree st")
    check_answer_phrase(judge, answer, "current_status", "in transit")
    check_answer_phrase(judge, answer, "latest_scan_location", "louisville")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--12", checks))
