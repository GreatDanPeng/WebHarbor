#!/usr/bin/env python3
"""Verify Ticketmaster--4.

I'm deciding between seeing a show at Sphere in Las Vegas or TD Garden in Boston. Which venue currently lists more upcoming events? For the venue with fewer events, also report its street address and the cheapest all-in price for a Standard Admission ticket to the Boston Bruins vs. Winnipeg Jets game.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (Judge, check_answer_any, check_answer_money,
                        check_answer_number, check_answer_phrase,
                        check_input_action, check_only_tables_changed,
                        check_purchase_order, check_read_only,
                        check_row_added, check_row_removed,
                        check_trajectory_identity, check_visited_path,
                        final_answer, run_verifier)

TASK_ID = "Ticketmaster--4"


# Frozen ground truth (reviewer r2 honest walk 2026-09-27, seed md5
# b03a154d...): Sphere venue page (155762) lists 20 upcoming events, TD
# Garden (8337) lists 18, so TD Garden has fewer. TD Garden street address
# "100 Legends Way, Boston, MA 02114". Cheapest Standard Admission ticket
# for Bruins vs. Winnipeg Jets (event 010064EDC5277AB0): $81.18 incl fees
# (Sec BALC Row I, listing 15685). The task pins Standard Admission, so the
# cheaper Accessible listing ($47.83) is not an acceptable answer.
SPHERE_ID = "155762"
TDG_ID = "8337"
EVENT_ID = "010064EDC5277AB0"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_visited_path(judge, traj, "Sphere venue page", rf"/venue/{SPHERE_ID}")
    check_visited_path(judge, traj, "TD Garden venue page", rf"/venue/{TDG_ID}")
    check_visited_path(judge, traj, "Bruins vs Jets event page", rf"/event/{EVENT_ID}")
    check_answer_number(judge, answer, "Sphere events", 20, ["sphere", "20"])
    check_answer_number(judge, answer, "TD Garden events", 18, ["garden", "18"])
    check_answer_phrase(judge, answer, "TD Garden street address", "100 Legends Way")
    check_answer_money(judge, answer, "cheapest Standard Admission ticket", 81.18)
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    sys.exit(run_verifier(TASK_ID, run_checks))
