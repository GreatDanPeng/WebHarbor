#!/usr/bin/env python3
"""Verify Speedo--0.

My daughter needs her first serious race suit. Use the swimwear quiz shopping
for a woman who does racing, choose the Fastskin Valor route, and buy the
cheapest recommended kneeskin in size 26. Pay with Visa 4242424242424242 exp
12/28, CVC 123, express delivery to Maya Torres, 22 Harbour Reach, Portsmouth,
PO1 3XY. Report the order number and the total charged.
"""
from verify_lib import (Judge, check_answer_number, check_answer_phrase,
                        check_new_order, check_only_tables_changed,
                        check_trajectory_identity, check_visited_path,
                        final_answer, run_verifier)

TASK_ID = "Speedo--0"

PRODUCT = "Women's Fastskin LZR Ignite Kneeskin Black/Grey"   # cheapest recommended kneeskin (£114, on sale)
UNIT_PRICE = 114.0
SHIPPING = 8.99                                                # Express Delivery
TOTAL = 122.99


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_swimsuit_quiz", r"/pages/swimsuit-quiz")
    check_visited_path(judge, traj, "visited_quiz_results", r"/pages/swimsuit-quiz/results")
    check_visited_path(judge, traj, "visited_kneeskin_pdp",
                       r"/products/womens-fastskin-lzr-ignite-kneeskin-black-grey")
    check_visited_path(judge, traj, "visited_checkout", r"/checkout")
    check_visited_path(judge, traj, "visited_confirmation", r"/order/confirmation/SP100008")
    check_answer_phrase(judge, answer, "mentions_product", "Kneeskin Black/Grey")
    check_answer_phrase(judge, answer, "order_number", "SP100008")
    check_answer_number(judge, answer, "total", "122.99", "total charged")

    check_only_tables_changed(judge, initial_db, after_db,
                              allowed={"orders", "order_items"})
    check_new_order(judge, initial_db, after_db,
                    email="maya.torres@example.com", subtotal=UNIT_PRICE,
                    discount=0.0, discount_code="", shipping_method="Express Delivery",
                    shipping=SHIPPING, total=TOTAL, card_last4="4242",
                    items=[(PRODUCT, "26", 1, UNIT_PRICE)])


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
