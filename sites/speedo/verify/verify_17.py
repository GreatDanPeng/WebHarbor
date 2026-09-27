#!/usr/bin/env python3
"""Verify Speedo--17.

Which four Team Speedo athletes represent Great Britain? List their names. Then
find the athlete whose motto is "Never fear failure" and report which Speedo
suit he wore at the Paris 2024 Olympics, and report the price of the cheapest
Women's Fastskin LZR Ignite Kneeskin colourway currently in stock.
"""
from verify_lib import (Judge, check_answer_number, check_answer_phrase,
                        check_read_only, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier)

TASK_ID = "Speedo--17"

GB_ATHLETES = ("Adam Ramsay-Peaty", "Alice Tai", "Duncan Scott", "Matt Richards")
MOTTO_ATHLETE_SLUG = "leon-marchand"
SUIT = "Fastskin Valor"      # Léon Marchand wore the Speedo Fastskin Valor at Paris 2024
CHEAPEST_IGNITE = 114.00     # Women's Fastskin LZR Ignite Kneeskin Black/Grey / Blue / Blue/Pink


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_team_speedo", r"/pages/team-speedo")
    check_visited_path(judge, traj, "visited_motto_athlete",
                       rf"/pages/team-speedo-{MOTTO_ATHLETE_SLUG}")
    check_visited_path(judge, traj, "visited_ignite_pdp",
                       r"/products/womens-fastskin-lzr-ignite-kneeskin")
    for name in GB_ATHLETES:
        check_answer_phrase(judge, answer, f"mentions_{name.split()[0].lower()}", name)
    check_answer_phrase(judge, answer, "mentions_motto_athlete", "Marchand")
    check_answer_phrase(judge, answer, "mentions_suit", SUIT)
    check_answer_number(judge, answer, "cheapest_ignite", "114.00",
                         "cheapest in-stock Women's Fastskin LZR Ignite Kneeskin")

    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
