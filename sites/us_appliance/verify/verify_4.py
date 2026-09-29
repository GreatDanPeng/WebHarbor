#!/usr/bin/env python3
"""Deterministic verifier for USAppliance--4 (us_appliance).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-appliance-review, seed md5
d0c844383f9ed997c8de508c00196de3) — never read from tasks.jsonl.
Usage: python3 verify_4.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "USAppliance--4"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: login, account, the delivered order detail, and (r2) the
    # shipped order detail.
    check_visited_path(judge, traj, "nav_login", r"/login\.php")
    check_visited_path(judge, traj, "nav_account", r"/account\.php")
    check_visited_path(judge, traj, "nav_order_detail", r"/account\.php/orders/1")
    check_visited_path(judge, traj, "nav_shipped_order", r"/account\.php/orders/2")
    # answer ground truth
    check_answer_number(judge, answer, "orders_in_history", 2)
    check_answer_phrase(judge, answer, "status_delivered", "Delivered")
    check_answer_phrase(judge, answer, "status_shipped", "Shipped")
    check_answer_phrase(judge, answer, "delivery_method", "In-Home Delivery")
    check_answer_phrase(judge, answer, "carrier", "R+L Carriers")
    check_answer_phrase(judge, answer, "tracking_number", "RL774912")
    check_answer_number(judge, answer, "timeline_events", 6)
    check_answer_money(judge, answer, "order_total", 2289.32)
    check_answer_number(judge, answer, "line_items", 2)
    # r2 deepening: the shipped order (10002) as well.
    check_answer_phrase(judge, answer, "shipped_carrier", "Maersk")
    check_answer_phrase(judge, answer, "shipped_tracking", "MN-88231340")
    check_answer_phrase(judge, answer, "shipped_eta", "Oct 6, 2026")
    check_answer_number(judge, answer, "shipped_timeline_events", 3)
    # audit-rail deepening: track the shipped order (10002) on the public
    # tracking page and open the FAQ's order-tracking question.
    check_visited_path(judge, traj, "nav_tracking", r"/ordertracking\.html")
    check_visited_path(judge, traj, "nav_faq", r"/faq\.html")
    check_answer_phrase(judge, answer, "track_10002_status", "Shipped")
    check_answer_phrase(judge, answer, "track_10002_latest_event",
                        "Shipped via Maersk. Tracking # MN-88231340")
    check_answer_count_at_least(judge, answer, "faq_tracking_answer",
                                ["we will send you tracking information",
                                 "visit our Order Tracking Page",
                                 "call us toll-free at (877) 628-9913"], 2)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
