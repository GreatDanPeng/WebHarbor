#!/usr/bin/env python3
"""Verify Tumblr--2.

Search for 'pixel art'. Report how many results the Top tab shows, and the
names of the first two blogs in the Blogs matching sidebar. Open the first
matching blog and report its exact title, its post count, and one phrase from
its description. Then switch to the Recent tab and report the blog name of
the newest post and its note count. Open that post and report its first two
tags and its like count.

audit rail: the first-matching-blog component (title/posts/description)
deepens the task above the 15-step depth bar; anchors frozen from the
rendered blog page (8pxl: PIXEL ART BY @SOFTWARING / 2,155 posts /
description 'PIXEL ARTIST … MTG ARTIST').
"""
from verify_lib import (Judge, check_read_only, check_trajectory_identity,
                        contains_all, contains_number, contains_phrase,
                        final_answer, navigated_path, navigated_search,
                        run_verifier, visited_permalink)

TASK_ID = "Tumblr--2"

QUERY = "pixel art"
TOP_RESULTS = 13
BLOG1 = "8pxl"
BLOG2 = "perplexi"
RECENT_BLOG = "wqonart"
RECENT_POST_ID = "829013306919501824"
RECENT_NOTES = 0
OPENED_TAGS = ("Septembit", "Septembit2026")
OPENED_LIKES = 0
FIRST_MATCH_TITLE = "pixel art by @softwaring"
FIRST_MATCH_POSTS = 2155
FIRST_MATCH_DESC_SNIPPET = "pixel artist"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("searched_pixel_art", navigated_search(traj, QUERY),
                "required: /search/pixel art")
    judge.check("visited_recent_tab",
                any("tab=recent" in u for u in
                    [s.get("url", "") for s in traj.get("steps") or [] if isinstance(s, dict)]),
                "required: the Recent tab (tab=recent)")
    judge.check("opened_newest_post",
               visited_permalink(traj, RECENT_BLOG, RECENT_POST_ID),
               f"required: /blog/{RECENT_BLOG}/{RECENT_POST_ID}")
    judge.check("visited_first_matching_blog",
                navigated_path(traj, f"/blog/{BLOG1}"),
                "required: /blog/8pxl (the first matching blog)")

    judge.check("answer_top_results_13", contains_number(answer, TOP_RESULTS),
                "expected 13 results on the Top tab")
    judge.check("answer_blog1_8pxl", contains_phrase(answer, BLOG1),
                "expected the first matching blog 8pxl")
    judge.check("answer_blog2_perplexi", contains_phrase(answer, BLOG2),
                "expected the second matching blog perplexi")
    judge.check("answer_first_match_title",
                contains_phrase(answer, FIRST_MATCH_TITLE),
                "expected the 8pxl blog title PIXEL ART BY @SOFTWARING")
    judge.check("answer_first_match_posts",
                contains_number(answer, FIRST_MATCH_POSTS),
                "expected the 8pxl blog post count 2,155 posts")
    judge.check("answer_first_match_description",
                contains_phrase(answer, FIRST_MATCH_DESC_SNIPPET),
                "expected a phrase from the 8pxl description (e.g. PIXEL "
                "ARTIST / MTG ARTIST)")
    judge.check("answer_recent_blog", contains_phrase(answer, RECENT_BLOG),
                "expected the newest Recent-tab post blog wqonart")
    judge.check("answer_recent_notes_0", contains_number(answer, RECENT_NOTES),
                "expected 0 notes on the newest Recent post")
    judge.check("answer_opened_tags",
                contains_all(answer, [f"#{OPENED_TAGS[0]}", f"#{OPENED_TAGS[1]}"]),
                "expected the tags #Septembit and #Septembit2026")
    judge.check("answer_opened_likes_0", contains_number(answer, OPENED_LIKES),
                "expected 0 likes on the opened post")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
