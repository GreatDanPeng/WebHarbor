#!/usr/bin/env python3
"""Verify StubHub--11.

Sign in as alice.j@test.com (TestPass123!). Report the payment cards currently on file with brand, last four digits, expiry month and year, and which one is the default. Add a new Mastercard test card in Alice's name with a future expiry and three-digit code, make it the default, then remove one of the older non-default cards. Report the final card list with the new default marked.
"""
from verify_lib import (Judge, check_answer_any, check_answer_number, check_answer_phrase,
                        check_answer_regex, check_answer_one_of, check_read_only,
                        check_only_tables_changed, check_table_deltas, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier)

TASK_ID = "StubHub--11"

from verify_lib import table_diff


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_payments_before", r"/secure/myaccount/payments")
    check_visited_path(judge, traj, "added_card_post", r"/secure/myaccount/payments")
    
    check_answer_phrase(judge, answer, "card_before_visa", "4242")
    check_answer_phrase(judge, answer, "card_before_mc", "8321")
    check_answer_phrase(judge, answer, "new_card_last4", "4444")
    judge.check("new_card_default",
                "default" in answer.casefold() and "4444" in answer,
                "answer must state the new Mastercard 4444 is the default")
    judge.check("old_card_removed",
                "8321" in answer and ("remove" in answer.casefold() or "no longer" in answer.casefold()),
                "answer must state the older non-default card 8321 was removed")
    added, removed, changed = table_diff(initial_db, after_db, "payment_cards")
    judge.check("card_delta_shape", len(added) == 1 and len(removed) == 1 and len(changed) == 1,
                f"one card added, one removed, one changed: +{list(added)} -{list(removed)} ~{list(changed)}")
    for key, row in added.items():
        judge.check("new_card_row", row["user_id"] == 1 and row["brand"] == "Mastercard"
                    and row["last4"] == "4444" and row["holder"] == "Alice Johnson"
                    and row["is_default"] == 1,
                    f"new card must be Alice's default Mastercard 4444: {dict(row)}")
    for key, row in removed.items():
        judge.check("removed_card_row", row["last4"] == "8321",
                    f"removed card must be the older non-default Mastercard 8321: {dict(row)}")
    for key, (before, after) in changed.items():
        judge.check("old_default_cleared", before["last4"] == "4242" and after["is_default"] == 0,
                    "the Visa 4242 must no longer be the default")
    check_only_tables_changed(judge, initial_db, after_db, ("payment_cards",))


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
