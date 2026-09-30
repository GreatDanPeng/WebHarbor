#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--12 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_12.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--12"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: checked-bags, carry-on rule pages and the fee calculator.
    check_visited_path(judge, traj, "nav_checked", r'/baggage/checked-bags')
    check_visited_path(judge, traj, "nav_carryon", r'/baggage/carry-on')
    check_visited_path(judge, traj, "nav_calculator", r'/baggage/fee-calculator')
    # answer ground truth: 62 total linear inches (30x20x12), Economy 50 lb vs
    # Premier 70 lb, a 60-lb bag is overweight (51-70 lb) at $100, carry-on
    # 23x35x56 cm (9x14x22 in), personal item 22x25x43 cm, Basic Economy
    # domestic includes only a personal item (full carry-on on international);
    # deepened at 93a2638f: three checked bags prepaid online for one United
    # Economy traveler ORD->DEN price at $35 + $45 + $150 = $230 per the fee
    # calculator (weight limit 50 lb per bag).
    check_answer_number(judge, answer, "max_linear_inches", 62)
    check_answer_number(judge, answer, "economy_weight_lb", 50)
    check_answer_number(judge, answer, "premier_weight_lb", 70)
    check_answer_money(judge, answer, "sixty_lb_fee", 100)
    ok_carry = ("23 x 35 x 56" in answer) or ("23x35x56" in answer) or \
               ("9 x 14 x 22" in answer) or ("9x14x22" in answer) or \
               ("35 x 56" in answer)
    if ok_carry:
        judge.ok("carryon_size", "23 x 35 x 56 cm / 9 x 14 x 22 in")
    else:
        judge.fail("carryon_size", "answer lacks carry-on size limits")
    ok_personal = ("22 x 25 x 43" in answer) or ("22x25x43" in answer) or \
                  ("25 x 43" in answer)
    if ok_personal:
        judge.ok("personal_item_size", "22 x 25 x 43 cm")
    else:
        judge.fail("personal_item_size", "answer lacks personal item size")
    ok_be = ("personal item" in answer.lower())
    if ok_be:
        judge.ok("be_carryon", "Basic Economy includes a personal item")
    else:
        judge.fail("be_carryon", "answer lacks the Basic Economy carry-on rule")
    check_answer_money(judge, answer, "calc_bag1_fee", 35)
    check_answer_money(judge, answer, "calc_bag2_fee", 45)
    check_answer_money(judge, answer, "calc_bag3_fee", 150)
    check_answer_money(judge, answer, "calc_3bag_total", 230)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
