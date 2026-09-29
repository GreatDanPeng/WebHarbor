#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--20 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_20.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--20"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_media_mail", r"/ship/mail-shipping-services")
    check_visited_path(judge, traj, "nav_restrictions", r"/shipping-restrictions")
    check_visited_path(judge, traj, "nav_packages_calc", r"/postcalc/packages")
    check_answer_any(judge, answer, "delivery_window", ["2-8 days", "2–8 days",
                                                        "2 to 8 days"])
    check_answer_number(judge, answer, "max_weight", 70)
    check_answer_count_at_least(judge, answer, "allowed_contents",
                                ["books", "sound recordings", "printed music",
                                 "test materials", "computer-readable media",
                                 "films"], 1)
    check_answer_count_at_least(judge, answer, "restricted_categories",
                                ["hazardous", "flammable", "lithium",
                                 "alcohol", "perfume", "aerosol"], 2)
    # r2 deepening (fix F-3): Media Mail price ladder at 1 and 20 pounds
    # (5 pounds was already pinned).
    check_answer_money(judge, answer, "mm_1lb", 4.39)
    check_answer_money(judge, answer, "mm_5lb", 7.34)
    check_answer_money(judge, answer, "mm_20lb", 18.39)
    # audit deepening (ordinal 57): contents-list count, video-game NOTE,
    # First-Class letters starting price, prohibited-list count, 50 lb rung.
    check_answer_number(judge, answer, "mm_contents_count", 8)
    check_answer_phrase(judge, answer, "video_games", "do not qualify")
    check_answer_money(judge, answer, "fcm_letters_from", 0.82)
    check_answer_number(judge, answer, "prohibited_count", 14)
    check_answer_count_at_least(judge, answer, "prohibited_items", [
        "Aerosols", "Air Bags", "Alcoholic Beverages", "Ammunition",
        "Cigarettes", "Dry Ice", "Explosives", "Gasoline", "Marijuana",
        "Mercury", "Nail Polish", "Perfumes", "Poisons"], 2)
    check_answer_money(judge, answer, "mm_50lb", 40.49)
    check_answer_money(judge, answer, "mm_70lb", 55.23)

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
