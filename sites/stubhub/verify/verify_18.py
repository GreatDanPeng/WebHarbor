#!/usr/bin/env python3
"""Verify StubHub--18.

Browse the site's full event catalog from the explore page. Report the first three events listed with performer, date, and venue, then go to page 2 and report the first three events there as well. Report the total number of events with tickets available, open the earliest event in the catalog, and report its get-in price and listing count.
"""
from verify_lib import (Judge, check_answer_any, check_answer_number, check_answer_phrase,
                        check_answer_regex, check_answer_one_of, check_read_only,
                        check_only_tables_changed, check_table_deltas, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier)

TASK_ID = "StubHub--18"



def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_explore_p1", r"/explore(\?page=1)?$|/explore$")
    check_visited_path(judge, traj, "visited_explore_p2", r"/explore\?page=2")
    check_visited_path(judge, traj, "visited_earliest_event", r"/pacific-northwest-ballet-seattle-tickets-9-26-2026/event/161322492")
    
    check_answer_phrase(judge, answer, "p1_event_1", "Serenade")
    check_answer_phrase(judge, answer, "p1_event_2", "Greenshield")
    check_answer_phrase(judge, answer, "p1_event_3", "Lovers Rock")
    check_answer_phrase(judge, answer, "p2_event_1", "Gnash")
    check_answer_phrase(judge, answer, "p2_event_2", "Kamelot")
    check_answer_phrase(judge, answer, "p2_event_3", "Beth Stelling")
    check_answer_number(judge, answer, "total_events", 1267)
    judge.check("earliest_event_named",
                "Serenade" in answer or "Pacific Northwest Ballet" in answer,
                "answer must name the earliest event (Pacific Northwest Ballet - Serenade)")
    check_answer_number(judge, answer, "earliest_getin", 106)
    check_answer_number(judge, answer, "earliest_listing_count", 1)
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
