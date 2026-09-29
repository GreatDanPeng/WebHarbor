#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--15 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_15.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--15"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_countries", r"/international/countries")
    check_visited_path(judge, traj, "nav_japan", r"/international/countries/japan")
    check_visited_path(judge, traj, "nav_intl_calc", r"/postcalc/international")
    check_answer_count_at_least(judge, answer, "prohibitions",
                                ["ammunition", "firearms", "hoverboards",
                                 "infectious substances", "narcotics",
                                 "radioactive materials"], 3)
    check_answer_phrase(judge, answer, "customs_form", "PS Form 2976")
    check_answer_number(judge, answer, "pmi_group", 17)
    check_answer_money(judge, answer, "pmi_4lb", 78.50)
    check_answer_money(judge, answer, "pmei_4lb", 108.45)
    # r2 deepening (fix F-3): PMI/FCPIS weight limits for Japan, and
    # Germany's PMI price group cross-check.
    check_answer_phrase(judge, answer, "pmi_weight_limit", "66 lbs")
    check_answer_phrase(judge, answer, "fcpis_weight_limit", "4 lbs")
    check_answer_number(judge, answer, "germany_group", 16)
    # audit deepening (ordinal 57): Canada's PMI price group for the
    # group comparison.
    check_visited_path(judge, traj, "nav_canada",
                       r"/international/countries/canada")
    check_answer_number(judge, answer, "canada_pmi_group", 1)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
