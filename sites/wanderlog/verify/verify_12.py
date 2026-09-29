#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--12 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r2 from the reviewer's independent honest walks on the
r2 review container wh-wanderlog-r2, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl.
Audit sync (orch/audit/wanderlog): list_title/rome_title accept
either rendering (page h1 'Best hotels in X' or the canonical list title) — honest double
read, us-appliance verify_8 precedent.
Usage: python3 verify_12.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_number_absent,
    check_answer_ordered, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Wanderlog--12"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_hotels", r"/hotels")
    check_visited_path(judge, traj, "nav_hotels_paris", r"/hotels/9614")
    check_visited_path(judge, traj, "nav_hotel1", r"/place/details/24349")
    check_visited_path(judge, traj, "nav_hotel3", r"/place/details/531760")
    check_visited_path(judge, traj, "nav_hotel5", r"/place/details/757903")
    check_visited_path(judge, traj, "nav_hotels_rome", r"/hotels/9616")
    check_visited_path(judge, traj, "nav_rome_hotel1", r"/place/details/390732")
    check_visited_path(judge, traj, "nav_rome_hotel2", r"/place/details/392578")
    check_answer_phrase(judge, answer, "h1", 'Search for hotel and Airbnb stays in one place')
    check_answer_phrase(judge, answer, "first_feature", 'All-in-one hotel search')
    # Audit sync: the hotels page renders the ranking as 'Best hotels in Paris' (h1) while
    # the underlying Wanderlog list is titled 'The 50 best hotels in Paris' (shown on the
    # hotels' Appears-in cards). Both are honest readings of 'the ranked list's title'.
    check_answer_any(judge, answer, "list_title",
                     ['The 50 best hotels in Paris', 'Best hotels in Paris'])
    check_answer_number(judge, answer, "upstream", 50)
    check_answer_ordered(judge, answer, "top5_order", ['Shangri-La Paris', 'Four Seasons Hotel George V, Paris', 'Ritz Paris', 'The Peninsula Paris', 'Le Meurice'])
    check_answer_phrase(judge, answer, "first_desc", 'Elegant rooms & suites in a luxe lodging offering Eiffel Tower views, a renowned restaurant & a spa')
    check_answer_phrase(judge, answer, "first_cat", 'Hotel')
    check_answer_regex(judge, answer, "first_coords", r"48\.8639[, ]*2\.2934")
    check_answer_phrase(judge, answer, "third_desc", 'Renowned luxury hotel with posh quarters & upscale dining, plus a chic spa & a gym')
    check_answer_phrase(judge, answer, "fifth_desc", 'Opulent quarters in a regal hotel offering 2 upscale restaurants, a bar & a patisserie, plus a spa')
    check_answer_any(judge, answer, "rome_title",
                     ['The 49 best hotels in Rome', 'Best hotels in Rome'])
    check_answer_number(judge, answer, "rome_upstream", 49)
    check_answer_ordered(judge, answer, "rome_top2", ['Hotel de Russie, a Rocco Forte hotel', 'Hotel Eden'])
    check_answer_phrase(judge, answer, "rome_first_desc", 'High-end hotel featuring an acclaimed restaurant with a garden, plus a bar & a spa')
    check_answer_phrase(judge, answer, "rome_second_desc", 'Elegant rooms & suites with complimentary Wi-Fi, plus a posh rooftop restaurant & a piano bar')
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
