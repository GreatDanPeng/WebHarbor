#!/usr/bin/env python3
"""Verify StubHub--5.

Sign in as carol.d@test.com (TestPass123!). Before buying, report which gift card amounts and designs the site offers. Then buy a $150 holiday-design gift card for your nephew Danny (danny.gift@example.com) including a short birthday message. Report the gift card code shown on the gift cards page, its status, the confirmation message, how many gift cards now appear in Carol's order history, and the amount and purchase date of the earliest one.
"""
from verify_lib import (Judge, check_answer_any, check_answer_number, check_answer_phrase,
                        check_answer_regex, check_answer_one_of, check_read_only,
                        check_only_tables_changed, check_table_deltas, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier)

TASK_ID = "StubHub--5"

import re
from verify_lib import table_diff


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_gift_cards_before", r"/gift-cards")
    check_visited_path(judge, traj, "visited_gift_cards_after", r"/gift-cards")
    
    for amount in (25, 50, 75, 100, 150, 200, 250, 500):
        check_answer_number(judge, answer, f"amount_{amount}", amount)
    for design in ("classic", "birthday", "holiday", "sports", "concert"):
        check_answer_phrase(judge, answer, f"design_{design}", design)
    check_answer_number(judge, answer, "purchased_amount", 150)
    check_answer_phrase(judge, answer, "recipient", "Danny")
    check_answer_regex(judge, answer, "gift_code_format", r"\bSH[A-Z0-9]{10}\b",
                       "a SH+10-char gift card code")
    judge.check("code_not_seed_frozen",
                not re.search(r"SHGC\d+", answer),
                "the new gift card code must not be one of the seeded fixture codes")
    check_answer_number(judge, answer, "gift_cards_in_history", 2)
    check_answer_number(judge, answer, "earliest_amount", 100)
    # r2 sync (2026-09-26): the F8 fix made the gift-cards / Orders pages show
    # the true seeded purchase date (created_at = 2026-07-24), so the earliest
    # card's purchase date is Jul 24, 2026 (the r1 contract froze the pre-fix
    # dateless "Aug 23" inference).
    judge.check("earliest_purchase_date",
                "Jul 24" in answer or "July 24" in answer,
                "answer must report the earliest gift card's purchase date (Jul 24, 2026)")
    added, removed, changed = table_diff(initial_db, after_db, "gift_card_orders")
    judge.check("gift_card_added", len(added) == 1 and not removed and not changed,
                f"exactly one new gift card row: +{list(added)} -{list(removed)} ~{list(changed)}")
    for key, row in added.items():
        judge.check("gift_card_row_exact",
                   row["user_id"] == 3 and row["amount"] == 150
                   and row["recipient_name"] == "Danny"
                   and row["recipient_email"] == "danny.gift@example.com"
                   and row["design"] == "holiday"
                   and re.fullmatch(r"SH[A-Z0-9]{10}", row["code"] or ""),
                   f"new gift card must be the $150 holiday card for Danny: {dict(row)}")
    check_only_tables_changed(judge, initial_db, after_db, ("gift_card_orders",))


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
