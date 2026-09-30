#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--5 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_5.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--5"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the All Forms catalog, the I-485 and I-693 details pages,
    # and the fee calculator for I-485, G-1450, G-1650 (I-693 fee read there).
    check_visited_path(judge, traj, "nav_forms", r"/forms\?[^ ]*q=I-485")
    check_visited_path(judge, traj, "nav_i485", r"/i-485")
    check_visited_path(judge, traj, "nav_i693", r"/i-693")
    for nid, name in (("97286", "i485"), ("97255", "g1450"), ("99832", "g1650")):
        check_visited_path(judge, traj, f"nav_fee_{name}",
                           rf"/feecalculator\?[^ ]*form={nid}")
    # answer ground truth
    check_answer_any(judge, answer, "edition_date", ["09/18/26"])
    check_answer_count_at_least(judge, answer, "pdfs",
                                ["Form I-485", "Instructions for Form I-485",
                                 "i-485.pdf", "i-485instr.pdf"], 2)
    check_answer_any(judge, answer, "i693_edition", ["01/20/25"])
    check_answer_count_at_least(judge, answer, "i693_pdfs",
                                ["Form I-693", "Instructions for Form I-693"], 2)
    check_answer_number(judge, answer, "i693_fee", 0)
    check_answer_money(judge, answer, "general_paper", 1440)
    check_answer_money(judge, answer, "general_online", 1390)
    check_answer_money(judge, answer, "under14_paper", 950)
    check_answer_number(judge, answer, "zero_categories", 11)
    check_answer_count_at_least(judge, answer, "zero_conditions",
                                ["served honorably on active duty",
                                 "refugee or you were paroled as a refugee",
                                 "deportation, exclusion, or removal proceedings",
                                 "Special Immigrant Juvenile"], 4)
    check_answer_any(judge, answer, "payment_forms", ["G-1450"])
    check_answer_any(judge, answer, "payment_forms2", ["G-1650"])
    check_answer_number(judge, answer, "g1450_fee", 0)
    check_answer_number(judge, answer, "g1650_fee", 0)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
