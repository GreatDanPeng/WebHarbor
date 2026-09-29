#!/usr/bin/env python3
"""Verify Tumblr--0.

Start from the Tumblr home page and open the most-followed tag in the Popular
tags panel. Report that tag's follower count, today's new-post count, and its
editorial description in one sentence. Open the first related tag in the
sidebar and report its name and new-post count. Come back, open the newest
post in the tag's feed, and report the posting blog, its note count, and the
first tag on that post. Then open that blog and report its post count.

r2 (ab8382a9): the tag hubs now carry the real editorial descriptions frozen
from the live tagged pages (six of the twelve hubs serve one upstream; the
#photography hub does), so the editorial component is gradeable.
"""
from verify_lib import (Judge, check_read_only, check_trajectory_identity,
                        contains_all, contains_any, contains_number,
                        contains_phrase, final_answer, navigated_path,
                        navigated_search, navigated_to, run_verifier,
                        visited_permalink)

TASK_ID = "Tumblr--0"

TAG = "photography"
HUB_FOLLOWERS = "43M"
HUB_NEW_POSTS = "2.4K"
RELATED_TAG = "photographer"
RELATED_NEW = "61"
NEWEST_POST_BLOG = "arainthepara"
NEWEST_POST_ID = "829013305812205568"
NEWEST_POST_NOTES = 0
NEWEST_POST_FIRST_TAG = "photography"
BLOG_POST_COUNT = 1
EDITORIAL_SNIPPET = "photography takes precedence over words"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("visited_home", navigated_to(traj, "/") or navigated_to(traj, ""),
                "the run must start from the home page")
    judge.check("visited_tag_hub_photography",
               navigated_path(traj, f"/tagged/{TAG}"),
                "required: /tagged/photography")
    judge.check("visited_related_tag",
               navigated_path(traj, f"/tagged/{RELATED_TAG}"),
                "required: /tagged/photographer (first related tag)")
    judge.check("opened_newest_post",
               visited_permalink(traj, NEWEST_POST_BLOG, NEWEST_POST_ID),
                f"required: /blog/{NEWEST_POST_BLOG}/{NEWEST_POST_ID}")
    judge.check("visited_blog_page", navigated_path(traj, f"/blog/{NEWEST_POST_BLOG}"),
                f"required: /blog/{NEWEST_POST_BLOG}")

    judge.check("answer_tag", contains_phrase(answer, f"#{TAG}")
                or contains_phrase(answer, TAG), "expected the tag #photography")
    judge.check("answer_followers_43M",
                contains_all(answer, ["43m followers"]) or contains_number(answer, 43),
                "expected 43M followers")
    judge.check("answer_new_posts_2_4K",
                contains_any(answer, ["2.4k new posts", "2.4k new posts today",
                                      "2,400 new posts", "2.4k posts today"]),
                "expected 2.4K new posts today")
    judge.check("answer_editorial",
                contains_phrase(answer, EDITORIAL_SNIPPET),
                "expected the #photography editorial 'For those who prefer to "
                "show rather than tell, photography takes precedence over "
                "words'")
    judge.check("answer_related_tag", contains_phrase(answer, f"#{RELATED_TAG}")
                or contains_phrase(answer, RELATED_TAG),
                "expected the related tag #photographer")
    judge.check("answer_related_new_61",
                contains_number(answer, 61) or contains_number(answer, 62),
                "expected the #photographer new-post count 61 new "
                "(as shown on the related-tag row)")
    judge.check("answer_newest_blog", contains_phrase(answer, NEWEST_POST_BLOG),
                f"expected the posting blog {NEWEST_POST_BLOG}")
    judge.check("answer_newest_notes_0", contains_number(answer, NEWEST_POST_NOTES),
                "expected 0 notes on the newest tagged post")
    judge.check("answer_first_tag",
                contains_phrase(answer, f"#{NEWEST_POST_FIRST_TAG}"),
                "expected the first tag #photography on the post")
    judge.check("answer_blog_post_count", contains_number(answer, BLOG_POST_COUNT),
                "expected the arainthepara post count 1 post")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
