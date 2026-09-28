#!/usr/bin/env python3
"""Verify StubHub--19.

Create a new account with realistic details. Buy a $50 sports-design gift card for a friend at a valid email address, then add the Seattle Kraken to your favorites from their performer page. Report the gift card code and its status, confirm the Kraken appear in your favorites, and report how many upcoming Kraken home games the performer page lists plus the opponent and date of the next one.
"""
from verify_lib import (Judge, check_answer_any, check_answer_number, check_answer_phrase,
                        check_answer_regex, check_answer_one_of, check_read_only,
                        check_only_tables_changed, check_table_deltas, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier)

TASK_ID = "StubHub--19"

import re
from verify_lib import table_diff


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_register", r"/secure/register")
    check_visited_path(judge, traj, "visited_gift_cards", r"/gift-cards")
    check_visited_path(judge, traj, "visited_kraken_page", r"/seattle-kraken-tickets/performer/900000460")
    check_visited_path(judge, traj, "visited_favorites", r"/favorites")
    
    check_answer_regex(judge, answer, "gift_code_format", r"\bSH[A-Z0-9]{10}\b",
                       "a SH+10-char gift card code")
    check_answer_number(judge, answer, "gift_amount", 50)
    check_answer_phrase(judge, answer, "design", "sports")
    judge.check("kraken_in_favorites",
                "kraken" in answer.casefold() and ("favorites" in answer.casefold()),
                "answer must confirm the Kraken appear in favorites")
    check_answer_number(judge, answer, "kraken_home_games", 41)
    check_answer_phrase(judge, answer, "next_opponent", "Calgary Flames")
    added_u, _, _ = table_diff(initial_db, after_db, "users")
    judge.check("new_user_created", len(added_u) == 1, f"exactly one new user: {list(added_u)}")
    new_uid = next(iter(added_u))[0] if added_u else None
    added_g, _, _ = table_diff(initial_db, after_db, "gift_card_orders")
    judge.check("gift_card_created", len(added_g) == 1, f"exactly one new gift card: {list(added_g)}")
    for key, row in added_g.items():
        judge.check("gift_card_row_exact",
                   row["user_id"] == new_uid and row["amount"] == 50
                   and row["design"] == "sports"
                   and re.fullmatch(r"SH[A-Z0-9]{10}", row["code"] or ""),
                   f"new gift card must be the $50 sports card for the new user: {dict(row)}")
    added_f, _, _ = table_diff(initial_db, after_db, "favorites")
    judge.check("kraken_favorite_created", len(added_f) == 1
                and next(iter(added_f.values()))["performer_id"] == 524
                and next(iter(added_f.values()))["user_id"] == new_uid,
                f"the new user must favorite the Kraken (performer 524): {list(added_f)}")
    _, _, changed_p = table_diff(initial_db, after_db, "performers")
    judge.check("kraken_follower_bump",
                (524,) in changed_p
                and changed_p[(524,)][1]["followers"] == changed_p[(524,)][0]["followers"] + 1,
                "the Kraken's follower count must increase by exactly one")
    check_only_tables_changed(judge, initial_db, after_db, ("users", "gift_card_orders", "favorites", "performers"))


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
