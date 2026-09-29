#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--12 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_12.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--12"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the news releases list page two, the four releases, the
    # glossary Refugee and Asylum searches.
    check_visited_path(judge, traj, "nav_releases", r"/newsroom/news-releases")
    check_visited_path(judge, traj, "nav_page2", r"/newsroom/news-releases\?[^ ]*page=2")
    check_visited_path(judge, traj, "nav_r1",
                       r"/newsroom/news-releases/bosnian-prisoner-abuser-charged-with-lying-to-get-us-citizenship")
    check_visited_path(judge, traj, "nav_r2",
                       r"/newsroom/news-releases/chinese-aliens-indicted-on-naturalization-and-firearms-charges")
    check_visited_path(judge, traj, "nav_r3",
                       r"/newsroom/news-releases/cuban-alien-convicted-for-international-alien-smuggling-and-money-laundering-conspiracy")
    check_visited_path(judge, traj, "nav_r4",
                       r"/newsroom/news-releases/aunt-and-us-airman-nephew-arrested-in-immigration-fraud-scheme")
    check_visited_path(judge, traj, "nav_glossary_refugee", r"/tools/glossary\?[^ ]*q=Refugee")
    check_visited_path(judge, traj, "nav_glossary_asylum", r"/tools/glossary\?[^ ]*q=Asylum")
    # answer ground truth
    check_answer_phrase(judge, answer, "release_date", "09/22/2026")
    check_answer_phrase(judge, answer, "city", "BOISE")
    check_answer_phrase(judge, answer, "defendant", "Miran Kostic")
    check_answer_phrase(judge, answer, "former_role", "Autonomous Province of Western Bosnia")
    check_answer_phrase(judge, answer, "charge_1", "attempted naturalization fraud")
    check_answer_phrase(judge, answer, "charge_1_term", "10 years")
    check_answer_phrase(judge, answer, "charge_2", "false statements")
    check_answer_phrase(judge, answer, "charge_2_term", "five years")
    check_answer_phrase(judge, answer, "agencies", "Homeland Security Investigations")
    check_answer_phrase(judge, answer, "agencies2", "FBI")
    check_answer_phrase(judge, answer, "c2_city", "ST. LOUIS")
    check_answer_phrase(judge, answer, "c2_huang_charges", "false statement in a naturalization proceeding")
    check_answer_phrase(judge, answer, "c2_huang_charges2", "fraudulent acquisition of a firearm")
    check_answer_phrase(judge, answer, "c2_du_charge", "alien in possession of a firearm")
    check_answer_phrase(judge, answer, "r3_date", "09/28/2026")
    check_answer_phrase(judge, answer, "r3_defendant", "Cabrera-Rodriguez")
    check_answer_phrase(judge, answer, "r3_penalty", "20 years")
    check_answer_phrase(judge, answer, "r4_date", "09/02/2026")
    check_answer_phrase(judge, answer, "r4_city", "KANSAS CITY")
    check_answer_number(judge, answer, "refugee_count", 8)
    check_answer_number(judge, answer, "asylum_count", 3)
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
