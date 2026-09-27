#!/usr/bin/env python3
"""Verify Speedo--11.

The Women's Endurance+ Medalist Swimsuit comes in several colourways. Compare
them: report each colourway's current price, which colourways are on sale and
how much each saves versus the regular price, and which colourways are the
most expensive. Then add the Navy colourway in size 34 to Alice's wishlist
(alice.j@test.com / TestPass123!).
"""
from verify_lib import (Judge, check_answer_number, check_answer_phrase,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier,
                        table_diff)

TASK_ID = "Speedo--11"

ALICE_ID = 1
NAVY_PRODUCT_ID = 961      # Women's Endurance+ Medalist Swimsuit Navy £23.25
# Colourway ground truth: Black £31.00, Blue £23.25 (two listings), Green
# £23.25, Navy £23.25, Red (Womens') £31.00, Printed Black £22.80, Printed
# Dark Pink £28.50, Plus Size Black £33.00. Most expensive: Plus Size Black.


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/search\?[^ ]*[Ee]ndurance")
    check_visited_path(judge, traj, "visited_navy_pdp",
                       r"/products/womens-endurance-medalist-swimsuit-navy")
    check_visited_path(judge, traj, "visited_login", r"/login")
    check_answer_phrase(judge, answer, "mentions_navy_price", "23.25")
    check_answer_phrase(judge, answer, "mentions_black_price", "31.00")

    check_only_tables_changed(judge, initial_db, after_db,
                              allowed={"wishlist_items"})
    added, removed, _ = table_diff(initial_db, after_db, "wishlist_items")
    judge.check("navy_added_for_alice",
                len(added) == 1 and len(removed) == 0
                and list(added.values())[0]["user_id"] == ALICE_ID
                and list(added.values())[0]["product_id"] == NAVY_PRODUCT_ID,
                f"added={list(added.values())!r} removed={list(removed.values())!r}")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
