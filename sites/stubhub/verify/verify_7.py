#!/usr/bin/env python3
"""Verify StubHub--7.

Search the site for 'metal' and for 'seattle', and report what the search suggestion service proposes for each term. Then open the Seattle Sounders FC and Seattle Mariners performer pages: report each performer's follower count and number of upcoming events, and each one's next event with date and venue. Which of the two performers has more upcoming events?
"""
import re

from verify_lib import (Judge, check_answer_any, check_answer_number, check_answer_phrase,
                        check_answer_regex, check_answer_one_of, check_read_only,
                        check_only_tables_changed, check_table_deltas, check_trajectory_identity,
                        check_search_suggestions, check_visited_path, final_answer, run_verifier)

TASK_ID = "StubHub--7"



def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "searched_metal", r"/search\?q=metal")
    # r2 sync (2026-09-26): the F7 fix wired the suggestion service into the
    # search-box autocomplete dropdown, so a fresh UI-path walker types the
    # term and reads the dropdown instead of navigating the raw endpoint.
    # Either use of the service satisfies the gate (anti-shortcut intact).
    check_search_suggestions(judge, traj, "suggestions_metal", "metal")
    check_visited_path(judge, traj, "searched_seattle", r"/search\?q=seattle")
    check_search_suggestions(judge, traj, "suggestions_seattle", "seattle")
    check_visited_path(judge, traj, "visited_sounders", r"/seattle-sounders-fc-tickets/performer/388488")
    check_visited_path(judge, traj, "visited_mariners", r"/seattle-mariners-tickets/performer/1043")
    
    check_answer_phrase(judge, answer, "suggestion_metal", "metallica")
    for name in ("seattle kraken", "seattle mariners", "seattle seahawks",
                 "seattle sounders fc"):
        check_answer_phrase(judge, answer, f"suggestion_seattle_{name.split()[1]}", name)
    check_answer_number(judge, answer, "sounders_followers", "56,600")
    check_answer_number(judge, answer, "sounders_events", 5)
    check_answer_phrase(judge, answer, "sounders_next_event", "Minnesota United")
    check_answer_phrase(judge, answer, "sounders_venue", "Lumen Field")
    check_answer_number(judge, answer, "mariners_followers", "75,200")
    check_answer_number(judge, answer, "mariners_events", 2)
    check_answer_phrase(judge, answer, "mariners_next_event", "Los Angeles Angels")
    check_answer_phrase(judge, answer, "mariners_venue", "T-Mobile Park")
    # audit fix (2026-09-26): the ground truth is the Sounders FC have more
    # upcoming events (5 vs 2). The old phrase gate accepted (and its label
    # even encouraged) the factually false "Mariners have more" direction.
    # The verdict must now state the true direction and must NOT claim the
    # Mariners have more.
    judge.check("more_events_verdict",
                "sounders" in answer.casefold() and "more" in answer.casefold()
                and not re.search(r"mariners\s+(?:have|has|had)\s+more", answer, re.I),
                "answer must state the Seattle Sounders FC have more upcoming events "
                "(5 vs the Mariners' 2); claiming the Mariners have more is false")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
