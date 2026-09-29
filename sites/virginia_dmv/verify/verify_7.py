#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--7 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_7.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_ordered,
    check_answer_money_after, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Virginia DMV--7"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # alice's seeded appointment lookup + Richmond Central office research
    check_visited_path(judge, traj, "nav_appointments", r"/appointments")
    check_visited_path(judge, traj, "nav_lookup", r"/appointments/lookup")
    check_visited_path(judge, traj, "nav_office", r"/locations/richmond-central")
    check_visited_path(judge, traj, "nav_richmond_search", r"/all-locations\?q=Richmond")
    check_visited_path(judge, traj, "nav_dmv_select_richmond", r"/all-locations\?q=Richmond&type=dmv_select")
    check_answer_phrase(judge, answer, "confirmation", "VADM9620114A")
    check_answer_phrase(judge, answer, "service", "Driver's License Renewal")
    check_answer_any(judge, answer, "office", ["richmond central"])
    check_answer_any(judge, answer, "date", ["2026-10-07", "october 7"])
    check_answer_phrase(judge, answer, "time", "10:20 AM")
    check_answer_phrase(judge, answer, "status", "Confirmed")
    check_answer_count_at_least(judge, answer, "booking_selects",
                                ["service type", "office", "date and time",
                                 "service, the office"], 2)
    check_answer_phrase(judge, answer, "office_address", "2300 West Broad Street")
    check_answer_any(judge, answer, "office_phone", ["804-497-7100", "(804) 497-7100"])
    check_answer_any(judge, answer, "weekday_hours", ["8:00 am-5:00 pm", "8:00 am - 5:00 pm"])
    check_answer_any(judge, answer, "saturday_hours", ["8:00 am-12:00 pm", "8:00 am - 12:00 pm"])
    check_answer_any(judge, answer, "not_offered", ["motorcycle skills testing"])
    check_answer_any(judge, answer, "nearby_office", ["east henrico"])
    check_answer_phrase(judge, answer, "nearby_address", "5517 South Laburnum Avenue")
    check_answer_number(judge, answer, "richmond_search_count", 6)
    check_answer_number(judge, answer, "richmond_dmv_select_count", 1)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
