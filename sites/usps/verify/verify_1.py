#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--1 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_1.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--1"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_postcalc", r"/postcalc/")
    check_visited_path(judge, traj, "nav_packages_calc", r"/postcalc/packages")
    check_attributed_money(judge, answer, "ga_8lb_z4", "Ground Advantage", 17.65)
    check_attributed_money(judge, answer, "pm_8lb_z4", "Priority Mail", 19.70)
    check_attributed_money(judge, answer, "pme_8lb_z4", "Priority Mail Express", 87.55)
    check_attributed_money(judge, answer, "mm_8lb", "Media Mail", 9.55)
    check_answer_phrase(judge, answer, "cheapest", "USPS Ground Advantage")
    check_answer_any(judge, answer, "mm_candles", [
        "not allowed", "cannot", "can't", "only books", "books and media",
        "media only", "isn't allowed", "no —", "No,"])
    # r2 deepening (fix F-3): Zone 8 re-price cross-check.
    check_answer_money(judge, answer, "pm_8lb_z8", 51.70)
    check_answer_money(judge, answer, "z8_minus_z4", 32.00)
    check_answer_any(judge, answer, "fr_unchanged", [
        "do not change", "did not change", "not change", "unchanged",
        "same", "stay", "stays"])
    # audit deepening (ordinal 57): Priority Mail / Ground Advantage
    # service pages (the rendering-layer sanitizer now exposes their text).
    check_visited_path(judge, traj, "nav_pm_page", r"/ship/priority-mail")
    check_visited_path(judge, traj, "nav_ga_page", r"/ship/ground-advantage")
    check_answer_money(judge, answer, "pm_page_fr_envelope", 12.90)
    check_answer_number(judge, answer, "pm_page_insurance", 100)
    check_answer_any(judge, answer, "ga_delivery_window", [
        "2-5 days", "2–5 days"])
    check_answer_money(judge, answer, "pm_2lb_z4", 14.35)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
