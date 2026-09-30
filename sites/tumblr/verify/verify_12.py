#!/usr/bin/env python3
"""Verify Tumblr--12.

Sign in as Carol (carol.d@test.com / TestPass123!). From your Following page,
open the pixel-art blog you follow, then open its newest post and reblog it
with the exact comment 'someday.'. Finally visit your own blog page and
report: the original post's blog, the comment shown on your reblog, and the
tags carried over.

NOTE (reviewer): the reblogged waneella post 'Shimmer' carries no tags (also
true upstream), so the honest 'tags carried over' answer is none; the
verifier asserts the empty tag list on the created reblog row instead of a
fragile absence-phrase match.

State contract: exactly one posts row (carol-d reblog of 827616468115079168,
user_created, trail from waneella), one reblogs row, and carol-d's
posts_count bumped by one.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_phrase, db_query, entered_identity,
                        final_answer, navigated_path, run_verifier,
                        visited_permalink)

TASK_ID = "Tumblr--12"

EMAIL = "carol.d@test.com"
SOURCE_BLOG = "waneella"
SOURCE_POST_ID = "827616468115079168"
COMMENT = "someday."


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_carol_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_following", navigated_path(traj, "/following"),
                "required: /following")
    judge.check("opened_waneella_blog",
                navigated_path(traj, f"/blog/{SOURCE_BLOG}"),
                "required: /blog/waneella (the pixel-art blog)")
    judge.check("opened_newest_post",
               visited_permalink(traj, SOURCE_BLOG, SOURCE_POST_ID),
               f"required: /blog/waneella/{SOURCE_POST_ID}")
    judge.check("visited_reblog_form",
                any(f"/post/{SOURCE_POST_ID}/reblog" in str(s.get("url", ""))
                    for s in traj.get("steps") or [] if isinstance(s, dict)),
                "required: the reblog form for the newest post")
    judge.check("typed_comment_someday",
                any("someday." in t for t in
                    [(s.get("params") or {}).get("text", "")
                     for s in traj.get("steps") or [] if isinstance(s, dict)])
                or any("someday." in str(s.get("detail", "")) for s in
                       traj.get("steps") or [] if isinstance(s, dict)),
                "required: the exact comment 'someday.' typed into the form")
    carol_blog = db_query(initial_db, "SELECT id, posts_count FROM blogs "
                          "WHERE name = 'carol-d'")[0]
    judge.check("visited_own_blog",
                navigated_path(traj, "/blog/carol-d"),
                "required: /blog/carol-d after the reblog")

    judge.check("answer_original_blog_waneella",
                contains_phrase(answer, SOURCE_BLOG),
                "expected waneella as the original post's blog")
    judge.check("answer_comment_someday", contains_phrase(answer, "someday."),
                "expected the comment 'someday.' on the reblog")

    # ---- DB after-state: exactly the reblog delta.
    init_posts = {r["id"] for r in db_query(initial_db, "SELECT id FROM posts")}
    after_posts = db_query(after_db, "SELECT * FROM posts")
    added = [p for p in after_posts if p["id"] not in init_posts]
    judge.check("one_post_added", len(added) == 1,
                f"added posts={[p['id'] for p in added]!r}")
    if added:
        p = added[0]
        judge.check("reblog_on_carol_blog",
                    p["blog_id"] == carol_blog["id"]
                    and p["reblog_of_id"] == SOURCE_POST_ID
                    and p["user_created"] == 1,
                    f"post row: blog_id={p['blog_id']} reblog_of={p['reblog_of_id']}")
        judge.check("reblog_trail_waneella", "waneella" in (p["trail"] or ""),
                    "the reblog trail must carry waneella")
        judge.check("reblog_comment_someday",
                    "someday." in (p["content"] or ""),
                    f"content={ (p['content'] or '')[:80]!r}")
        judge.check("reblog_no_tags_carried",
                    (p["tags"] or "[]").strip() in ("[]", ""),
                    f"tags={p['tags']!r} — the source post has no tags")
    init_reblogs = {r["source_post_id"] for r in
                    db_query(initial_db, "SELECT source_post_id FROM reblogs")}
    after_reblogs = db_query(after_db, "SELECT * FROM reblogs")
    new_reblogs = [r for r in after_reblogs
                   if r["source_post_id"] not in init_reblogs
                   or r["id"] not in {x["id"] for x in db_query(initial_db, "SELECT * FROM reblogs")}]
    judge.check("one_reblog_row",
                len(new_reblogs) == 1 and new_reblogs[0]["source_post_id"] == SOURCE_POST_ID,
                f"reblog rows added={[r['id'] for r in new_reblogs]!r}")
    after_count = db_query(after_db, "SELECT posts_count FROM blogs WHERE id = ?",
                           (carol_blog["id"],))[0]["posts_count"]
    judge.check("carol_posts_count_bumped",
                after_count == carol_blog["posts_count"] + 1,
                f"posts_count {carol_blog['posts_count']} -> {after_count}")
    changed = changed_tables(initial_db, after_db)
    judge.check("only_expected_tables_changed",
                set(changed) <= {"posts", "reblogs", "blogs"},
                f"unexpected deltas: {changed!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
