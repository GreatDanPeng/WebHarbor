#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--11."""
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
    check_trajectory_identity(judge, traj, "UPS--11")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_account", r"/account")
    check_visited_path(judge, traj, "nav_daily", r"/business/daily-pickup")
    check_visited_path(judge, traj, "nav_smart", r"/business/smart-pickup")
    check_visited_path(judge, traj, "nav_dayspecific", r"/business/day-specific-pickup")
    check_visited_path(judge, traj, "nav_pickup_options", r"/business/pickup-dropoff-options")
    check_visited_path(judge, traj, "nav_weekend", r"/business/weekend-pickup")
    check_answer_number(judge, answer, "account_shipments", "3")
    check_answer_money(judge, answer, "daily_fee", 39.00)
    check_answer_money(judge, answer, "smart_fee", 18.50)
    check_answer_money(judge, answer, "dayspecific_3day_fee", 23.25)
    cheap_sentences = [s for s in answer.lower().split(".")
                       if "cheapest" in s]
    if not cheap_sentences:
        judge.fail("cheapest_pickup", "answer never states which pickup option is cheapest")
    elif not any("smart pickup" in s for s in cheap_sentences):
        judge.fail("cheapest_pickup", "no 'cheapest' sentence names UPS Smart Pickup")
    elif any(("day-specific" in s or "daily pickup" in s) for s in cheap_sentences):
        judge.fail("cheapest_pickup", "a 'cheapest' sentence names a more expensive option")
    else:
        judge.ok("cheapest_pickup", "smart pickup named cheapest")
    check_answer_money(judge, answer, "oncall_future_fee", 9.65)
    check_answer_money(judge, answer, "oncall_same_day_fee", 15.75)
    check_answer_money(judge, answer, "smart_saturday_fee", 8.00)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--11", checks))
