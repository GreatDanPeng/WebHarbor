#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--15."""
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
    check_trajectory_identity(judge, traj, "UPS--15")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_locator", r"/locations\?zip=60601")
    check_visited_path(judge, traj, "nav_store_detail", r"/locations/94892")
    check_visited_path(judge, traj, "nav_pack_ship", r"/store/pack-and-ship")
    check_answer_phrase(judge, answer, "store_name", "the ups store")
    check_answer_phrase(judge, answer, "store_street", "323 e wacker dr")
    check_answer_phrase(judge, answer, "store_phone", "3122688290")
    check_answer_phrase(judge, answer, "mon_hours", "9:00 am")
    check_answer_phrase(judge, answer, "tue_hours", "8:00 am")
    check_answer_phrase(judge, answer, "air_dropoff", "mon-fri: 3:00pm")
    check_answer_phrase(judge, answer, "ground_dropoff", "mon-fri: 3:00pm")
    check_answer_phrase(judge, answer, "ap_name", "cvs store # 8910")
    check_answer_phrase(judge, answer, "ap_street", "205 n columbus dr")
    check_answer_phrase(judge, answer, "which_closer", "access point")
    check_answer_phrase(judge, answer, "pack_experts", "certified packing experts")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--15", checks))
