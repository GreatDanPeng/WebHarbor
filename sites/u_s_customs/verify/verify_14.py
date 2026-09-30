#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--14 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_14.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--14"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_events", r"/careers/events")
    check_visited_path(judge, traj, "nav_ofo", r"/careers/career-paths/ofo")
    check_answer_number(judge, answer, "total_events", 4)
    check_answer_phrase(judge, answer, "waco_city", "Waco")
    check_answer_phrase(judge, answer, "waco_name", "Waco's Fall Hiring Fair")
    check_answer_phrase(judge, answer, "waco_date", "Sep 28, 2026")
    check_answer_phrase(judge, answer, "waco_type", "In Person Live Event")
    check_answer_phrase(judge, answer, "dallas_date", "Sep 29, 2026")
    check_answer_phrase(judge, answer, "dallas_location", "Addison")
    check_answer_phrase(judge, answer, "webinar_name", "OFO CBPO Recruitment Webinar")
    check_answer_phrase(judge, answer, "webinar_type", "Online")
    check_answer_count_at_least(judge, answer, "ofo_titles",
                                ["CBP Officer", "Customs and Border Protection Officer"], 1)
    check_answer_count_at_least(judge, answer, "in_person_events",
                                ["Waco", "Dallas", "Tulare"], 3)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
