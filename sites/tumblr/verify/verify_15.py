#!/usr/bin/env python3
"""Verify Tumblr--15.

Sign in as Bob (bob.c@test.com / TestPass123!) and send an ask to Alice's
blog asking which museum she visits most. Confirm the ask was sent. Then log
out, sign in as Alice (alice.j@test.com / TestPass123!), open your inbox, and
report the exact text of the question that arrived.

State contract (r2, corrected against the real app behavior): the ask goes
into Alice's EXISTING (bob-c) conversation (the seed already carries one,
now with a seeded unread message from bob-c). Opening the conversation marks
every incoming message read, so the honest delta is: +1 message (the ask,
from_user=0, sender bob-c, containing the museum question) and the seeded
unread bob-c message flips read 0 -> 1. No conversation rows change.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_phrase, db_query, entered_identity,
                        final_answer, navigated_path, run_verifier)

TASK_ID = "Tumblr--15"

BOB_EMAIL = "bob.c@test.com"
ALICE_EMAIL = "alice.j@test.com"
ASK_CONFIRMATION = "your question has been sent to alice's archive"
QUESTION_SNIPPET = "museum"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_bob_email", entered_identity(traj, BOB_EMAIL),
                f"required: Bob's login form must receive {BOB_EMAIL}")
    judge.check("entered_alice_email", entered_identity(traj, ALICE_EMAIL),
                f"required: Alice's login form must receive {ALICE_EMAIL}")
    judge.check("visited_ask_form",
                any("/ask" in str(s.get("url", "")) for s in
                    traj.get("steps") or [] if isinstance(s, dict)),
                "required: the ask form on Alice's blog")
    judge.check("visited_alice_inbox", navigated_path(traj, "/inbox"),
                "required: Alice's /inbox after re-login")
    judge.check("opened_bob_conversation",
                navigated_path(traj, "/inbox/bob-c"),
                "required: /inbox/bob-c showing the arrived question")

    judge.check("answer_ask_confirmation",
                contains_phrase(answer, ASK_CONFIRMATION),
                "expected the 'Your question has been sent to Alice's Archive.' "
                "confirmation")
    judge.check("answer_question_text",
                contains_phrase(answer, QUESTION_SNIPPET),
                "expected the arrived question mentioning the museum")

    # ---- DB after-state: the ask lands in alice's EXISTING (bob-c)
    # conversation; opening it also flips the seeded unread message.
    alice = db_query(initial_db, "SELECT id FROM users WHERE email = ?",
                     (ALICE_EMAIL,))[0]["id"]
    conv = db_query(initial_db,
                    "SELECT id FROM conversations WHERE user_id = ? "
                    "AND blog_name = 'bob-c'", (alice,))[0]
    init_msgs = {r["id"]: r for r in db_query(
        initial_db, "SELECT * FROM messages WHERE conversation_id = ?",
        (conv["id"],))}
    after_msgs = db_query(after_db,
                          "SELECT * FROM messages WHERE conversation_id = ?",
                          (conv["id"],))
    added = [m for m in after_msgs if m["id"] not in init_msgs]
    judge.check("ask_message_added",
                len(added) == 1 and added[0]["from_user"] == 0
                and added[0]["sender_name"] == "bob-c"
                and QUESTION_SNIPPET in (added[0]["body"] or ""),
                f"added messages={[ (m['sender_name'], (m['body'] or '')[:40]) for m in added]!r}")
    read_flips = [m for m in after_msgs
                  if m["id"] in init_msgs
                  and init_msgs[m["id"]]["read"] in (0, False)
                  and m["read"] in (1, True)]
    seeded_unread = [i for i, m in init_msgs.items()
                     if m["from_user"] == 0 and m["read"] in (0, False)]
    judge.check("seeded_unread_message_marked_read",
                len(read_flips) == len(seeded_unread),
                f"seeded unread={[i for i in seeded_unread]!r} "
                f"flipped={[m['id'] for m in read_flips]!r}")
    changed = changed_tables(initial_db, after_db)
    judge.check("only_messages_changed",
                changed == ["messages"],
                f"unexpected deltas: {changed!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
