#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--4 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_4.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--4"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the All Forms catalog search, the I-131 details page, and
    # the fee calculator for the five travel-document categories.
    check_visited_path(judge, traj, "nav_forms", r"/forms\?[^ ]*q=travel")
    check_visited_path(judge, traj, "nav_i131", r"/i-131")
    for nid, name in (("99067", "ap"), ("99064", "rp"), ("99065", "refugee"),
                      ("99066", "tps"), ("99068", "cnmi")):
        check_visited_path(judge, traj, f"nav_fee_{name}",
                           rf"/feecalculator\?[^ ]*form={nid}")
    # answer ground truth
    check_answer_any(judge, answer, "form_number", ["I-131"])
    check_answer_any(judge, answer, "edition_date", ["01/20/25", "January 20, 2025"])
    check_answer_count_at_least(judge, answer, "pdfs",
                                ["Form I-131", "Instructions for Form I-131",
                                 "i-131.pdf", "i-131instr.pdf"], 2)
    check_answer_money(judge, answer, "ap_paper", 630)
    check_answer_money(judge, answer, "ap_online", 580)
    check_answer_money(judge, answer, "rp_fee", 630)
    check_answer_phrase(judge, answer, "rp_waiver", "Not eligible for a Fee Waiver request")
    check_answer_number(judge, answer, "refugee_fee", 0)
    check_answer_money(judge, answer, "tps_paper", 630)
    check_answer_money(judge, answer, "tps_online", 580)
    check_answer_money(judge, answer, "cnmi_fee", 630)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
