#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--15 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the r3 honest Playwright walks on
the fix container wh-vadm-fix3, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r3-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_15.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Virginia DMV--15"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # new-to-Virginia research chain + Richmond counts + title appointment
    check_visited_path(judge, traj, "nav_moving", r"/moving(?!/)")
    check_visited_path(judge, traj, "nav_new_virginia", r"/moving/new-virginia")
    check_visited_path(judge, traj, "nav_manual_exam", r"/drivers-manual/1/1")
    check_visited_path(judge, traj, "nav_richmond_search", r"/all-locations\?q=Richmond")
    check_visited_path(judge, traj, "nav_richmond_csc", r"/all-locations\?q=richmond&type=csc")
    check_visited_path(judge, traj, "nav_wizard", r"/appointments/new")
    check_answer_number(judge, answer, "license_deadline", 60)
    check_answer_number(judge, answer, "title_deadline", 30)
    check_answer_number(judge, answer, "cdl_deadline", 30)
    check_answer_count_at_least(judge, answer, "safety_inspection",
        ["annual safety inspection", "safety inspection sticker", "annual inspection"], 1)
    check_answer_count_at_least(judge, answer, "emissions_localities", ["fairfax"], 1)
    check_answer_any(judge, answer, "insurance_note", ["from the moment you register", "moment you register"])
    check_answer_any(judge, answer, "sticker_note", ["local sticker or decal", "local sticker", "decal"])
    check_answer_any(judge, answer, "cdl_rule", ["virginia cdl within 30 days", "get a virginia cdl within 30 days"])
    check_answer_any(judge, answer, "voter_note", ["voter registration is available at any dmv office",
                                                   "voter registration available at any dmv office",
                                                   "voter registration is available at any dmv",
                                                   "register to vote"])
    check_answer_any(judge, answer, "before_register", ["must first title", "first title your vehicle"])
    check_answer_count_at_least(judge, answer, "exam_exempt",
                                ["out-of-state license", "u.s. state", "canada", "germany",
                                 "france", "republic of korea"], 1)
    check_answer_number(judge, answer, "richmond_count", 6)
    check_answer_number(judge, answer, "richmond_csc_count", 5)
    check_answer_regex(judge, answer, "confirmation_number", r"VADM\d{6}-[A-F0-9]{6}")
    check_answer_regex(judge, answer, "booked_time", r"\d{1,2}:\d{2} AM")
    check_answer_any(judge, answer, "booked_date", ["2026-10-05", "october 5"])
    check_answer_any(judge, answer, "booked_service", ["vehicle registration / title",
                                                       "vehicle registration/title"])
    check_only_tables_changed(judge, initial, after, {"appointments"})
    check_rows_added(judge, initial, after, "appointments", [
        (None, "rx:^VADM\\d{6}-[A-F0-9]{6}$", None, "Alex Morgan", "alex.morgan@example.com",
         "richmond-central", "Vehicle Registration / Title", "2026-10-05",
         "rx:^\\d{1,2}:\\d{2} AM$", "Confirmed", "2026-09-29"),
    ], "appt_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
