#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--2 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_2.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--2"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_packages_calc", r"/postcalc/packages")
    check_answer_money(judge, answer, "pm_30lb_z8", 146.20)
    # r2 deepening (fix F-3): the task now asks for all four zone-based
    # services plus the Zone 4 re-price and the Flat Rate zone check.
    check_attributed_money(judge, answer, "pme_30lb_z8",
                           "Priority Mail Express", 289.10)
    check_attributed_money(judge, answer, "ga_30lb_z8",
                           "Ground Advantage", 112.80)
    check_attributed_money(judge, answer, "mm_30lb", "Media Mail", 25.76)
    check_answer_money(judge, answer, "large_frb", 34.00)
    check_answer_money(judge, answer, "small_frb", 13.65)
    check_answer_phrase(judge, answer, "cheaper_option", "Large Flat Rate Box")
    check_answer_money(judge, answer, "pm_30lb_z4", 63.65)
    check_answer_any(judge, answer, "frb_zone_unchanged", [
        "do not change", "did not change", "not change", "unchanged",
        "same", "stay", "stays"])
    # audit deepening (ordinal 57): Media Mail rules from the Send Mail &
    # Packages page and the free Flat Rate box from the Postal Store.
    check_visited_path(judge, traj, "nav_mail_services",
                       r"/ship/mail-shipping-services")
    check_visited_path(judge, traj, "nav_supplies",
                       r"/store/shipping-supplies-priority-mail")
    check_answer_number(judge, answer, "mm_max_weight", 70)
    check_answer_phrase(judge, answer, "video_games", "do not qualify")
    check_answer_money(judge, answer, "medium_frb_store", 0.00)
    check_answer_money(judge, answer, "mm_70lb", 55.23)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
