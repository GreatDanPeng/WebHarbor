#!/usr/bin/env python3
"""Deterministic verifier for USPS.com--19 (usps).

Ground truth below is HARDCODED (frozen from the reviewer's independent
walkthroughs of the review instance, seed md5 af00d6d452e0fdddcf2197357ad9f3b2)
— never read from tasks.jsonl.
Usage: python3 verify_19.py --run_dir DIR [--initial_db P] [--after_db P]
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

TASK_ID = "USPS.com--19"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_newsroom", r"/newsroom")
    check_visited_path(judge, traj, "nav_recent_release", r"/newsroom/squirrels")
    check_visited_path(judge, traj, "nav_holiday_release", r"/newsroom/postal-service-recommends-2026-holiday")
    check_answer_phrase(judge, answer, "recent_title", "Squirrels")
    check_answer_phrase(judge, answer, "recent_date", "September 25, 2026")
    check_answer_any(judge, answer, "announces", ["stamps", "Stamp"])
    check_answer_count_at_least(judge, answer, "image_description",
                                ["squirrels and chipmunks in snow stamps",
                                 "Squirrels and chipmunks"], 1)
    check_answer_phrase(judge, answer, "holiday_date", "September 22, 2026")
    check_answer_any(judge, answer, "recommendation", [
        "mail and ship packages early", "ship early",
        "mailing and shipping packages early", "shipping packages early"])
    # r2 deepening (fix F-3): second-most-recent release title/date, holiday
    # release image description, and the newsroom release count.
    check_answer_phrase(judge, answer, "second_title", "Linda McCartney")
    check_answer_phrase(judge, answer, "second_date", "September 25, 2026")
    # audit deepening (ordinal 57): the holiday release carries NO image
    # (upstream capture has images: []) — the old holiday_image anchor was
    # satisfied by the word "holiday" and the r2 fixture answer fabricated
    # "its image shows holiday mail". Replaced with real page facts: the
    # release TYPE column, the Winter Wreath release, and Service Alerts.
    check_answer_phrase(judge, answer, "recent_type", "News Release")
    check_visited_path(judge, traj, "nav_winter_wreath",
                       r"/newsroom/postal-service-issues-winter-wreath")
    check_answer_phrase(judge, answer, "wreath_date", "September 18, 2026")
    check_answer_any(judge, answer, "wreath_image", ["Winter Wreath stamp"])
    check_visited_path(judge, traj, "nav_service_alerts", r"/newsroom/service-alerts")
    check_answer_number(judge, answer, "alerts_count", 4)
    check_answer_any(judge, answer, "alert_title", [
        "Business Mailers Weather Alerts", "Resident Weather Alerts",
        "Mailer information", "International Service Alerts"])
    check_answer_number(judge, answer, "release_count", 14)
    check_visited_path(judge, traj, "nav_diwali_release",
                       r"/newsroom/u-s-postal-service-celebrates-festival")
    check_answer_phrase(judge, answer, "diwali_date", "September 17, 2026")
    check_answer_any(judge, answer, "diwali_image", ["Diwali stamp"])
    # audit deepening (ordinal 57): one alert page opened for its detail.
    check_answer_any(judge, answer, "alert_detail", [
        "planned power outages", "planned power outage", "weather"])

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
