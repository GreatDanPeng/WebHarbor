#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--6."""
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
    check_trajectory_identity(judge, traj, "UPS--6")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_account", r"/account")
    check_visited_path(judge, traj, "nav_pickup", r"/pickup")
    check_visited_path(judge, traj, "nav_pickup_confirm", r"/pickup/confirm/PK1000001|"
                       r"/pickup/confirm/PK")
    check_answer_phrase(judge, answer, "label_created_tracking", "1z7r4t920199330245")
    check_answer_phrase(judge, answer, "label_created_service", "next day air saver")
    check_answer_phrase(judge, answer, "label_created_sched", "2026-09-29")
    check_answer_phrase(judge, answer, "pickup_confirmation", "pk1000001")
    check_answer_money(judge, answer, "pickup_fee", 9.65)
    # DB: exactly one future-day pickup request for Dave Miller at MoPac
    check_only_tables_changed(judge, initial, after, {"pickup_requests"})
    check_rows_added(judge, initial, after, "pickup_requests",
                     [(None, "PK1000001", 4, None, None, None,
                       "1701 South MoPac Expressway", "Austin", "TX", "78746",
                       None, "2026-09-29", "9:00 AM", "5:00 PM",
                       1, 9.8, None, 0, 9.65, None, None)],
                     "db_pickup_row")


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--6", checks))
