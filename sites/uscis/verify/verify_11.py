#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--11 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_11.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--11"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the alerts list, the four alerts, page two of the alerts,
    # the all-news list, the glossary H-1B search.
    check_visited_path(judge, traj, "nav_alerts", r"/newsroom/alerts")
    check_visited_path(judge, traj, "nav_a1",
                       r"/newsroom/alerts/uscis-reaches-h-2b-cap-for-first-half-of-fy-2027")
    check_visited_path(judge, traj, "nav_a2",
                       r"/newsroom/alerts/uscis-reaches-h-2b-cap-for-second-half-of-fy-2026")
    check_visited_path(judge, traj, "nav_a3",
                       r"/newsroom/alerts/uscis-reaches-fiscal-year-2027-h-1b-cap")
    check_visited_path(judge, traj, "nav_page2", r"/newsroom/alerts\?[^ ]*page=2")
    check_visited_path(judge, traj, "nav_a4",
                       r"/newsroom/alerts/court-order-on-diversity-immigrant-visa-program-hold-policy")
    check_visited_path(judge, traj, "nav_allnews", r"/newsroom/all-news")
    check_visited_path(judge, traj, "nav_glossary", r"/tools/glossary\?[^ ]*q=H-1B")
    # answer ground truth
    check_answer_phrase(judge, answer, "a1_pub_date", "09/11/2026")
    check_answer_phrase(judge, answer, "a1_final_receipt_date", "Sept. 4, 2026")
    check_answer_phrase(judge, answer, "a1_start_date", "April 1, 2027")
    check_answer_phrase(judge, answer, "a1_after_receipt",
                        "reject new cap-subject H-2B petitions received after Sept. 4, 2026")
    check_answer_phrase(judge, answer, "a1_fraud_invite", "online tip form")
    check_answer_phrase(judge, answer, "a2_pub_date", "03/20/2026")
    check_answer_phrase(judge, answer, "a2_final_receipt_date", "March 10, 2026")
    check_answer_phrase(judge, answer, "a3_pub_date", "07/17/2026")
    check_answer_phrase(judge, answer, "a3_cap_regular", "65,000")
    check_answer_phrase(judge, answer, "a3_cap_adv", "20,000")
    check_answer_phrase(judge, answer, "a4_pub_date", "09/04/2026")
    check_answer_phrase(judge, answer, "a4_order", "PM-602-0193")
    check_answer_number(judge, answer, "allnews_count", 60)
    check_answer_number(judge, answer, "glossary_count", 5)
    check_answer_phrase(judge, answer, "glossary_first", "Cap-gap extension")
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
