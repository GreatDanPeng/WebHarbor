#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--5 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_5.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_answer_regex, check_attributed_money, check_only_tables_changed,
    check_read_only, check_rows_added, check_screenshots,
    check_seed_contract, check_section_phrase, check_trajectory_identity,
    check_visited_any, check_visited_path, final_answer, run_verifier,
)

TASK_ID = "USPS.com--5"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_cns", r"/clicknship/create")
    check_visited_path(judge, traj, "nav_cns_step2", r"/clicknship/create\?step=2")
    check_visited_path(judge, traj, "nav_cns_step3", r"/clicknship/create\?step=3")
    check_visited_path(judge, traj, "nav_label", r"/clicknship/label")
    # task-as-written anchor: 4.2 lb Priority Mail, Zone 2 (PM retail $14.95)
    check_answer_money(judge, answer, "pm_base", 14.95)
    # insurance on $350 (band 300.01-400) = $6.05; Signature = $5.15
    check_answer_money(judge, answer, "total_paid", 26.15)
    check_answer_regex(judge, answer, "new_tracking", r"94\d{20}")
    check_answer_phrase(judge, answer, "expected_delivery", "October 1, 2026")
    check_only_tables_changed(judge, initial, after,
                              {"shipments", "scan_events"})
    # r2 truth-move #1 (fix F-7/F-8): the wizard now preserves the step-1
    # addresses on later POSTs and sets signature_required from the
    # Signature Confirmation checkbox, so the honest row carries
    # signature_required = 1 (sender/recipient stay None wildcards).
    check_rows_added(judge, initial, after, "shipments", [
        [None, r"rx:^94\d{20}$", 1, "pm", None, None, None, None, None,
         None, None, None, 4.2, "2026-09-28", "Shipping Label Created",
         "2026-10-01", None, 350.0, 1, None, 1, 26.15, 0, None,
         "2026-09-28"],
    ], "cns_shipment_added")
    check_rows_added(judge, initial, after, "scan_events", [
        [None, None, "2026-09-28 14:05", "Shipping Label Created",
         "label_created", None, 0],
    ], "cns_scan_added")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
