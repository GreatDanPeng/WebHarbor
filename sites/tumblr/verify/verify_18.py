#!/usr/bin/env python3
"""Verify Tumblr--18.

Sign in as Alice (alice.j@test.com / TestPass123!) and create a quote post
quoting 'Art is the only way to run away without leaving home.' attributed to
Twyla Tharp, with the tag quotes. Publish it, then open your blog page and
report the quote, its source, and the tag shown on the post.

State contract: one posts row (alice-j, user-created quote post with the
quote/source and tags [quotes]) and alice-j's posts_count bumped by one.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_phrase, db_query, entered_identity,
                        final_answer, navigated_path, run_verifier)

TASK_ID = "Tumblr--18"

EMAIL = "alice.j@test.com"
QUOTE = "art is the only way to run away without leaving home"
SOURCE = "twyla tharp"
TAG = "#quotes"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_alice_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_composer", navigated_path(traj, "/new/post"),
                "required: /new/post")
    judge.check("quote_tab_used",
                any("type=quote" in str(s.get("url", "")) for s in
                    traj.get("steps") or [] if isinstance(s, dict)),
                "required: the composer's Quote tab")
    judge.check("typed_quote",
                any(QUOTE[:30] in t.lower() for t in
                    [(s.get("params") or {}).get("text", "") for s in
                     traj.get("steps") or [] if isinstance(s, dict)]),
                "required: the quote text typed into the composer")
    judge.check("typed_source",
                any(SOURCE in t.lower() for t in
                    [(s.get("params") or {}).get("text", "") for s in
                     traj.get("steps") or [] if isinstance(s, dict)]),
                "required: the source 'Twyla Tharp'")
    judge.check("visited_own_blog", navigated_path(traj, "/blog/alice-j"),
                "required: /blog/alice-j after publishing")

    judge.check("answer_quote", contains_phrase(answer, QUOTE),
                "expected the quote 'Art is the only way to run away without "
                "leaving home.'")
    judge.check("answer_source", contains_phrase(answer, SOURCE),
                "expected the source Twyla Tharp")
    judge.check("answer_tag", contains_phrase(answer, TAG),
                "expected the tag #quotes on the post")

    # ---- DB after-state: exactly the new quote post.
    alice_blog = db_query(initial_db,
                          "SELECT id, posts_count FROM blogs WHERE name = 'alice-j'")[0]
    init_posts = {r["id"] for r in db_query(initial_db, "SELECT id FROM posts")}
    added = [p for p in db_query(after_db, "SELECT * FROM posts")
             if p["id"] not in init_posts]
    judge.check("one_post_added", len(added) == 1,
                f"added posts={[p['id'] for p in added]!r}")
    if added:
        p = added[0]
        judge.check("post_on_alice_blog",
                    p["blog_id"] == alice_blog["id"] and p["user_created"] == 1,
                    f"blog_id={p['blog_id']} type={p['type']}")
        judge.check("post_is_quote_type", p["type"] == "quote",
                    f"type={p['type']!r}")
        judge.check("quote_recorded",
                    QUOTE[:30] in (p["content"] or "").lower(),
                    f"content={ (p['content'] or '')[:90]!r}")
        judge.check("source_recorded",
                    SOURCE in (p["content"] or "").lower(),
                    "the source must be recorded on the post")
        judge.check("tag_recorded", '"quotes"' in (p["tags"] or ""),
                    f"tags={p['tags']!r}")
    after_count = db_query(after_db, "SELECT posts_count FROM blogs WHERE id = ?",
                           (alice_blog["id"],))[0]["posts_count"]
    judge.check("alice_posts_count_bumped",
                after_count == alice_blog["posts_count"] + 1,
                f"posts_count {alice_blog['posts_count']} -> {after_count}")
    changed = changed_tables(initial_db, after_db)
    judge.check("only_expected_tables_changed",
                set(changed) <= {"posts", "blogs"},
                f"unexpected deltas: {changed!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
