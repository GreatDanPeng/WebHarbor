#!/usr/bin/env python3
"""Verify Tumblr--4.

Search for the Tumblr Staff post announcing that reblogs in a chain now get
their own notes. Open it and report the exact note count, like count and
reblog count shown, plus the post's opening line. List the usernames of the
two most recent likers and the first reblog shown in its notes. Then open the
posting blog and report its title, total post count, and when it was last
updated, and open its newest post and report the first tag on that post.

r2 (ab8382a9): the announcement post itself carries no tags (on the mirror
and upstream), so the first-tag component was re-anchored on the posting
blog's newest post ('Premium just got better', first tag 'tumblr premium'),
which is a real tagged post on both the mirror and upstream.
"""
from verify_lib import (Judge, check_read_only, check_trajectory_identity,
                        contains_all, contains_number, contains_phrase,
                        final_answer, navigated_path, navigated_search,
                        run_verifier, visited_permalink)

TASK_ID = "Tumblr--4"

POST_ID = "811288138350821376"
BLOG = "staff"
NOTES = 319748
LIKES = 101183
REBLOGS = 168847
OPENING = "reblogs in a chain now get their own notes"
LIKERS = ("suipearlgloss", "orlissegrapeangel")
FIRST_REBLOG = "sooopap"
BLOG_TITLE = "Tumblr Staff"
BLOG_POSTS = 2989
BLOG_UPDATED = "10 days ago"
NEWEST_POST_ID = "828009069026721792"
NEWEST_POST_FIRST_TAG = "tumblr premium"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("searched_reblog_chain",
                navigated_search(traj, "reblogs in a chain")
                or navigated_search(traj, "reblogs in a chain now get their own notes")
                or any("reblogs" in u.lower() and "/search/" in u
                       for u in [str(s.get("url", "")) for s in traj.get("steps") or []
                                 if isinstance(s, dict)]),
                "required: search for the reblog-chain announcement")
    judge.check("opened_staff_post", visited_permalink(traj, BLOG, POST_ID),
                f"required: /blog/staff/{POST_ID}")
    judge.check("visited_staff_blog", navigated_path(traj, f"/blog/{BLOG}"),
                "required: /blog/staff")
    judge.check("opened_staff_newest_post",
               visited_permalink(traj, BLOG, NEWEST_POST_ID),
               f"required: /blog/staff/{NEWEST_POST_ID} (the blog's newest "
               "post, where the first tag is read)")

    judge.check("answer_notes_319748", contains_number(answer, NOTES),
                "expected 319,748 notes")
    judge.check("answer_likes_101183", contains_number(answer, LIKES),
                "expected 101,183 likes")
    judge.check("answer_reblogs_168847", contains_number(answer, REBLOGS),
                "expected 168,847 reblogs")
    judge.check("answer_opening_line", contains_phrase(answer, OPENING),
                "expected the opening line 'Reblogs in a chain now get their own notes'")
    judge.check("answer_two_likers", contains_all(answer, LIKERS),
                f"expected the likers {LIKERS}")
    judge.check("answer_first_reblog", contains_phrase(answer, FIRST_REBLOG),
                "expected sooopap as the first reblog in the notes")
    judge.check("answer_blog_title", contains_phrase(answer, BLOG_TITLE),
                "expected the blog title Tumblr Staff")
    judge.check("answer_blog_posts_2989", contains_number(answer, BLOG_POSTS),
                "expected 2,989 posts on the staff blog")
    judge.check("answer_blog_updated",
                contains_phrase(answer, BLOG_UPDATED)
                or contains_phrase(answer, "updated 10 days"),
                "expected 'Updated 10 days ago'")
    judge.check("answer_newest_first_tag",
                contains_phrase(answer, NEWEST_POST_FIRST_TAG),
                "expected the first tag 'tumblr premium' on the staff blog's "
                "newest post")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
