#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--10."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (Judge, check_answer_absent, check_answer_any,
                        check_answer_count_at_least, check_answer_money,
                        check_answer_number, check_answer_phrase,
                        check_only_tables_changed, check_read_only,
                        check_rows_added, check_rows_changed,
                        check_seed_contract, check_screenshots,
                        check_trajectory_identity, check_visited_any,
                        check_visited_path, final_answer, run_verifier)


def checks(judge, traj, initial, after):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, "UPS--10")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_detail", r"/track/detail/1ZF5R8210372885301$")
    check_visited_path(judge, traj, "nav_status_article", r"/support/article/understanding-tracking-status")
    check_visited_path(judge, traj, "nav_claims", r"/claims")
    check_visited_path(judge, traj, "nav_locator", r"/locations\?zip=10001&type=UPS(%20|\+)Access(%20|\+)Point")
    check_answer_phrase(judge, answer, "status", "transferred to post office")
    check_answer_phrase(judge, answer, "last_scan_desc",
                        "transferred to the local post office to finish the delivery")
    check_answer_any(judge, answer, "article_extra_time",
                     ["allow for an extra day or two", "allow an extra day or two"])
    check_answer_phrase(judge, answer, "claims_faq",
                        "until the exception scan")
    check_answer_any(judge, answer, "claims_faq_handover",
                     ["handed over to the post office", "handed over to the post"])
    check_answer_phrase(judge, answer, "ap_name", "deepchhaya deli")
    check_answer_phrase(judge, answer, "ap_street", "334 w 37th st")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--10", checks))
