#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--18 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_18.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--18"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_postcalc", r"/postcalc/")
    check_visited_path(judge, traj, "nav_extra_services", r"/postcalc/extra-services")
    check_visited_path(judge, traj, "nav_claims_help", r"/help/claims")
    # r2 deepening (fix F-3): base postage for a 1-lb Zone 4 package, the
    # $100.01-$200 insurance band, Registered Mail for the $280 coin, the
    # COD $200.01-$300 fee, and the File a Claim cross-page insurance check.
    check_answer_money(judge, answer, "base_pm_1lb_z4", 11.90)
    check_answer_money(judge, answer, "insurance_200_300", 4.55)
    check_answer_money(judge, answer, "insurance_100_200", 4.50)
    check_answer_money(judge, answer, "registered_coin", 25.00)
    check_answer_money(judge, answer, "certified", 5.55)
    check_answer_money(judge, answer, "return_receipt", 4.65)
    check_answer_money(judge, answer, "signature", 5.15)
    check_answer_money(judge, answer, "cod_200_300", 24.80)
    check_answer_money(judge, answer, "total_four", 19.90)
    check_answer_money(judge, answer, "claims_page_insurance", 4.55)
    check_answer_number(judge, answer, "filing_deadline", 60)
    # audit deepening (ordinal 57): Priority Mail service page values.
    check_visited_path(judge, traj, "nav_pm_page", r"/ship/priority-mail")
    check_answer_money(judge, answer, "pm_page_fr_envelope", 12.90)
    check_answer_number(judge, answer, "pm_page_insurance", 100)
    check_answer_money(judge, answer, "pme_page_fr_envelope", 35.90)
    check_visited_path(judge, traj, "nav_pme_page",
                       r"/ship/priority-mail-express")
    # audit deepening (ordinal 57): Zone 8 + 2-pound re-prices.
    check_answer_money(judge, answer, "pm_1lb_z8", 16.95)
    check_answer_money(judge, answer, "pm_2lb_z4", 14.35)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
