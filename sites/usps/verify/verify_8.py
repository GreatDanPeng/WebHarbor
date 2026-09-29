#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--8 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_8.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_phrase,
    check_answer_regex, check_attributed_money, check_only_tables_changed,
    check_read_only, check_rows_added, check_screenshots,
    check_seed_contract, check_section_phrase, check_trajectory_identity,
    check_visited_any, check_visited_path, final_answer, run_verifier,
)

TASK_ID = "USPS.com--8"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_locations", r"/locations")
    check_visited_path(judge, traj, "nav_beverly", r"/locations/beverly-hills-ca-90210")
    check_answer_number(judge, answer, "locations_listed", 1)
    check_answer_phrase(judge, answer, "location_name", "Beverly Hills")
    check_answer_any(judge, answer, "street_address", [
        "191 Beverly Hills Main St"])
    check_answer_any(judge, answer, "mon_fri_hours", ["9:00 am - 7:00 pm",
                                                      "9:00 am to 7:00 pm"])
    check_answer_phrase(judge, answer, "established", "October 17, 1907")
    check_answer_phrase(judge, answer, "postmaster", "Michael J. O'Rourke")
    # r2 truth-move #6 (fix F-13): hours render in 12-hour clock now, so the
    # frozen "9:00 am - 19:00 pm" hybrid format no longer exists on the site.
    # Deepened (fix F-3): phone number + name-search cross-check.
    check_answer_phrase(judge, answer, "phone", "800-ASK-USPS")
    check_answer_count_at_least(judge, answer, "one_service",
                                ["Bulk Mail Acceptance", "Burial Flags",
                                 "Stamps by Mail"], 1)
    check_answer_phrase(judge, answer, "name_search_zip", "90210")
    check_answer_phrase(judge, answer, "name_search_state", "CA")
    # audit deepening (ordinal 57): county + Sunday hours on the detail
    # page, the two-result name search (Beverly WV), and ZIP 90230.
    check_answer_phrase(judge, answer, "bh_saturday", "10:00 am - 1:00 pm")
    check_answer_phrase(judge, answer, "bh_sunday", "Closed")
    check_answer_number(judge, answer, "name_search_count", 2)
    check_answer_phrase(judge, answer, "beverly_wv_state", "WV")
    check_answer_phrase(judge, answer, "beverly_wv_zip", "26253")
    check_answer_any(judge, answer, "beverly_wv_est", ["1806"])
    check_visited_path(judge, traj, "nav_beverly_wv", r"/locations/beverly-wv-26253")
    check_answer_phrase(judge, answer, "culver_name", "Culver City")
    check_answer_any(judge, answer, "culver_mon_fri", ["9:00 am - 5:00 pm"])
    check_visited_path(judge, traj, "nav_culver", r"/locations/culver-city-ca-90230")
    check_answer_count_at_least(judge, answer, "reserve_periods",
                                ["6 months", "3 months"], 2)
    check_visited_path(judge, traj, "nav_bh_reserve",
                       r"/po-boxes/reserve/beverly-hills-ca-90210")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
