#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--5 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the r3 honest Playwright walks on
the fix container wh-vadm-fix3, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r3-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_5.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_ordered,
    check_answer_money_after, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Virginia DMV--5"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # Alexandria CSC research + Franconia alternative + finder-filter counts
    check_visited_path(judge, traj, "nav_locations", r"/all-locations")
    check_visited_path(judge, traj, "nav_alexandria_search", r"/all-locations\?q=Alexandria")
    check_visited_path(judge, traj, "nav_alexandria", r"/locations/alexandria")
    check_visited_path(judge, traj, "nav_franconia", r"/locations/franconia")
    check_visited_path(judge, traj, "nav_dmv_select_filter", r"/all-locations\?[^ ]*type=dmv_select")
    check_visited_path(judge, traj, "nav_alexandria_dmvselect", r"/all-locations\?q=Alexandria&type=dmv_select")
    check_visited_path(judge, traj, "nav_fairfax_search", r"/all-locations\?q=Fairfax&type=dmv_select")
    check_visited_path(judge, traj, "nav_csc_filter", r"/all-locations\?[^ ]*type=csc")
    check_answer_phrase(judge, answer, "address", "2681 Mill Road")
    check_answer_any(judge, answer, "phone", ["804-497-7100", "(804) 497-7100", "804.497.7100"])
    check_answer_any(judge, answer, "fax", ["703-317-3564", "(703) 317-3564"])
    check_answer_any(judge, answer, "weekday_hours", ["8:00 am-5:00 pm", "8:00 am - 5:00 pm", "8 am-5 pm"])
    check_answer_any(judge, answer, "saturday_hours", ["8:00 am-12:00 pm", "8:00 am - 12:00 pm", "8 am-12 pm"])
    check_answer_any(judge, answer, "motorcycle_testing", ["motorcycle skills testing not available",
                                                           "does not offer motorcycle skills testing",
                                                           "motorcycle skills testing: not available",
                                                           "motorcycle skills testing is not available",
                                                           "not available: motorcycle skills testing"])
    check_answer_any(judge, answer, "road_testing", ["in-car road skills testing",
                                                      "road skills testing: in-car",
                                                      "in-car road skills"])
    check_answer_any(judge, answer, "franconia_fax", ["703-922-3875", "(703) 922-3875"])
    check_answer_any(judge, answer, "franconia_service", ["motorcycle skills testing"])
    check_answer_number(judge, answer, "dmv_select_count", 58)
    check_answer_number(judge, answer, "alexandria_dmvselect_count", 1)
    check_answer_any(judge, answer, "alexandria_office", ["aaa alexandria"])
    check_answer_phrase(judge, answer, "alexandria_office_address", "2231 Eisenhower Avenue")
    check_answer_number(judge, answer, "fairfax_dmv_select_count", 2)
    check_answer_number(judge, answer, "csc_count", 76)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
