#!/usr/bin/env python3
"""Verify Tumblr--16.

Sign in as Alice (alice.j@test.com / TestPass123!). Note the unread badge
count on Activity, open Activity, and list every notification: for each,
report who acted and what they did, plus how long ago the newest one
happened. Open the newest notification's actor blog and report its title
and post count. Then check your Inbox badge count and report it. Finally
navigate to the home page and confirm the Activity badge has cleared,
reporting the count you see.

NOTE (r2, ab8382a9): the seed now carries one unread inbox message for Alice
(from bob-c), so the Inbox nav badge renders with count 1; the honest answer
reports it. The expected notification age is deterministic against the
frozen mirror date ('2 days ago' on the production seed).

audit rail: the actor-blog component deepens the task above the 15-step
depth bar; anchors frozen from the rendered pages (newest notification actor
bob-c — blog 'bob's sketchbook', 3 posts).

State contract: alice's four notifications flip is_new -> 0; nothing else.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_number, contains_phrase, db_query,
                        entered_identity, final_answer, navigated_path,
                        run_verifier)

TASK_ID = "Tumblr--16"

EMAIL = "alice.j@test.com"
BADGE_BEFORE = 4
NOTIFICATIONS = (
    ("bob-c", "liked", "hello tumblr"),
    ("carol-d", "reblogged", "hello tumblr"),
    ("david-k", "started following", None),
    ("bob-c", "sent you a message", None),
)
NEWEST_WHEN = "2 days ago"
INBOX_BADGE = 1
ACTOR_BLOG = "bob-c"
ACTOR_BLOG_TITLE = "bob's sketchbook"
ACTOR_BLOG_POSTS = 3


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_alice_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_activity", navigated_path(traj, "/activity"),
                "required: /activity")
    judge.check("opened_actor_blog",
                navigated_path(traj, f"/blog/{ACTOR_BLOG}"),
                f"required: /blog/{ACTOR_BLOG} (the newest notification's "
                "actor blog)")
    judge.check("returned_home", navigated_path(traj, "/dashboard")
                or navigated_path(traj, "/"),
                "required: back to the home page afterwards")

    judge.check("answer_badge_4", contains_number(answer, BADGE_BEFORE),
                "expected the Activity badge count 4")
    judge.check("answer_notification_bob_like",
                contains_phrase(answer, "bob-c liked")
                and contains_phrase(answer, "hello tumblr"),
                "expected 'bob-c liked your post \"hello tumblr\"'")
    judge.check("answer_notification_carol_reblog",
                contains_phrase(answer, "carol-d reblogged"),
                "expected 'carol-d reblogged your post'")
    judge.check("answer_notification_david_follow",
                contains_phrase(answer, "david-k")
                and contains_phrase(answer, "following"),
                "expected 'david-k started following your blog'")
    judge.check("answer_notification_bob_message",
                contains_phrase(answer, "bob-c")
                and contains_phrase(answer, "message"),
                "expected 'bob-c sent you a message'")
    judge.check("answer_newest_when",
                contains_phrase(answer, NEWEST_WHEN),
                "expected the newest notification to be '2 days ago'")
    judge.check("answer_inbox_badge_one",
                contains_number(answer, INBOX_BADGE),
                "expected the Inbox badge to read 1 (one unread message)")
    judge.check("answer_actor_blog_title",
                contains_phrase(answer, ACTOR_BLOG_TITLE),
                "expected the actor blog title \"bob's sketchbook\"")
    judge.check("answer_actor_blog_posts",
                contains_number(answer, ACTOR_BLOG_POSTS),
                "expected the actor blog's 3 posts")
    judge.check("answer_activity_cleared",
                contains_phrase(answer, "cleared")
                or contains_phrase(answer, "no badge")
                or contains_phrase(answer, "no longer")
                or contains_phrase(answer, "gone"),
                "expected the Activity badge to have cleared")

    # ---- DB after-state: exactly the is_new flips.
    alice = db_query(initial_db, "SELECT id FROM users WHERE email = ?",
                     (EMAIL,))[0]["id"]
    init_notifs = db_query(initial_db,
                           "SELECT * FROM notifications WHERE user_id = ?",
                           (alice,))
    after_notifs = db_query(after_db,
                             "SELECT * FROM notifications WHERE user_id = ?",
                             (alice,))
    judge.check("all_notifications_marked_read",
                all(n["is_new"] in (0, False) for n in after_notifs),
                f"is_new values={[n['is_new'] for n in after_notifs]!r}")
    same_content = all(
        (ia["type"], ia["actor_blog"], ia["post_id"], ia["created_at"])
        == (ib["type"], ib["actor_blog"], ib["post_id"], ib["created_at"])
        for ia, ib in zip(sorted(init_notifs, key=lambda r: r["id"]),
                          sorted(after_notifs, key=lambda r: r["id"])))
    judge.check("notification_content_unchanged", same_content,
                "notification rows must not change beyond is_new")
    changed = changed_tables(initial_db, after_db)
    judge.check("only_notifications_changed", changed == ["notifications"],
                f"unexpected deltas: {changed!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
