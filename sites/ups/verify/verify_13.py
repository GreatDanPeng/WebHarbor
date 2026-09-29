#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--13."""
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
    check_trajectory_identity(judge, traj, "UPS--13")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_support_search", r"/support\?q=status")
    check_visited_path(judge, traj, "nav_status_article", r"/support/article/understanding-tracking-status")
    check_visited_path(judge, traj, "nav_detail", r"/track/detail/1Z99624Y0371728890$")
    check_visited_path(judge, traj, "nav_locator", r"/locations\?zip=10001&type=UPS(%20|\+| )Drop(%20|\+| )Box")
    check_answer_phrase(judge, answer, "label_created_meaning",
                        "we've received the shipment details and billing information")
    check_answer_phrase(judge, answer, "long_distance_note",
                        "won't be scanned again until they reach their destination hub")
    # 'second-to-last scan' frozen as the second most recent scan
    # (penultimate in time): Departed from Facility, Louisville, KY, 2026-09-27.
    check_answer_phrase(judge, answer, "second_to_last_scan_location", "louisville")
    check_answer_phrase(judge, answer, "second_to_last_scan_day", "2026-09-27")
    check_answer_phrase(judge, answer, "scheduled_delivery", "2026-10-02")
    check_answer_phrase(judge, answer, "service", "ups ground")
    check_answer_phrase(judge, answer, "dropbox_name", "tishman speyer")
    check_answer_phrase(judge, answer, "dropbox_ground_dropoff", "mon-fri: 1:30pm")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--13", checks))
