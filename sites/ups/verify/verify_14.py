#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--14."""
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
    check_trajectory_identity(judge, traj, "UPS--14")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_weekend", r"/business/weekend-pickup")
    check_visited_path(judge, traj, "nav_pickup", r"/pickup")
    check_visited_path(judge, traj, "nav_pickup_confirm", r"/pickup/confirm/PK")
    check_answer_money(judge, answer, "smart_saturday_fee", 8.00)
    check_answer_money(judge, answer, "saturday_stop_charge", 12.00)
    check_answer_money(judge, answer, "review_total_fee", 16.60)
    check_answer_phrase(judge, answer, "confirmation_number", "pk1000001")
    # DB: exactly one Saturday pickup request at 88 King Street
    check_only_tables_changed(judge, initial, after, {"pickup_requests"})
    check_rows_added(judge, initial, after, "pickup_requests",
                     [(None, "PK1000001", None, None, None, None,
                       "88 King Street", "San Francisco", "CA", "94107",
                       None, "2026-10-03", "9:00 AM", "5:00 PM",
                       1, 5.0, None, 1, 16.6, None, None)],
                     "db_pickup_row")


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--14", checks))
