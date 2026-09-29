#!/usr/bin/env python3
"""Verify Tumblr--17.

Sign in as Carol (carol.d@test.com / TestPass123!) and create a text post
titled 'Cabin Wishlist, Part Two' with at least one sentence about a wood
stove and the tags cottagecore and wishlist. Publish it, then open your blog
page and report the post's title, its tags, and confirm the first tag links
to a tag page with posts on it.

State contract: one posts row (carol-d, user-created text post with the
title/wood-stove body and tags [cottagecore, wishlist]) and carol-d's
posts_count bumped by one.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_all, contains_number, contains_phrase,
                        db_query, entered_identity, final_answer,
                        navigated_path, run_verifier)

TASK_ID = "Tumblr--17"

EMAIL = "carol.d@test.com"
TITLE = "Cabin Wishlist, Part Two"
BODY_KEYWORD = "wood stove"
TAGS = ("cottagecore", "wishlist")
TAG_PAGE_POSTS = 10  # visible posts on the tagged page (11 total)


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_carol_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_composer", navigated_path(traj, "/new/post"),
                "required: /new/post")
    judge.check("typed_title",
                any(TITLE.lower() in t.lower() for t in
                    [(s.get("params") or {}).get("text", "") for s in
                     traj.get("steps") or [] if isinstance(s, dict)]),
                f"required: the title '{TITLE}' typed into the composer")
    judge.check("typed_body",
                any(BODY_KEYWORD in t.lower() for t in
                    [(s.get("params") or {}).get("text", "") for s in
                     traj.get("steps") or [] if isinstance(s, dict)]),
                "required: a body sentence mentioning the wood stove")
    judge.check("typed_tags",
                any("cottagecore" in t and "wishlist" in t for t in
                    [(s.get("params") or {}).get("text", "") for s in
                     traj.get("steps") or [] if isinstance(s, dict)]),
                "required: the tags 'cottagecore, wishlist'")
    judge.check("visited_own_blog", navigated_path(traj, "/blog/carol-d"),
                "required: /blog/carol-d after publishing")
    judge.check("visited_tag_page",
                navigated_path(traj, "/tagged/cottagecore"),
                "required: /tagged/cottagecore via the first tag link")

    judge.check("answer_title", contains_phrase(answer, TITLE),
                "expected the post title 'Cabin Wishlist, Part Two'")
    judge.check("answer_tags",
                contains_all(answer, [f"#{TAGS[0]}", f"#{TAGS[1]}"]),
                "expected the tags #cottagecore and #wishlist")
    judge.check("answer_tag_page_has_posts",
                contains_number(answer, TAG_PAGE_POSTS)
                or contains_number(answer, TAG_PAGE_POSTS + 1)
                or contains_phrase(answer, "posts"),
                "expected the cottagecore tag page to show posts")

    # ---- DB after-state: exactly the new post.
    carol_blog = db_query(initial_db,
                          "SELECT id, posts_count FROM blogs WHERE name = 'carol-d'")[0]
    init_posts = {r["id"] for r in db_query(initial_db, "SELECT id FROM posts")}
    added = [p for p in db_query(after_db, "SELECT * FROM posts")
             if p["id"] not in init_posts]
    judge.check("one_post_added", len(added) == 1,
                f"added posts={[p['id'] for p in added]!r}")
    if added:
        p = added[0]
        judge.check("post_on_carol_blog",
                    p["blog_id"] == carol_blog["id"] and p["user_created"] == 1,
                    f"blog_id={p['blog_id']} user_created={p['user_created']}")
        judge.check("post_title_recorded",
                    TITLE.lower() in ((p["content"] or "") + (p["summary"] or "")).lower(),
                    f"content={ (p['content'] or '')[:100]!r}")
        judge.check("post_tags_recorded",
                    '"cottagecore"' in (p["tags"] or "")
                    and '"wishlist"' in (p["tags"] or ""),
                    f"tags={p['tags']!r}")
    after_count = db_query(after_db, "SELECT posts_count FROM blogs WHERE id = ?",
                           (carol_blog["id"],))[0]["posts_count"]
    judge.check("carol_posts_count_bumped",
                after_count == carol_blog["posts_count"] + 1,
                f"posts_count {carol_blog['posts_count']} -> {after_count}")
    changed = changed_tables(initial_db, after_db)
    judge.check("only_expected_tables_changed",
                set(changed) <= {"posts", "blogs"},
                f"unexpected deltas: {changed!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
