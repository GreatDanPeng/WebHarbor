#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--16."""
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
    check_trajectory_identity(judge, traj, "UPS--16")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_services", r"/services")
    check_visited_path(judge, traj, "nav_2dm_detail", r"/services/2DM")
    check_visited_path(judge, traj, "nav_ctc", r"/ctc")
    check_visited_path(judge, traj, "nav_gnd_detail", r"/services/GND")
    check_answer_count_at_least(judge, answer, "saturday_air_services",
                                ["next day air early", "next day air",
                                 "2nd day air", "3 day select"], 4)
    check_answer_phrase(judge, answer, "2dm_commitment",
                        "guaranteed on-time delivery by 10:30 a.m. or 12:00 p.m.")
    check_answer_phrase(judge, answer, "2dm_second_day", "second business day")
    check_answer_phrase(judge, answer, "2dm_guarantee", "guaranteed")
    check_answer_phrase(judge, answer, "2dm_latest_pickup", "9:00 p.m.")
    check_answer_money(judge, answer, "sf_sea_2dm_price", 79.99)
    check_answer_phrase(judge, answer, "sf_sea_2dm_delivered_by", "10:30 a.m. wednesday september 30")
    check_answer_phrase(judge, answer, "gnd_max_weight", "150")
    check_answer_phrase(judge, answer, "gnd_delivered_by_default", "one to five business days")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--16", checks))
