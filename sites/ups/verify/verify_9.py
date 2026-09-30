#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--9."""
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
    check_trajectory_identity(judge, traj, "UPS--9")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_login", r"/login")
    check_visited_path(judge, traj, "nav_claim_new", r"/claims/new")
    check_visited_path(judge, traj, "nav_claim_status", r"/claims/status/CLM")
    check_answer_phrase(judge, answer, "claim_number_prefix", "clm")
    check_answer_phrase(judge, answer, "claim_status", "claim review in progress")
    check_answer_phrase(judge, answer, "resolution_days", "8 to 10 business days")
    # DB: exactly one claim row for the damaged bowls (contact email agent-chosen)
    check_only_tables_changed(judge, initial, after, {"claims"})
    row = after.execute(
        "SELECT claim_id, tracking_number, role, problem_type, merchandise, "
        "item_count, item_value, status FROM claims "
        "WHERE tracking_number='1Z58F0E70371234458'").fetchone()
    if row is None:
        judge.fail("db_claim_row", "claim for 1Z58F0E70371234458 missing")
    else:
        cid = row[0]
        want = ("CLM4000001", "1Z58F0E70371234458", "receiver", "damaged",
                "hand-thrown ceramic bowl set", 2, 180.0,
                "Claim Review in Progress")
        if row != want:
            judge.fail("db_claim_fields", f"{row!r} != {want!r}")
        else:
            judge.ok("db_claim_fields", "receiver/damaged/bowls/2/$180/in review")
        if cid.lower() not in answer.lower():
            judge.fail("answer_claim_number", f"answer lacks {cid}")
        else:
            judge.ok("answer_claim_number", cid)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--9", checks))
