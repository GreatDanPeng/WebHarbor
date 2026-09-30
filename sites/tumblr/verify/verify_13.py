#!/usr/bin/env python3
"""Verify Tumblr--13.

Sign in as David (david.k@test.com / TestPass123!). Search for 'cyberpunk'
and open the last blog suggested in the sidebar. Report its title and
description. Follow it, then confirm it appears on your Following page and
that its posts show up on your dashboard, and report the summary of its
newest post on the dashboard.

r2 (ab8382a9): the task is re-anchored on the LAST suggested blog (scipunk),
which carries a real description on the mirror and upstream ('Cyberpunk
Aesthetic' — 'Neon Lights - Movies - Games - Sci-fi - Computers - Megacities
- Rain - Glitch Art - Music - scipunk.bsky.social'); the first suggestion
(cyberpunk / 'Synaptic Seepage') has none on either.

State contract: exactly one follow row (david, scipunk blog) added.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_phrase, db_query, entered_identity,
                        final_answer, follow_pairs, navigated_path,
                        navigated_search, run_verifier)

TASK_ID = "Tumblr--13"

EMAIL = "david.k@test.com"
QUERY = "cyberpunk"
BLOG_NAME = "scipunk"
BLOG_TITLE = "Cyberpunk Aesthetic"
BLOG_DESC_SNIPPET = ("neon lights - movies - games - sci-fi - computers - "
                    "megacities - rain - glitch art - music - "
                    "scipunk.bsky.social")
DASH_NEWEST_SUMMARY = "alien (1979)"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_david_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("searched_cyberpunk", navigated_search(traj, QUERY),
                "required: /search/cyberpunk")
    judge.check("opened_last_suggested_blog",
                navigated_path(traj, f"/blog/{BLOG_NAME}"),
                "required: /blog/scipunk (last suggested blog)")
    judge.check("visited_dashboard", navigated_path(traj, "/dashboard"),
                "required: /dashboard after following")
    judge.check("visited_following", navigated_path(traj, "/following"),
                "required: /following to confirm the follow")

    judge.check("answer_title", contains_phrase(answer, BLOG_TITLE),
                "expected the blog title Cyberpunk Aesthetic")
    judge.check("answer_description",
                contains_phrase(answer, BLOG_DESC_SNIPPET),
                "expected the scipunk blog description (Neon Lights - Movies - "
                "Games - Sci-fi - Computers - Megacities - Rain - Glitch Art - "
                "Music - scipunk.bsky.social)")
    judge.check("answer_dashboard_newest",
                contains_phrase(answer, DASH_NEWEST_SUMMARY),
                "expected the newest dashboard post 'Alien (1979)'")

    # ---- DB after-state: exactly one follow row added.
    david = db_query(initial_db, "SELECT id FROM users WHERE email = ?",
                     (EMAIL,))[0]["id"]
    blog_id = db_query(initial_db, "SELECT id FROM blogs WHERE name = ?",
                       (BLOG_NAME,))[0]["id"]
    init = follow_pairs(initial_db)
    after = follow_pairs(after_db)
    added = set(after) - set(init)
    removed = set(init) - set(after)
    judge.check("one_follow_added",
                added == {(david, blog_id)} and not removed,
                f"added={sorted(added)!r} removed={sorted(removed)!r}")
    changed = changed_tables(initial_db, after_db)
    judge.check("only_follows_changed", changed == ["follows"],
                f"unexpected deltas: {changed!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
