#!/usr/bin/env python3
"""Deterministic verifier for Verizon--15 (verizon).

Ground truth below is HARDCODED (frozen from the reviewer's two independent
Playwright rounds on the review container wh-verizon-r2review, seed md5
f2d20153c24b6945fb5203b81d7f1fb6) — never read from tasks.jsonl.
Navigation gates cover ONLY the surfaces the task text requires (no
unrequired filters/sorts/detail pages); answer anchors are page-verbatim
with tolerance for equally-honest renderings.
Usage: python3 verify_15.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "Verizon--15"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_support", r"/support/$")
    check_visited_path(judge, traj, "nav_return_policy", r"/support/return_policy/")
    check_visited_path(judge, traj, "nav_trade_in", r"/trade-in/$")
    check_visited_path(judge, traj, "nav_estimate", r"/trade-in/estimate")
    check_visited_path(judge, traj, "nav_contact_us", r"/support/contact_us/")
    check_visited_path(judge, traj, "nav_stores", r"/stores/$")
    check_visited_path(judge, traj, "nav_wa", r"/stores/washington/$")
    check_visited_path(judge, traj, "nav_tacoma", r"/stores/washington/tacoma/$")
    check_visited_path(judge, traj, "nav_tacoma_detail", r"/store/r00000002096/$")

    # answer ground truth
    check_answer_money(judge, answer, "restocking_fee", 50.00)
    check_answer_phrase(judge, answer, "excluded_state", "Hawaii")
    check_answer_number(judge, answer, "return_window", 30)
    check_answer_phrase(judge, answer, "exchanges", "one exchange")
    check_answer_phrase(judge, answer, "condition", "like-new condition")
    check_answer_regex(judge, answer, "after_window",
        r"will not receive a refund|no refund")
    check_answer_regex(judge, answer, "retailer_rule",
        r"[Aa]uthorized [Rr]etailer[^.]{0,120}(own return/exchange policy|return/exchange policy)|own return/exchange policy")
    check_answer_phrase(judge, answer, "gift_section", "Gift card returns")
    check_answer_phrase(judge, answer, "term_section", "Standard monthly account service termination")
    check_answer_money(judge, answer, "s26_cracked", 120.00)
    check_answer_money(judge, answer, "px10a_good", 160.00)
    check_answer_phrase(judge, answer, "sales_number", "800-225-5499")
    check_answer_any(judge, answer, "sales_hours",
        ["8 AM - 10 PM ET (Mon - Sat)", "9 AM - 10 PM ET (Sun)"])
    check_answer_count_at_least(judge, answer, "billing_hours",
        ["8 AM - 7 PM PDT (Mon - Sat)", "8 AM - 5 PM PDT (Sun)",
         "8 AM - 7 PM ET (Mon - Fri)"], 2)
    check_answer_phrase(judge, answer, "tacoma_addr", "4009 Tacoma Mall Blvd")
    check_answer_phrase(judge, answer, "tacoma_sunday", "10:00 AM 06:00 PM")

    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
