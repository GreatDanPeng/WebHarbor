#!/usr/bin/env python3
"""Verify Tumblr--8.

Sign in as Alice (alice.j@test.com / TestPass123!) and open your dashboard.
Report how many posts the first page shows, the names of every blog appearing
on that page, and the summary and note count of the newest post. Then open
that newest post and report its like count, reblog count, and total note
count. Finally open the second post on the page and report its blog name,
note count, and first tag.

audit rail: the second-dashboard-post component deepens the task above the
15-step depth bar; anchors frozen from the rendered dashboard (second card:
nasa 'Autumn is a second spring…' 5.6K notes on the card / 5,594 live on the
permalink, first tag #nasa).
"""
from verify_lib import (Judge, SEED_USERS, check_read_only,
                        check_trajectory_identity, contains_all,
                        contains_number, contains_phrase, entered_identity,
                        final_answer, navigated_path, run_verifier,
                        visited_permalink)

TASK_ID = "Tumblr--8"

EMAIL = "alice.j@test.com"
DASH_POSTS = 8
DASH_BLOGS = ("meolog", "nasa", "staff", "waneella")
NEWEST_BLOG = "meolog"
NEWEST_POST_ID = "828475230982930432"
NEWEST_SUMMARY = "Kodak Ektar 100"
NEWEST_NOTES = 556
# The post's raw like count is 395; the permalink notes tab shows 396 for
# Alice (her own seeded like is included), same display duality as T9.
OPENED_LIKES = (395, 396)
OPENED_REBLOGS = 155
OPENED_NOTES = 556
SECOND_POST_BLOG = "nasa"
SECOND_POST_ID = "828471464226406400"
SECOND_POST_NOTES = 5592          # frozen note_count
SECOND_POST_NOTES_LIVE = 5594     # live count on the permalink (seeded likes)
SECOND_POST_NOTES_CARD = "5.6k"   # compact count on the dashboard card
SECOND_POST_FIRST_TAG = "#nasa"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_alice_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_dashboard", navigated_path(traj, "/dashboard"),
                "required: /dashboard after login")
    judge.check("opened_newest_post",
               visited_permalink(traj, NEWEST_BLOG, NEWEST_POST_ID),
               f"required: /blog/{NEWEST_BLOG}/{NEWEST_POST_ID}")
    judge.check("opened_second_post",
                visited_permalink(traj, SECOND_POST_BLOG, SECOND_POST_ID),
                f"required: /blog/{SECOND_POST_BLOG}/{SECOND_POST_ID} "
                "(the second post on the dashboard)")

    judge.check("answer_page_posts_8", contains_number(answer, DASH_POSTS),
                "expected 8 posts on the first dashboard page")
    judge.check("answer_dash_blogs", contains_all(answer, DASH_BLOGS),
                f"expected the blogs {DASH_BLOGS}")
    judge.check("answer_newest_summary",
                contains_phrase(answer, NEWEST_SUMMARY),
                "expected the newest post 'Kodak Ektar 100'")
    judge.check("answer_newest_notes_556", contains_number(answer, NEWEST_NOTES),
                "expected 556 notes on the newest post")
    judge.check("answer_opened_likes_395",
                any(contains_number(answer, v) for v in OPENED_LIKES),
                "expected 395 likes on the opened post (396 where the notes "
                "tab includes Alice's own like)")
    judge.check("answer_opened_reblogs_155",
                contains_number(answer, OPENED_REBLOGS),
                "expected 155 reblogs on the opened post")
    judge.check("answer_opened_notes_556",
                contains_number(answer, OPENED_NOTES),
                "expected 556 total notes on the opened post")
    judge.check("answer_second_blog",
                contains_phrase(answer, SECOND_POST_BLOG),
                "expected the second dashboard post to be by nasa")
    judge.check("answer_second_notes",
                any(contains_number(answer, v) for v in
                    (SECOND_POST_NOTES, SECOND_POST_NOTES_LIVE))
                or SECOND_POST_NOTES_CARD in answer.lower(),
                "expected 5,592 notes on the second dashboard post "
                "(5.6K on the card / 5,594 live on the permalink)")
    judge.check("answer_second_first_tag",
                contains_phrase(answer, SECOND_POST_FIRST_TAG),
                "expected the second dashboard post's first tag #nasa")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
