#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--15 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_15.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--15"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the four cabin pages + the 787-9 fleet page (Polaris pitch).
    check_visited_path(judge, traj, "nav_be", r'/travel-info/cabins/basic-economy')
    check_visited_path(judge, traj, "nav_epu", r'/travel-info/cabins/economy-plus')
    check_visited_path(judge, traj, "nav_pp", r'/travel-info/cabins/premium-plus')
    check_visited_path(judge, traj, "nav_polaris", r'/travel-info/cabins/united-polaris')
    check_visited_path(judge, traj, "nav_fleet_78p", r'/travel-info/fleet/78P')
    # answer ground truth:
    #   Basic Economy: personal item only domestic; full carry-on on
    #     international routes; no changes permitted.
    #   Economy Plus: from $29 per flight; free at booking for Premier Gold
    #     and above; free at check-in for Premier Silver.
    #   Premium Plus: 2 free checked bags at 70 lb.
    #   Polaris pitch (787-9): 6'6" (198 cm) lie-flat sleeping space.
    ok_be_carry = ("personal item" in answer.lower()) and \
                  (("international" in answer.lower()) or \
                   ("canada" in answer.lower()) or \
                   ("south america" in answer.lower()))
    if ok_be_carry:
        judge.ok("be_carryon_rules", "personal item + international carry-on")
    else:
        judge.fail("be_carryon_rules", "answer lacks the two carry-on rules")
    ok_be_change = ("no changes" in answer.lower()) or \
                   ("cannot be changed" in answer.lower()) or \
                   ("not changeable" in answer.lower())
    if ok_be_change:
        judge.ok("be_change_rule", "no changes permitted")
    else:
        judge.fail("be_change_rule", "answer lacks the Basic Economy change rule")
    check_answer_money(judge, answer, "epu_from_price", 29)
    ok_epu_free = ("gold" in answer.lower()) and ("silver" in answer.lower())
    if ok_epu_free:
        judge.ok("epu_free_for", "Gold+ at booking, Silver at check-in")
    else:
        judge.fail("epu_free_for", "answer lacks who gets Economy Plus free")
    check_answer_number(judge, answer, "pp_free_bags", 2)
    check_answer_number(judge, answer, "pp_bag_weight", 70)
    ok_pitch = ("6'6\"" in answer) or ("198 cm" in answer) or ("198cm" in answer)
    if ok_pitch:
        judge.ok("polaris_pitch", "6'6\" / 198 cm")
    else:
        judge.fail("polaris_pitch", "answer lacks the Polaris seat pitch")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
