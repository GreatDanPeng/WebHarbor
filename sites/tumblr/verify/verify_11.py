#!/usr/bin/env python3
"""Verify Tumblr--11.

Sign in as Bob (bob.c@test.com / TestPass123!). From Explore, open the first
trending post, note its current note count, and like it. Report the count
shown after liking. Then open your Likes page and confirm the post appears at
the top, reporting its summary and posting blog.

State contract: exactly one like row (bob, 817505727903137792) added and
nothing else.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_number, contains_phrase, db_query,
                        entered_identity, final_answer, like_pairs,
                        navigated_path, run_verifier, visited_permalink)

TASK_ID = "Tumblr--11"

EMAIL = "bob.c@test.com"
FIRST_BLOG = "meolog"
POST_ID = "817505727903137792"
NOTES_BEFORE = 3404
NOTES_AFTER = 3405
TOP_SUMMARY = "Rhododendron"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_bob_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_explore", navigated_path(traj, "/explore"),
                "required: /explore")
    judge.check("opened_first_trending",
               visited_permalink(traj, FIRST_BLOG, POST_ID)
               or any("post/" + POST_ID in u for u in
                      [str(s.get("url", "")) for s in traj.get("steps") or []
                       if isinstance(s, dict)]),
               f"required: the first trending post {POST_ID}")
    judge.check("visited_likes", navigated_path(traj, "/likes"),
                "required: /likes after liking")

    judge.check("answer_blog_meolog", contains_phrase(answer, FIRST_BLOG),
                "expected the first trending post to be from meolog")
    judge.check("answer_before_3404",
                contains_number(answer, NOTES_BEFORE) or "3.4k" in answer.lower(),
                "expected 3.4K notes before liking")
    judge.check("answer_after_3405", contains_number(answer, NOTES_AFTER),
                "expected 3,405 notes after liking")
    judge.check("answer_likes_top_summary",
                contains_phrase(answer, TOP_SUMMARY),
                "expected the liked 'Rhododendron' post at the top of Likes")

    # ---- DB after-state: exactly one like added for bob on the trending post.
    bob = db_query(initial_db, "SELECT id FROM users WHERE email = ?",
                   (EMAIL,))[0]["id"]
    init = like_pairs(initial_db)
    after = like_pairs(after_db)
    added = set(after) - set(init)
    removed = set(init) - set(after)
    judge.check("one_like_added",
                added == {(bob, POST_ID)} and not removed,
                f"added={sorted(added)!r} removed={sorted(removed)!r}")
    changed = changed_tables(initial_db, after_db)
    judge.check("only_likes_changed", changed in ([], ["likes"]),
                f"unexpected table deltas: {changed!r}")
    # the like must be Bob's newest like so it tops the Likes page
    newest = db_query(after_db, "SELECT post_id FROM likes WHERE user_id = ? "
                      "ORDER BY created_at DESC LIMIT 1", (bob,))
    judge.check("like_is_newest", bool(newest) and newest[0]["post_id"] == POST_ID,
                "the new like must sort first on the Likes page")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
