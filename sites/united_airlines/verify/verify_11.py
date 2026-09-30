#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--11 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_11.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--11"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the checked bag fee calculator.
    check_visited_path(judge, traj, "nav_calculator", r'/baggage/fee-calculator')
    # answer ground truth (calculator output, frozen):
    #   Member / Economy / ORD-DEN / 2 bags: $35 + $45 = $80 online,
    #   $40 + $50 = $90 at the airport; weight 50 lb.
    #   Premier Gold / United Business / LHR-DEN / 2 bags online: the
    #   calculator prices $35 + $45 = $80 with a free-bags note (Gold in
    #   Economy gets 2 free bags); weight 70 lb. Both the calculator fees
    #   and the free-allowance reading are defensible for scenario 2.
    check_answer_money(judge, answer, "s1_bag1_online", 35)
    check_answer_money(judge, answer, "s1_bag2_online", 45)
    check_answer_money(judge, answer, "s1_online_total", 80)
    check_answer_money(judge, answer, "s1_bag1_airport", 40)
    check_answer_money(judge, answer, "s1_bag2_airport", 50)
    check_answer_money(judge, answer, "s1_airport_total", 90)
    ok_s2 = ("80" in answer) or ("free" in answer.lower()) or ("$0" in answer)
    if ok_s2:
        judge.ok("s2_fees", "$80 calculator price or free-allowance reading")
    else:
        judge.fail("s2_fees", "answer lacks scenario-2 fees ($80 or free)")
    check_answer_number(judge, answer, "member_weight_limit", 50)
    check_answer_number(judge, answer, "gold_weight_limit", 70)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
