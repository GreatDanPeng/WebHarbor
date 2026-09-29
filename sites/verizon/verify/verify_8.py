#!/usr/bin/env python3
"""Deterministic verifier for Verizon--8 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_8.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_number_absent, check_answer_ordered, check_answer_phrase,
    check_answer_regex, check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, db_one, final_answer, run_verifier,
)

TASK_ID = "Verizon--8"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")
    check_visited_path(judge, traj, "nav_stores", r"/stores/$")
    check_visited_path(judge, traj, "nav_wa", r"/stores/washington/$")
    check_visited_path(judge, traj, "nav_seattle", r"/stores/washington/seattle/$")
    check_visited_path(judge, traj, "nav_northgate_detail", r"/store/r00000151174/$")
    check_visited_path(judge, traj, "nav_appointment", r"/store/r00000151174/appointment")
    check_visited_path(judge, traj, "nav_appt_conf", r"/appointment/APT[0-9]+")

    # answer ground truth
    check_answer_money(judge, answer, "edge_good", 130.00)
    check_answer_phrase(judge, answer, "store_addr", "401 NE Northgate Way")
    check_answer_phrase(judge, answer, "store_sunday", "10:00 AM 06:00 PM")
    check_answer_phrase(judge, answer, "store_phone", "206-367-0687")
    row = db_one(after, "SELECT confirmation FROM appointments WHERE id = (SELECT MAX(id) FROM appointments)")
    check_answer_confirmation(judge, answer, "appt_confirmation", row[0] if row else None, "APT")
    check_answer_phrase(judge, answer, "appt_date", "2026-10-06")
    check_answer_phrase(judge, answer, "appt_time", "02:00 PM")
    check_answer_phrase(judge, answer, "appt_topic", "Device trade-in")
    check_answer_count_at_least(judge, answer, "appt_topics",
        ["New line & device purchase", "Device trade-in", "Billing & payments",
         "Technical support", "Fios / Home Internet"], 3)

    # DB after-state: exact allowed delta
    check_only_tables_changed(judge, initial, after, {"appointments"})
    check_rows_added(judge, initial, after, "appointments",
        [[None, 1, None, "Sam Rivera", "sam.rivera@example.com", "206-555-0139",
          "Device trade-in", "2026-10-06", "02:00 PM", "rx:^APT[0-9]{6}$",
          "confirmed"]], "appointment_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
