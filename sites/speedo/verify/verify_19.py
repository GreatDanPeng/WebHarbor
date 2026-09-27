#!/usr/bin/env python3
"""Verify Speedo--19.

David (david.k@test.com / TestPass123!) got a new club card. Sign in, remove
his existing Visa card, add a new default Visa card with number
4012888812345678 exp 03/29, and report how many cards are saved and which is
the default. Then remove the two pairs of goggles from his wishlist and report
the remaining wishlist count.
"""
from verify_lib import (Judge, check_answer_number, check_answer_phrase,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier,
                        table_diff)

TASK_ID = "Speedo--19"

DAVID_ID = 4
CARD_ID = 5                 # David's only card row (Sqlite reuses the rowid after delete+add)
NEW_LAST4 = "5678"
NEW_LABEL = "Club"
NEW_EXP = (3, 29)
GOGGLES_IDS = {61, 816}     # Adult Fastskin Speed Socket 2.0 Mirrored Goggles Red/Smoke,
                           # Speedo iQ Vanquisher 3.0 Track Navy


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_login", r"/login")
    check_visited_path(judge, traj, "visited_payment", r"/account/payment")
    check_visited_path(judge, traj, "visited_wishlist", r"/account/wishlist|/wishlist")
    check_answer_number(judge, answer, "card_count", 1, "cards saved")
    check_answer_phrase(judge, answer, "mentions_default", "5678")
    check_answer_number(judge, answer, "wishlist_count", 4, "remaining wishlist count")

    check_only_tables_changed(judge, initial_db, after_db,
                              allowed={"payment_cards", "wishlist_items"})
    # card swap: the single card row must now be the new Visa ****5678 Club 03/29 default
    a, r, c = table_diff(initial_db, after_db, "payment_cards")
    judge.check("card_swap_single_row",
                not a and not r and len(c) == 1,
                f"added={list(a.values())!r} removed={list(r.values())!r} changed={list(c.keys())!r}")
    for key, (before, after) in c.items():
        judge.check("new_card_values",
                    after["user_id"] == DAVID_ID and after["brand"] == "Visa"
                    and after["last4"] == NEW_LAST4 and after["label"] == NEW_LABEL
                    and (after["exp_month"], after["exp_year"]) == NEW_EXP
                    and after["is_default"] == 1,
                    f"before={dict(before)} after={dict(after)}")
    # wishlist: exactly the two goggles removed, nothing else
    wa, wr, _ = table_diff(initial_db, after_db, "wishlist_items")
    judge.check("two_goggles_removed",
                len(wr) == 2 and len(wa) == 0
                and all(row["user_id"] == DAVID_ID and row["product_id"] in GOGGLES_IDS
                        for row in wr.values()),
                f"removed={list(wr.values())!r} added={list(wa.values())!r}")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
