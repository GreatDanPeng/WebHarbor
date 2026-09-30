#!/usr/bin/env python3
"""Verify Tumblr--10.

Sign in as Alice (alice.j@test.com / TestPass123!). On the Following page,
list every blog you follow in the order shown. Unfollow the cabin blog, then
verify it no longer appears on the page, and report the new follow count.
Follow it again and confirm the page is back to its original state.

State contract: the follow SET is identical to the seed at the end; the only
allowed DB delta is the recreated (alice, cabinporn) follow row whose
created_at moved to the task run.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_number, contains_phrase, db_query,
                        entered_identity, final_answer, follow_pairs,
                        navigated_path, run_verifier)

TASK_ID = "Tumblr--10"

EMAIL = "alice.j@test.com"
CABIN_BLOG = "cabinporn"
FOLLOW_COUNT = 6
AFTER_UNFOLLOW_COUNT = 5
FOLLOWED_BLOGS = ("cabinporn", "writingprompts", "nasa", "meolog",
                  "waneella", "staff")


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_alice_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_following",
                sum(1 for u in [str(s.get("url", ""))
                                for s in traj.get("steps") or [] if isinstance(s, dict)]
                    if u.rstrip("/").endswith("/following")) >= 2,
                "required: /following before and after the unfollow/refollow")
    judge.check("visited_cabin_blog",
                navigated_path(traj, f"/blog/{CABIN_BLOG}"),
                "required: /blog/cabinporn on the refollow path")

    judge.check("answer_follow_count_6", contains_number(answer, FOLLOW_COUNT),
                "expected 6 followed blogs")
    judge.check("answer_after_unfollow_count_5",
                contains_number(answer, AFTER_UNFOLLOW_COUNT),
                "expected 5 blogs after unfollowing the cabin blog")
    judge.check("answer_lists_cabin",
                contains_phrase(answer, "cabinporn")
                or contains_phrase(answer, "cabin porn"),
                "expected the cabin blog (Cabin Porn® / cabinporn) in the list")
    judge.check("answer_confirm_restore",
                contains_phrase(answer, "6")
                and (contains_phrase(answer, "restored")
                     or contains_phrase(answer, "back")
                     or contains_phrase(answer, "original")
                     or contains_phrase(answer, "again")
                     or contains_phrase(answer, "refollow")),
                "expected the confirmation that the page is back to 6 blogs")

    # ---- DB after-state: same follow set, only the cabinporn row re-dated.
    init = follow_pairs(initial_db)
    after = follow_pairs(after_db)
    alice = db_query(initial_db, "SELECT id FROM users WHERE email = ?",
                     (EMAIL,))[0]["id"]
    init_pairs = {k for k in init if k[0] == alice}
    after_pairs = {k for k in after if k[0] == alice}
    judge.check("follow_set_identical", init_pairs == after_pairs,
                f"follow set changed: {init_pairs ^ after_pairs!r}")
    cabin = db_query(initial_db, "SELECT id FROM blogs WHERE name = ?",
                     (CABIN_BLOG,))[0]["id"]
    changed = changed_tables(initial_db, after_db, ("follows",))
    ok_delta = (
        changed == ["follows"]
        and len(init) == len(after)
        and after[(alice, cabin)]["created_at"] != init[(alice, cabin)]["created_at"])
    judge.check("only_cabinporn_follow_redated", ok_delta,
                f"unexpected DB delta: changed tables {changed_tables(initial_db, after_db)!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
