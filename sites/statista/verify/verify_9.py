#!/usr/bin/env python3
"""Verify Statista--9.

I'm writing a paper and need proper citations. Find Statista's statistic about the average inflation rate worldwide, open its citations, and give me the full APA citation including the publisher and the cited URL, plus the MLA citation for the same statistic, and tell me the survey time period shown on the page.
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "Statista--9"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_search", r"/serp\?q=average\+inflation\+rate\+worldwide")
    check_visited_path(judge, traj, "visited_statistic", r"/statistics/256598/")
    check_visited_path(judge, traj, "visited_apa_citation", r"citation=APA")
    check_visited_path(judge, traj, "visited_mla_citation", r"citation=MLA")
    check_answer_phrase(judge, answer, "publisher", "Statista Research Department")
    check_answer_phrase(judge, answer, "cited_url", "https://www.statista.com/statistics/256598/global-inflation-rate-compared-to-previous-year/")
    check_answer_phrase(judge, answer, "survey_start", "01/01/1980")
    check_answer_phrase(judge, answer, "survey_end", "31/12/2031")
    check_answer_phrase(judge, answer, "apa_named", "APA")
    check_answer_phrase(judge, answer, "mla_named", "MLA")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
