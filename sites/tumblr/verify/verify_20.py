#!/usr/bin/env python3
"""Verify Tumblr--20.

Register a new Tumblr account with your own email, the username
harbor-tester, and a password of at least 8 characters. Confirm you land on
an empty dashboard and report the message shown. Then follow NASA's blog
from Explore and report the first post that appears on your dashboard,
including its summary and note count.

State contract: one users row (username harbor-tester), one blogs row
(harbor-tester), one follows row (new user -> nasa); nothing else. The
registration email is agent-chosen; the username is pinned by the task.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_number, contains_phrase, db_query,
                        final_answer, navigated_path, run_verifier)

TASK_ID = "Tumblr--20"

USERNAME = "harbor-tester"
EMPTY_DASH_MESSAGES = ("follow some blogs from explore to fill your dashboard",
                       "posts from the 0 blogs you follow")
NASA_POST_ID = "828471464226406400"
NASA_SUMMARY = "autumn is a second spring"
NASA_NOTES = 5592


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("visited_register", navigated_path(traj, "/register"),
                "required: /register")
    judge.check("typed_username",
                any(USERNAME in t.lower() for t in
                    [(s.get("params") or {}).get("text", "") for s in
                     traj.get("steps") or [] if isinstance(s, dict)]),
                f"required: the username '{USERNAME}' typed into the form")
    judge.check("typed_password",
                any(len(t) >= 8 for t in
                    [(s.get("params") or {}).get("text", "") for s in
                     traj.get("steps") or [] if isinstance(s, dict)]),
                "required: a password of at least 8 characters")
    judge.check("visited_dashboard", navigated_path(traj, "/dashboard"),
                "required: /dashboard (the empty dashboard after registering)")
    judge.check("visited_explore", navigated_path(traj, "/explore"),
                "required: /explore on the way to follow NASA")
    judge.check("followed_nasa",
                any("/blog/nasa/follow" in str(s.get("url", ""))
                    or ("follow" in str(s.get("target", "")).lower()
                        and "nasa" in (str(s.get("target", "")) + str(s.get("detail", ""))).lower())
                    for s in traj.get("steps") or [] if isinstance(s, dict)),
                "required: the follow action on NASA's blog")

    judge.check("answer_empty_dashboard",
                any(contains_phrase(answer, m) for m in EMPTY_DASH_MESSAGES),
                "expected the empty-dashboard message")
    judge.check("answer_first_post_summary",
                contains_phrase(answer, NASA_SUMMARY),
                "expected the first dashboard post 'Autumn is a second spring…'")
    judge.check("answer_first_post_notes",
                contains_number(answer, NASA_NOTES) or "5.6k" in answer.lower(),
                "expected 5,592 notes (5.6K) on the first dashboard post")

    # ---- DB after-state: registration + follow.
    init_users = {r["id"] for r in db_query(initial_db, "SELECT id FROM users")}
    after_users = db_query(after_db, "SELECT * FROM users")
    new_users = [u for u in after_users if u["id"] not in init_users]
    judge.check("one_user_added",
                len(new_users) == 1 and new_users[0]["username"] == USERNAME,
                f"new users={[(u['username'], u['email']) for u in new_users]!r}")
    init_blogs = {r["id"] for r in db_query(initial_db, "SELECT id FROM blogs")}
    after_blogs = db_query(after_db, "SELECT * FROM blogs")
    new_blogs = [b for b in after_blogs if b["id"] not in init_blogs]
    judge.check("one_blog_added",
                len(new_blogs) == 1 and new_blogs[0]["name"] == USERNAME,
                f"new blogs={[b['name'] for b in new_blogs]!r}")
    if new_users:
        uid = new_users[0]["id"]
        nasa = db_query(initial_db, "SELECT id FROM blogs WHERE name = 'nasa'")[0]["id"]
        init_follows = {r["user_id"] for r in
                       db_query(initial_db, "SELECT user_id FROM follows")}
        new_follows = [f for f in db_query(after_db, "SELECT * FROM follows")
                       if f["user_id"] not in init_follows]
        judge.check("one_follow_added",
                    len(new_follows) == 1
                    and new_follows[0]["user_id"] == uid
                    and new_follows[0]["blog_id"] == nasa,
                    f"new follows={new_follows!r}")
    changed = changed_tables(initial_db, after_db)
    judge.check("only_expected_tables_changed",
                set(changed) <= {"users", "blogs", "follows"},
                f"unexpected deltas: {changed!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
