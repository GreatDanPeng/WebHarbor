#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--9 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_9.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_any, check_visited_path,
    final_answer, run_verifier,
)

TASK_ID = "CBP.gov--9"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_forms", r"/newsroom/publications/forms")
    check_visited_path(judge, traj, "nav_7501_search", r"/newsroom/publications/forms\?.*q=[^#]*7501")
    check_visited_path(judge, traj, "nav_7501_detail",
                       r"/newsroom/publications/forms/7501-entry-summary-with-continuation-sheets")
    check_visited_path(judge, traj, "nav_form19",
                       r"/newsroom/publications/forms/19$")
    check_answer_number(judge, answer, "total_forms", 97)
    check_answer_phrase(judge, answer, "form7501_title", "Entry Summary with Continuation Sheets")
    check_answer_phrase(judge, answer, "form7501_date", "Feb 11 2026")
    check_answer_phrase(judge, answer, "form7501_sha", "87046018fbd6ca62")
    check_answer_phrase(judge, answer, "form19_name", "Protest")
    check_answer_phrase(judge, answer, "form19_date", "May 1 2024")
    # newest listed date: Sep 14 2026 — a documented tie between 1304 and 4609
    check_answer_any(judge, answer, "newest_form",
                     [("1304"), ("4609")])
    check_answer_any(judge, answer, "newest_title",
                     ["Crew Effects Declarations",
                      "Petition for Remission or Mitigation"])
    check_answer_number(judge, answer, "declaration_matches", 13)
    check_answer_phrase(judge, answer, "customs_declaration_form", "6059B")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
