#!/usr/bin/env python3
"""Verify Tumblr--19.

Sign in as Bob (bob.c@test.com / TestPass123!). In settings, change your
blog title to 'bob's art lab' and save. Then open your blog page and report
the new title exactly as displayed, your blog's username, how many posts it
shows, and the summary of its newest post. Finally open your blog's archive
and report the newest month shown.

State contract: the bob-c blog row's title becomes "bob's art lab"; nothing
else changes.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_number, contains_phrase, db_query,
                        entered_identity, final_answer, navigated_path,
                        run_verifier)

TASK_ID = "Tumblr--19"

EMAIL = "bob.c@test.com"
NEW_TITLE = "bob's art lab"
USERNAME = "bob-c"
POSTS_COUNT = 3
NEWEST_SUMMARY = "shapes shapes shapes"
ARCHIVE_NEWEST_MONTH = "September 2026"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_bob_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_settings", navigated_path(traj, "/settings"),
                "required: /settings")
    judge.check("typed_new_title",
                any("art lab" in t.lower() for t in
                    [(s.get("params") or {}).get("text", "") for s in
                     traj.get("steps") or [] if isinstance(s, dict)]),
                "required: the new title typed into the settings form")
    judge.check("visited_own_blog", navigated_path(traj, f"/blog/{USERNAME}"),
                "required: /blog/bob-c after saving")
    judge.check("visited_archive",
                navigated_path(traj, f"/blog/{USERNAME}/archive"),
                "required: /blog/bob-c/archive")

    judge.check("answer_new_title", contains_phrase(answer, NEW_TITLE),
                "expected the new title 'bob's art lab'")
    judge.check("answer_username", contains_phrase(answer, USERNAME),
                "expected the username bob-c")
    judge.check("answer_posts_count", contains_number(answer, POSTS_COUNT),
                "expected 3 posts on the blog")
    judge.check("answer_newest_summary",
                contains_phrase(answer, NEWEST_SUMMARY),
                "expected the newest post 'shapes shapes shapes'")
    judge.check("answer_archive_month",
                contains_phrase(answer, ARCHIVE_NEWEST_MONTH),
                "expected September 2026 as the newest archive month")

    # ---- DB after-state: only the blog title changed.
    changed = changed_tables(initial_db, after_db)
    judge.check("only_blogs_changed", changed == ["blogs"],
                f"unexpected deltas: {changed!r}")
    init_blog = db_query(initial_db, "SELECT * FROM blogs WHERE name = ?",
                         (USERNAME,))[0]
    after_blog = db_query(after_db, "SELECT * FROM blogs WHERE name = ?",
                          (USERNAME,))[0]
    diffs = {k: (init_blog[k], after_blog[k]) for k in init_blog
             if init_blog[k] != after_blog[k]}
    judge.check("title_is_only_blog_diff",
                set(diffs) == {"title"} and diffs["title"][1] == NEW_TITLE,
                f"blog row diffs: {diffs!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
