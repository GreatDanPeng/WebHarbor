#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--6 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_6.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_phrase, check_read_only, check_rows_added,
    check_rows_changed, check_only_tables_changed, check_screenshots,
    check_seed_contract, check_trajectory_identity, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "United Airlines--6"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: My Trips lookup KX42LM, add the next bag, seat map.
    check_visited_path(judge, traj, "nav_mytrips", r'/mytrips')
    check_visited_path(judge, traj, "nav_trip", r'/mytrips/KX42LM')
    check_visited_path(judge, traj, "nav_seatmap", r'/mytrips/KX42LM/seats/1')
    # answer ground truth: Premier Silver = 1 free bag on this trip; the
    # trip already carries one free bag, so the NEXT (second) bag costs $35
    # online — the task (reworded at 93a2638f) asks for "the fee charged for
    # the added bag", an unambiguous $35 anchor; the standard (non-Economy
    # Plus) window/aisle seat is any seat in the 787-8 Economy band, now
    # rows 15-32 (widened from 15-20 by the interior-spec fix).
    check_answer_number(judge, answer, "free_bags", 1)
    check_answer_money(judge, answer, "bag_fee", 35)
    import re as _re
    seat_rx = _re.compile(r'\b(1[5-9]|2[0-9]|3[0-2])[A-K]\b')
    if seat_rx.search(answer):
        judge.ok("seat", seat_rx.search(answer).group(0))
    else:
        judge.fail("seat", "answer lacks a standard seat 15A-32K")
    check_only_tables_changed(judge, initial, after, {"baggage_items", "passengers"})
    check_rows_added(judge, initial, after, "baggage_items",
                    [[None, 1, 1, "Checked bag 2", 0, 35.0]], "bag_row")
    check_rows_changed(judge, initial, after, "passengers",
                       [[1, 1, "Alice", "Johnson", None, None, None,
                         "8511174410", "rx:^(1[5-9]|2[0-9]|3[0-2])[A-K]$", 0, ""]],
                       "seat_row")

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
