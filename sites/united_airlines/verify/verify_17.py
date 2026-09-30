#!/usr/bin/env python3
"""Deterministic verifier for United Airlines--17 (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_17.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "United Airlines--17"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the four Help Center articles.
    check_visited_path(judge, traj, "nav_checkin_article", r'/help/check-in-online')
    check_visited_path(judge, traj, "nav_sameday_article", r'/help/same-day-change')
    check_visited_path(judge, traj, "nav_award_article", r'/help/change-award')
    check_visited_path(judge, traj, "nav_epu_article", r'/help/economy-plus')
    # answer ground truth: online check-in opens 24 hours before and closes
    # 60 minutes before departure; same-day change up to $75 (free on
    # standby for Premier members); award redeposit after canceling is free
    # (no fee), no-show costs a nonrefundable $125 service fee; the lowest
    # Economy Plus price is $29 per flight. Deepened at 93a2638f: each of
    # the four answers must cite the exact title of its source article.
    check_answer_number(judge, answer, "checkin_open_hours", 24)
    check_answer_number(judge, answer, "checkin_close_minutes", 60)
    check_answer_money(judge, answer, "sameday_fee", 75)
    ok_standby = ("standby" in answer.lower()) and ("premier" in answer.lower())
    if ok_standby:
        judge.ok("standby_free", "free standby for Premier members")
    else:
        judge.fail("standby_free", "answer lacks the free-standby rule")
    ok_redeposit = ("redeposit" in answer.lower() or "deposit" in answer.lower()) and \
                   (("no fee" in answer.lower()) or ("free" in answer.lower()) or \
                    ("waived" in answer.lower()))
    if ok_redeposit:
        judge.ok("award_redeposit", "no redeposit fee after canceling")
    else:
        judge.fail("award_redeposit", "answer lacks the redeposit-fee answer")
    check_answer_money(judge, answer, "noshow_fee", 125)
    check_answer_money(judge, answer, "epu_lowest_price", 29)
    check_answer_phrase(judge, answer, "source_article_checkin",
                        "How early can I check in for my flight?")
    check_answer_phrase(judge, answer, "source_article_sameday",
                        "What is the same-day change option?")
    check_answer_phrase(judge, answer, "source_article_award",
                        "Can I get my miles back if I cancel an award flight?")
    check_answer_phrase(judge, answer, "source_article_epu",
                        "What is Economy Plus?")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
