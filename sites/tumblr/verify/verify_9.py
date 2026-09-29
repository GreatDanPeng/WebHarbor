#!/usr/bin/env python3
"""Verify Tumblr--9.

Sign in as Alice (alice.j@test.com / TestPass123!) and open your Likes page.
Report how many posts you have liked in total and, for the most recent one,
the posting blog, its summary, and its note count. Then open that post and
report its first tag, like count, reblog count, and total note count.

NOTE (r2, ab8382a9): the Likes page head now shows the total explicitly
("11 liked posts in total"). The like count of the opened post displays as
9,446 (Post details) or 9,447 (notes tab, including Alice's own like); both
are accepted.
"""
from verify_lib import (Judge, check_read_only, check_trajectory_identity,
                        contains_number, contains_phrase, entered_identity,
                        final_answer, navigated_path, run_verifier,
                        visited_permalink)

TASK_ID = "Tumblr--9"

EMAIL = "alice.j@test.com"
TOTAL_LIKED = 11
RECENT_BLOG = "staff"
RECENT_POST_ID = "822057428507049984"
RECENT_SUMMARY = "blog that's gone missing"
RECENT_NOTES_CARD = 12  # card shows 12K
OPENED_FIRST_TAG = "#tumblr"
OPENED_NOTES = 12381
OPENED_LIKES = (9446, 9447)
OPENED_REBLOGS = 2092


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_alice_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_likes", navigated_path(traj, "/likes"),
                "required: /likes")
    judge.check("opened_most_recent_like",
               visited_permalink(traj, RECENT_BLOG, RECENT_POST_ID),
               f"required: /blog/{RECENT_BLOG}/{RECENT_POST_ID}")

    judge.check("answer_total_liked_11", contains_number(answer, TOTAL_LIKED),
                "expected 11 liked posts in total")
    judge.check("answer_recent_blog", contains_phrase(answer, RECENT_BLOG),
                "expected the most recent liked post to be from staff")
    judge.check("answer_recent_summary",
                contains_phrase(answer, RECENT_SUMMARY),
                "expected the summary 'In case you're looking for a blog that's "
                "gone missing on Tumblr…'")
    judge.check("answer_recent_notes",
                contains_number(answer, OPENED_NOTES) or "12k" in answer.lower(),
                "expected 12,381 notes (12K on the card)")
    judge.check("answer_first_tag", contains_phrase(answer, OPENED_FIRST_TAG),
                "expected the first tag #tumblr")
    judge.check("answer_opened_likes",
                contains_number(answer, OPENED_LIKES[0])
                or contains_number(answer, OPENED_LIKES[1]),
                "expected 9,446/9,447 likes")
    judge.check("answer_opened_reblogs",
                contains_number(answer, OPENED_REBLOGS),
                "expected 2,092 reblogs")
    judge.check("answer_opened_notes",
                contains_number(answer, OPENED_NOTES),
                "expected 12,381 total notes")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
