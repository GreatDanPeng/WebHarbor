#!/usr/bin/env python3
"""Deterministic verifier for CBP.gov--8 (u_s_customs).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review container wh-us-customs-r2review, seed md5
26b00e5808a42028cc0c3019eb3912f5) — never read from tasks.jsonl.
Usage: python3 verify_8.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "CBP.gov--8"



def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_releases_list", r"/newsroom/media-releases/all(\?|$)")
    check_visited_path(judge, traj, "nav_ceremony_release",
                       r"/newsroom/(national|local)-media-release/11-memorial-ceremony-juarez")
    check_visited_path(judge, traj, "nav_tidal_search", r"/newsroom/media-releases/all\?.*q=[^#]*tidal")
    check_visited_path(judge, traj, "nav_87_release",
                       r"/newsroom/national-media-release/operation-tidal-wave-boston-leads-87-cruise-ship-crew-removals-cbp")
    check_answer_phrase(judge, answer, "port", "Laredo")
    check_answer_phrase(judge, answer, "bridge", "Juarez-Lincoln Bridge")
    check_answer_phrase(judge, answer, "release_date", "2026-09-11")
    check_answer_any(judge, answer, "honored",
                     ["victims", "first responders", "survivors"])
    check_answer_number(judge, answer, "search_total", 2)
    check_answer_number(judge, answer, "crew_removed", 87)
    check_answer_phrase(judge, answer, "port_boston", "Port of Boston")
    check_answer_phrase(judge, answer, "other_title", "another 10 cruise ship crewmembers")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
