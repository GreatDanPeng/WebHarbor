#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--3."""
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
    check_trajectory_identity(judge, traj, "UPS--3")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_ctc", r"/ctc")
    check_answer_number(judge, answer, "services_count", "6")
    check_answer_phrase(judge, answer, "cheapest_service", "ups ground")
    check_answer_money(judge, answer, "cheapest_price", 21.40)
    check_answer_phrase(judge, answer, "most_expensive_service", "next day air")
    check_answer_phrase(judge, answer, "most_expensive_early", "early")
    check_answer_money(judge, answer, "most_expensive_price", 243.57)
    check_answer_any(judge, answer, "price_change",
                    ["no change", "unchanged", "does not change", "stays", "same price",
                     "remains", "still $21.40", "no difference", "$0"])
    check_answer_money(judge, answer, "nonresi_cheapest_price", 21.40)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--3", checks))
