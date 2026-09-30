#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--0."""
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
    check_trajectory_identity(judge, traj, "UPS--0")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    # navigation: multi-number track, both details, locator, location detail
    check_visited_path(judge, traj, "nav_track", r"/track\?tracknums?=.*1Z58F0E70312456012")
    check_visited_path(judge, traj, "nav_track_second", r"/track\?tracknums?=.*1Z58F0E71248779034|"
                       r"tracknums=1Z58F0E71248779034")
    check_visited_path(judge, traj, "nav_detail_first", r"/track/detail/1Z58F0E70312456012$")
    check_visited_path(judge, traj, "nav_detail_second", r"/track/detail/1Z58F0E71248779034$")
    check_visited_path(judge, traj, "nav_locator", r"/locations\?zip=10001")
    check_visited_path(judge, traj, "nav_pickup_location", r"/locations/255850")
    # answers
    check_answer_phrase(judge, answer, "latest_scan_status", "out for delivery")
    check_answer_phrase(judge, answer, "latest_scan_location", "maspeth")
    check_answer_phrase(judge, answer, "latest_scan_day", "2026-09-28")
    check_answer_phrase(judge, answer, "latest_scan_time", "8:52")
    check_answer_number(judge, answer, "facility_stops_after_seattle", "4")
    check_answer_count_at_least(judge, answer, "facility_stops_cities",
                               ["spokane", "commerce city", "hodgkins", "maspeth"], 3)
    check_answer_any(judge, answer, "pickup_location_name",
                     ["the ups store", "the upss store"])
    check_answer_phrase(judge, answer, "pickup_location_street", "337 10th ave")
    check_answer_phrase(judge, answer, "pickup_by_date", "2026-10-05")
    check_answer_phrase(judge, answer, "ground_dropoff", "mon-fri: 6:30pm")
    # DB: read-only task
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--0", checks))
