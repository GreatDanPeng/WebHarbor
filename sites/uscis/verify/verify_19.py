#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--19 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_19.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--19"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the I-765 details page, the fee calculator I-765 record,
    # the processing-times tool I-765 NBC record, Case Status Online, the
    # While My Case is Pending page, the glossary EAD search.
    check_visited_path(judge, traj, "nav_i765", r"/i-765")
    check_visited_path(judge, traj, "nav_feecalculator",
                       r"/feecalculator\?[^ ]*form=97312")
    check_visited_path(judge, traj, "nav_pt",
                       r"/processing-times\?[^ ]*form=I-765[^ ]*office=NBC")
    check_visited_path(judge, traj, "nav_casestatus", r"/casestatus")
    check_visited_path(judge, traj, "nav_pending", r"/tools/while-my-case-is-pending")
    check_visited_path(judge, traj, "nav_glossary",
                       r"/tools/glossary\?[^ ]*q=Employment")
    # answer ground truth
    check_answer_any(judge, answer, "edition_date", ["08/21/25", "August 21, 2025"])
    check_answer_count_at_least(judge, answer, "pdfs",
                                ["Form I-765", "Instructions for Form I-765",
                                 "Form I-765 Worksheet",
                                 "i-765.pdf", "i-765instr.pdf", "i-765ws.pdf"], 3)
    check_answer_money(judge, answer, "paper_fee", 520)
    check_answer_money(judge, answer, "online_fee", 470)
    check_answer_money(judge, answer, "pending_i485_fee", 260)
    check_answer_phrase(judge, answer, "nbc_pub", "May 31, 2018")
    check_answer_phrase(judge, answer, "nbc_c9_range", "6 Months to 4 Months")
    check_answer_ordered(judge, answer, "ordered_tools",
                         ["Check your case status",
                          "Check case processing times",
                          "Ask about a case taking longer than expected",
                          "Update your mailing address",
                          "Ask about missing mail",
                          "Correct a typographical error",
                          "Request appointment accommodations"])
    check_answer_phrase(judge, answer, "ead_term",
                        "Employment Authorization Document (Form I-766/EAD)")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
