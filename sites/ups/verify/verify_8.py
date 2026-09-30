#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--8."""
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
    check_trajectory_identity(judge, traj, "UPS--8")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_account", r"/account")
    check_visited_path(judge, traj, "nav_detail", r"/track/detail/1Z7R4T920399120014$")
    check_visited_path(judge, traj, "nav_track_page", r"/track\?tracknums?=.*1Z7R4T920399120014")
    check_answer_number(judge, answer, "packages_count", "3")
    check_answer_number(judge, answer, "delivered_count", "1")
    check_answer_number(judge, answer, "in_transit_count", "2")
    check_answer_phrase(judge, answer, "signed_by", "t. olsen")
    check_answer_phrase(judge, answer, "delivery_day", "2026-09-26")
    check_answer_phrase(judge, answer, "pkg2_scan_status", "departed from facility")
    check_answer_phrase(judge, answer, "pkg2_scan_location", "commerce city")
    check_answer_phrase(judge, answer, "track_status", "in transit")
    check_answer_phrase(judge, answer, "latest_scan_facility", "commerce city")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--8", checks))
