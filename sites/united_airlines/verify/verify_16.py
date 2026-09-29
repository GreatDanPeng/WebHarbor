#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--16 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_16.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--16"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: both fleet pages.
    check_visited_path(judge, traj, "nav_78p", r'/travel-info/fleet/78P')
    check_visited_path(judge, traj, "nav_77x", r'/travel-info/fleet/77X')
    # answer ground truth (re-frozen at r2 from the 93a2638f site, seed md5
    # 3a04d306...; fleet data):
    #   787-9: total seat rows 37 (12 Polaris / 3 Premium Plus / 5 Economy
    #     Plus / 17 Economy), seats 48 / 21 / 39 / 149, Wi-Fi Panasonic,
    #     cruise 560 mph, wingspan 197 ft 4 in,
    #     engines General Electric GEnx-1B76 x2, thrust 76,100 lbf.
    #   777-300ER: total seat rows 46 (15 / 3 / 7 / 21), seats 60 / 24 / 62 /
    #     204, Wi-Fi Panasonic, cruise 557 mph, wingspan 212 ft 7 in,
    #     engines General Electric GE90-115B x2, thrust 115,300 lbf.
    check_answer_number(judge, answer, "ua789_seat_rows", 37)
    check_answer_number(judge, answer, "ua789_polaris_rows", 12)
    check_answer_number(judge, answer, "ua789_pp_rows", 3)
    check_answer_number(judge, answer, "ua789_epu_rows", 5)
    check_answer_count_at_least(judge, answer, "ua789_seats",
                                ["48", "21", "39", "149"], 4)
    check_answer_phrase(judge, answer, "ua789_wifi", "Panasonic")
    check_answer_number(judge, answer, "ua789_cruise", 560)
    ok_789_wing = ("197 ft 4 in" in answer) or ("197ft4in" in answer.replace(" ", ""))
    if ok_789_wing:
        judge.ok("ua789_wingspan", "197 ft 4 in")
    else:
        judge.fail("ua789_wingspan", "answer lacks the 787-9 wingspan")
    ok_789_eng = ("GEnx" in answer)
    if ok_789_eng:
        judge.ok("ua789_engine", "General Electric GEnx-1B76")
    else:
        judge.fail("ua789_engine", "answer lacks the 787-9 engine")
    check_answer_number(judge, answer, "b77w_seat_rows", 46)
    check_answer_number(judge, answer, "b77w_polaris_rows", 15)
    check_answer_number(judge, answer, "b77w_pp_rows", 3)
    check_answer_number(judge, answer, "b77w_epu_rows", 7)
    check_answer_count_at_least(judge, answer, "b77w_seats",
                                ["60", "24", "62", "204"], 4)
    check_answer_phrase(judge, answer, "b77w_wifi", "Panasonic")
    check_answer_number(judge, answer, "b77w_cruise", 557)
    ok_77w_wing = ("212 ft 7 in" in answer) or ("212ft7in" in answer.replace(" ", ""))
    if ok_77w_wing:
        judge.ok("b77w_wingspan", "212 ft 7 in")
    else:
        judge.fail("b77w_wingspan", "answer lacks the 777-300ER wingspan")
    ok_77w_eng = ("GE90" in answer)
    if ok_77w_eng:
        judge.ok("b77w_engine", "General Electric GE90-115B")
    else:
        judge.fail("b77w_engine", "answer lacks the 777-300ER engine")
    check_answer_number(judge, answer, "b77w_thrust", 115300)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
