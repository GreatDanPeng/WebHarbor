#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--14 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_14.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--14"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: carol's account page + MileagePlus program page.
    check_visited_path(judge, traj, "nav_signin", r'/signin')
    check_visited_path(judge, traj, "nav_account", r'/account')
    check_visited_path(judge, traj, "nav_program", r'/mileageplus')
    # answer ground truth: PQF 2 / PQP 640; Premier Silver needs 12 PQF +
    # 4,000 PQP (or 5,000 PQP only) — the account page and the program page
    # state the same thresholds; deepened at 93a2638f: she still needs
    # 10 more PQF and 3,360 more PQP for Silver; Premier 1K earns 11 miles
    # per dollar.
    check_answer_number(judge, answer, "current_pqf", 2)
    check_answer_number(judge, answer, "current_pqp", 640)
    check_answer_number(judge, answer, "silver_pqf", 12)
    check_answer_number(judge, answer, "silver_pqp", 4000)
    check_answer_number(judge, answer, "silver_pqp_only", 5000)
    check_answer_number(judge, answer, "onek_earn_rate", 11)
    check_answer_number(judge, answer, "remaining_pqf", 10)
    check_answer_number(judge, answer, "remaining_pqp", 3360)
    import re as _re
    agree_rx = _re.compile(r'\b(agree[ds]?|the same|same on both|consistent|'
                            r'match(es|ed)?|identical)\b', _re.I)
    if agree_rx.search(answer):
        judge.ok("thresholds_agree", agree_rx.search(answer).group(0))
    else:
        judge.fail("thresholds_agree",
                   "answer must state whether the two pages' thresholds agree")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
