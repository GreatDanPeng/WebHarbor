#!/usr/bin/env python3
"""Deterministic verifier for USCIS.gov--7 (uscis).

Ground truth below is HARDCODED (frozen from the auditor's independent
walkthroughs of the audit container wh-uscis-audit, seed md5
e3b7b4f99717af8145217556ecf8fd44) — never read from tasks.jsonl.
Usage: python3 verify_7.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USCIS.gov--7"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # navigation: the civil surgeon locator (22202 + Arabic/Female/Male
    # filters), the designated-civil-surgeons and vaccination pages, the fee
    # calculator I-693 record and the I-693 details page.
    check_visited_path(judge, traj, "nav_surgeon",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=22202")
    check_visited_path(judge, traj, "nav_surgeon_arabic",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=22202[^ ]*language=Arabic")
    check_visited_path(judge, traj, "nav_surgeon_female",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=22202[^ ]*gender=Female")
    check_visited_path(judge, traj, "nav_surgeon_male",
                       r"/tools/find-a-civil-surgeon\?[^ ]*zip=22202[^ ]*gender=Male")
    check_visited_path(judge, traj, "nav_dcs", r"/tools/designated-civil-surgeons")
    check_visited_path(judge, traj, "nav_vacc",
                       r"/tools/designated-civil-surgeons/vaccination-requirements")
    check_visited_path(judge, traj, "nav_feecalculator",
                       r"/feecalculator\?[^ ]*form=97307")
    check_visited_path(judge, traj, "nav_i693", r"/i-693")
    # answer ground truth
    check_answer_phrase(judge, answer, "closest_name", "VAN DORN PEDIATRICS, PC")
    check_answer_phrase(judge, answer, "closest_addr", "2500 NORTH VAN DORN STREET")
    check_answer_any(judge, answer, "closest_dist", ["2.8 miles", "2.8"])
    check_answer_phrase(judge, answer, "doctor_name", "DR. MOHEB ANDRAWIS")
    check_answer_phrase(judge, answer, "doctor_phone", "703-933-0555")
    check_answer_phrase(judge, answer, "second_doctor", "DR. MONA HANNA")
    check_answer_phrase(judge, answer, "third_name", "BEAUREGARD MEDICAL CENTER")
    check_answer_phrase(judge, answer, "third_street", "4216 KING STREET")
    check_answer_phrase(judge, answer, "third_phone", "703-820-7000")
    check_answer_number(judge, answer, "arabic_count", 5)
    check_answer_phrase(judge, answer, "arabic_sample", "VAN DORN PEDIATRICS, PC")
    check_answer_number(judge, answer, "female_count", 4)
    check_answer_phrase(judge, answer, "first_female", "DR. MONA HANNA")
    check_answer_number(judge, answer, "male_count", 6)
    check_answer_count_at_least(judge, answer, "vaccines",
                                ["Mumps", "Measles", "Rubella", "Polio"], 3)
    check_answer_number(judge, answer, "i693_fee", 0)
    check_answer_any(judge, answer, "i693_edition", ["01/20/25"])
    check_read_only(judge, initial, after)

if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
