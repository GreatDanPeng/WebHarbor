#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--4."""
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
    check_trajectory_identity(judge, traj, "UPS--4")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_compare", r"/services/compare")
    check_visited_path(judge, traj, "nav_ctc", r"/ctc")
    check_visited_path(judge, traj, "nav_service_detail", r"/services/1DA")
    check_answer_phrase(judge, answer, "guaranteed_1030_nextday_early", "next day air early")
    check_answer_phrase(judge, answer, "guaranteed_1030_nextday", "next day air")
    check_answer_absent(judge, answer, "not_2dm_nextday",
                        "2nd day air a.m. delivers by 10:30 the next business day")
    check_answer_phrase(judge, answer, "cheapest_of_those", "next day air")
    check_answer_money(judge, answer, "cheapest_price", 134.98)
    check_answer_phrase(judge, answer, "delivered_by_commitment", "10:30 a.m. tuesday september 29")
    check_answer_phrase(judge, answer, "latest_pickup", "9:00 p.m.")
    check_answer_phrase(judge, answer, "schedule_by", "7:00 p.m.")
    check_answer_phrase(judge, answer, "max_weight", "150")
    check_answer_phrase(judge, answer, "max_length", "108")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--4", checks))
