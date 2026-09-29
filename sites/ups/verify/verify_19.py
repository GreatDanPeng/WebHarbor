#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--19."""
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
    check_trajectory_identity(judge, traj, "UPS--19")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_ctc", r"/ctc")
    check_visited_path(judge, traj, "nav_intercept_article", r"/support/article/ups-delivery-intercept")
    check_answer_phrase(judge, answer, "ground_price_service", "ups ground")
    check_answer_money(judge, answer, "ground_price", 32.80)
    check_answer_phrase(judge, answer, "ground_delivered_by", "wednesday september 30")
    check_answer_phrase(judge, answer, "billable_weight", "15.0")
    check_answer_money(judge, answer, "nde_transportation", 246.68)
    check_answer_money(judge, answer, "nde_das", 4.50)
    check_answer_money(judge, answer, "nde_fuel", 84.15)
    check_answer_money(judge, answer, "intercept_web_fee", 18.00)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--19", checks))
