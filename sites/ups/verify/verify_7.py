#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--7."""
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
    check_trajectory_identity(judge, traj, "UPS--7")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_locator", r"/locations\?zip=10001")
    check_visited_path(judge, traj, "nav_dropbox_detail", r"/locations/235041")
    check_visited_any(judge, traj, "nav_store_or_ap_detail", [r"/locations/255850", r"/locations/152025"])
    check_answer_number(judge, answer, "total_locations", "20")
    check_answer_number(judge, answer, "access_points_count", "2")
    check_answer_number(judge, answer, "drop_boxes_count", "8")
    check_answer_phrase(judge, answer, "dropbox_name", "tishman speyer")
    check_answer_phrase(judge, answer, "dropbox_street", "66 hudson blvd e")
    check_answer_phrase(judge, answer, "dropbox_ground_dropoff", "mon-fri: 1:30pm")
    check_answer_phrase(judge, answer, "store_phone", "2124577300")
    check_answer_phrase(judge, answer, "ap_street", "334 w 37th st")
    # The closest Access Point (Deepchhaya Deli & Grocery, loc 152025) has no
    # phone in the captured locator data: the detail page shows no Tel line.
    # Defensible reading frozen: report the address + that no phone is listed
    # (or explicitly 'not listed'/'no phone'). Reporting another location's
    # phone is a wrong answer and fails.
    check_answer_any(judge, answer, "ap_phone",
                     ["no phone", "not listed", "no phone listed", "none listed",
                      "no number", "phone is not", "no tel"])
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--7", checks))
