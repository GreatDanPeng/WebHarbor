#!/usr/bin/env python3
"""Verify Tumblr--1.

Explore today's trending posts. Report the blog name and note count of the
first trending post on the Explore page, then open that post and report its
like count and reblog count. Return to Explore, go to page 2, and report the
blog name, note count, and opening words of the first post there, plus its
first two tags. Then open that blog and report its exact title, total post
count, and when it was last updated.

audit rail: the page-2 blog component (title/posts/updated) deepens the task
so the honest walk stays above the 15-step depth bar; anchors frozen from
the rendered pages (sparth: SPARTH / 713 posts / Updated 7 days ago).
"""
from verify_lib import (Judge, check_read_only, check_trajectory_identity,
                        contains_all, contains_any, contains_number,
                        contains_phrase, final_answer, navigated_path,
                        navigated_to, run_verifier, visited_permalink)

TASK_ID = "Tumblr--1"

FIRST_BLOG = "meolog"
FIRST_POST_ID = "817505727903137792"
FIRST_NOTES = 3404
OPENED_LIKES = 2217
OPENED_REBLOGS = 1172
PAGE2_BLOG = "sparth"
PAGE2_POST_ID = "828074392064032769"
PAGE2_NOTES = 2926
PAGE2_OPENING = "spaceships in red and white paper"
PAGE2_TAGS = ("concept art", "art")
PAGE2_BLOG_TITLE = "sparth"
PAGE2_BLOG_POSTS = 713
PAGE2_BLOG_UPDATED = "7 days ago"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("visited_explore", navigated_path(traj, "/explore"),
                "required: /explore")
    judge.check("opened_first_trending_post",
               visited_permalink(traj, FIRST_BLOG, FIRST_POST_ID),
               f"required: /blog/{FIRST_BLOG}/{FIRST_POST_ID}")
    judge.check("visited_explore_page2",
               any("/explore" in u and "page=2" in u for u in
                   [s.get("url", "") for s in traj.get("steps") or [] if isinstance(s, dict)]
                   + [traj.get("final_url", "")]),
               "required: /explore?page=2")

    judge.check("answer_first_blog", contains_phrase(answer, FIRST_BLOG),
                "expected the first trending blog meolog")
    judge.check("answer_first_notes",
                contains_number(answer, FIRST_NOTES) or "3.4k" in answer.lower(),
                "expected 3.4K notes (3,404) for the first trending post")
    judge.check("answer_opened_likes", contains_number(answer, OPENED_LIKES),
                "expected 2,217 likes on the opened post")
    judge.check("answer_opened_reblogs", contains_number(answer, OPENED_REBLOGS),
                "expected 1,172 reblogs on the opened post")
    judge.check("answer_page2_blog", contains_phrase(answer, PAGE2_BLOG),
                "expected the page-2 first post blog sparth")
    judge.check("answer_page2_notes",
                contains_number(answer, PAGE2_NOTES) or "2.9k" in answer.lower(),
                "expected 2.9K notes (2,926) for the page-2 first post")
    judge.check("answer_page2_opening",
                contains_phrase(answer, PAGE2_OPENING),
                "expected the opening words 'spaceships in red and white paper…'")
    judge.check("answer_page2_tags",
                contains_all(answer, [f"#{PAGE2_TAGS[0]}", f"#{PAGE2_TAGS[1]}"]),
                "expected the first two tags #concept art and #art")
    judge.check("visited_page2_blog",
                navigated_path(traj, f"/blog/{PAGE2_BLOG}"),
                "required: /blog/sparth (the page-2 first post's blog)")
    judge.check("answer_page2_blog_title",
                contains_phrase(answer, PAGE2_BLOG_TITLE),
                "expected the sparth blog title SPARTH")
    judge.check("answer_page2_blog_posts",
                contains_number(answer, PAGE2_BLOG_POSTS),
                "expected the sparth blog post count 713 posts")
    judge.check("answer_page2_blog_updated",
                contains_phrase(answer, PAGE2_BLOG_UPDATED),
                "expected the sparth blog 'Updated 7 days ago' label")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
