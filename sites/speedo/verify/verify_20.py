#!/usr/bin/env python3
"""Verify Speedo--20.

Buy the Adult Silicone Cap in Purple with a delivery option that costs under
£10. Use guest checkout with email casey.morgan@example.com, address Casey
Morgan, 2 Windmill Lane, Leeds, LS6 1QR, paying with Visa 4242424242424242
exp 08/28, CVC 909. Report the order number and total.
"""
from verify_lib import (Judge, check_answer_number, check_answer_phrase, check_new_order,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier)

TASK_ID = "Speedo--20"

PRODUCT_NAME = "Adult Silicone Cap Purple"
UNIT_PRICE = 6.75
SHIPPING = 5.99            # Standard Delivery (£5.99 < £10)
TOTAL = 12.74


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_pdp", r"/products/adult-silicone-cap-purple")
    check_visited_path(judge, traj, "visited_checkout", r"/checkout")
    check_visited_path(judge, traj, "visited_confirmation", r"/order/confirmation/SP100008")
    check_answer_phrase(judge, answer, "order_number", "SP100008")
    check_answer_number(judge, answer, "total", "12.74", "order total")

    check_only_tables_changed(judge, initial_db, after_db,
                              allowed={"orders", "order_items"})
    check_new_order(judge, initial_db, after_db,
                    email="casey.morgan@example.com", subtotal=UNIT_PRICE,
                    discount=0.0, discount_code="", shipping_method="Standard Delivery",
                    shipping=SHIPPING, total=TOTAL, card_last4="4242",
                    items=[(PRODUCT_NAME, "One Size", 1, UNIT_PRICE)])


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
