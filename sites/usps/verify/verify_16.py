#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--16 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_16.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--16"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_intl_calc", r"/postcalc/international")
    check_visited_path(judge, traj, "nav_germany", r"/international/countries/germany")
    check_answer_money(judge, answer, "ca_fcpis", 29.05)
    check_answer_money(judge, answer, "ca_pmi", 47.05)
    check_answer_money(judge, answer, "de_fcpis", 32.85)
    check_answer_money(judge, answer, "de_pmi", 85.50)
    check_answer_any(judge, answer, "de_restriction", [
        "medicines", "phytosanitary", "import licenses", "meat and meat"])
    check_answer_number(judge, answer, "pmi_max_weight", 70)
    # audit deepening (ordinal 57): the 4-pound Germany re-price and the
    # Canada country listing.
    check_answer_money(judge, answer, "de4_pmi", 94.65)
    check_answer_money(judge, answer, "de4_pmei", 118.00)
    check_visited_path(judge, traj, "nav_canada",
                       r"/international/countries/canada")
    check_answer_number(judge, answer, "canada_pmi_group", 1)
    check_answer_number(judge, answer, "canada_pmi_max", 66)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
