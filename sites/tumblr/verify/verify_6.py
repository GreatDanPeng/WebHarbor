#!/usr/bin/env python3
"""Verify Tumblr--6.

Search for 'flight test like a NASA engineer' and open the result titled
'Flight Test Like a NASA Engineer!'. Report the video provider shown under
the player on that post, the post's tags, and its note count, like count, and
reblog count. Then open the posting blog and report its title, total post
count, when it was last updated, and the newest month shown in its archive
with its number of posts.

r2 (ab8382a9): the task now pins the result by its unique visible title
('Flight Test Like a NASA Engineer!' — exactly one card on page 1 carries
it), removing the old search ambiguity (the post ranks sixth).
"""
from verify_lib import (Judge, check_read_only, check_trajectory_identity,
                        contains_all, contains_number, contains_phrase,
                        final_answer, navigated_path, navigated_search,
                        run_verifier, visited_permalink)

TASK_ID = "Tumblr--6"

POST_ID = "793768130342273024"
BLOG = "nasa"
PROVIDER = "video · tumblr"
TAGS = ("#nasa", "#space", "#science", "#technology")
NOTES = 582
LIKES = 459
REBLOGS = 117
TITLE_PHRASE = "flight test like a nasa engineer!"
BLOG_TITLE = "NASA"
BLOG_POSTS = 1759
BLOG_UPDATED = "5 days ago"
ARCHIVE_NEWEST_MONTH = "September 2026"
ARCHIVE_NEWEST_COUNT = 3


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("searched_flight_test",
                navigated_search(traj, "flight test like a NASA engineer")
                or any("/search/" in u and "nasa" in u.lower()
                       for u in [str(s.get("url", "")) for s in traj.get("steps") or []
                                 if isinstance(s, dict)]),
                "required: search for the NASA flight-test video post")
    judge.check("opened_titled_video_post", visited_permalink(traj, BLOG, POST_ID),
                f"required: /blog/nasa/{POST_ID} (the result titled "
                "'Flight Test Like a NASA Engineer!')")
    judge.check("visited_nasa_blog", navigated_path(traj, f"/blog/{BLOG}"),
                "required: /blog/nasa")
    judge.check("visited_nasa_archive",
                navigated_path(traj, f"/blog/{BLOG}/archive"),
                "required: /blog/nasa/archive")

    judge.check("answer_provider", contains_phrase(answer, PROVIDER)
                or contains_phrase(answer, "video · tumblr")
                or contains_phrase(answer, "video by tumblr"),
                "expected the provider 'Video · tumblr' under the player")
    judge.check("answer_tags", contains_all(answer, TAGS),
                "expected at least the tags #nasa #space #science #technology")
    judge.check("answer_notes_582", contains_number(answer, NOTES),
                "expected 582 notes")
    judge.check("answer_likes_459", contains_number(answer, LIKES),
                "expected 459 likes")
    judge.check("answer_reblogs_117", contains_number(answer, REBLOGS),
                "expected 117 reblogs")
    judge.check("answer_post_title", contains_phrase(answer, TITLE_PHRASE),
                "expected the post title 'Flight Test Like a NASA Engineer!'")
    judge.check("answer_blog_title", contains_phrase(answer, BLOG_TITLE),
                "expected the blog title NASA")
    judge.check("answer_blog_posts_1759", contains_number(answer, BLOG_POSTS),
                "expected 1,759 posts")
    judge.check("answer_blog_updated",
                contains_phrase(answer, BLOG_UPDATED)
                or contains_phrase(answer, "updated 5 days"),
                "expected 'Updated 5 days ago'")
    judge.check("answer_archive_newest_month",
                contains_phrase(answer, ARCHIVE_NEWEST_MONTH),
                "expected September 2026 as the newest archive month")
    judge.check("answer_archive_newest_count",
                contains_number(answer, ARCHIVE_NEWEST_COUNT),
                "expected 3 posts in September 2026")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
