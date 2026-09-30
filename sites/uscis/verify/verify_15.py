#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--15 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_15.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_any, check_answer_count_at_least, check_answer_money,
    check_answer_number, check_answer_ordered, check_answer_phrase,
    check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "USCIS.gov--15"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the glossary searches for the three terms, 'adjustment',
    # Asylee, and the letter-A index.
    for term in ("Adjustment", "Advance", "Biometrics"):
        check_visited_path(judge, traj, "nav_glossary_" + term.split()[0],
                           rf"/tools/glossary\?[^ ]*q={term}")
    check_visited_path(judge, traj, "nav_glossary_adjustment",
                       r"/tools/glossary\?[^ ]*q=adjustment")
    check_visited_path(judge, traj, "nav_glossary_asylee",
                       r"/tools/glossary\?[^ ]*q=Asylee")
    check_visited_path(judge, traj, "nav_letter_a", r"/tools/glossary\?[^ ]*letter=A")
    # answer ground truth
    check_answer_phrase(judge, answer, "aos_def",
                        "apply for lawful permanent resident status")
    check_answer_phrase(judge, answer, "ap_def",
                        "travel back to the United States without applying for a visa")
    check_answer_phrase(judge, answer, "bio_def",
                        "fingerprints, photograph")
    check_answer_number(judge, answer, "adjustment_count", 5)
    check_answer_phrase(judge, answer, "a_term_1", "Adjustment of Status")
    check_answer_phrase(judge, answer, "a_term_2", "Adjustment to immigrant status")
    check_answer_number(judge, answer, "letter_a_count", 28)
    check_answer_phrase(judge, answer, "asylee_def",
                        "unable or unwilling to return to their country of nationality")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
