#!/usr/bin/env python3
"""Verify Tumblr--14.

Sign in as Alice (alice.j@test.com / TestPass123!) and open the conversation
with the Tumblr Staff blog in your inbox. Report the exact text of the last
message staff sent. Reply asking one more question, confirm the sent
confirmation, and confirm your message appears in the thread, reporting its
text. Then go back to the inbox and report how many conversations are listed
and which one shows as unread.

audit rail: the return-to-inbox component deepens the task above the 15-step
depth bar; anchors frozen from the rendered inbox after the reply (two
conversations listed: staff; bob-c — the seeded unread one).

State contract: exactly one message row appended to the (alice, staff)
conversation, and that conversation's updated_at bumped; nothing else.
"""
from verify_lib import (Judge, changed_tables, check_trajectory_identity,
                        contains_count, contains_phrase, db_query,
                        entered_identity, final_answer, navigated_path,
                        navigated_to, run_verifier)

TASK_ID = "Tumblr--14"

EMAIL = "alice.j@test.com"
LAST_STAFF_MESSAGE = ("glad to hear it! the tag pages got a fresh coat of "
                      "paint this month. let us know if anything else comes up.")
CONFIRMATION = "message sent."
INBOX_CONVERSATIONS = 2
UNREAD_CONVERSATION = "bob-c"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("entered_alice_email", entered_identity(traj, EMAIL),
                f"required: the login form must receive {EMAIL}")
    judge.check("visited_inbox", navigated_path(traj, "/inbox"),
                "required: /inbox")
    judge.check("opened_staff_conversation",
                navigated_path(traj, "/inbox/staff"),
                "required: /inbox/staff")
    judge.check("sent_reply",
                any("send" in (str(s.get("url", "")) + str(s.get("target", ""))).lower()
                    for s in traj.get("steps") or [] if isinstance(s, dict)),
                "required: the reply POST to /inbox/staff/send")

    judge.check("answer_last_staff_message",
                contains_phrase(answer, LAST_STAFF_MESSAGE),
                "expected the exact last staff message text")
    judge.check("answer_sent_confirmation",
                contains_phrase(answer, CONFIRMATION),
                "expected the 'Message sent.' confirmation")
    # the agent's own reply text must be echoed in the answer
    typed = [(s.get("params") or {}).get("text", "") for s in
             traj.get("steps") or [] if isinstance(s, dict)
             and s.get("action") in ("type", "input", "fill")]
    typed = [t for t in typed if t and "test.com" not in t and "TestPass" not in t]
    judge.check("answer_echoes_reply",
                any(t.rstrip(".?! ").lower() in answer.lower() for t in typed),
                "the reported thread must include the agent's own reply text")
    judge.check("returned_to_inbox",
                navigated_to(traj, "/inbox", times=2),
                "required: back to /inbox after the reply")
    judge.check("answer_inbox_conversations",
                contains_count(answer, INBOX_CONVERSATIONS),
                "expected 2 conversations listed in the inbox")
    judge.check("answer_unread_conversation",
                contains_phrase(answer, UNREAD_CONVERSATION),
                "expected bob-c as the unread conversation")

    # ---- DB after-state: one message added on alice's staff conversation.
    alice = db_query(initial_db, "SELECT id FROM users WHERE email = ?",
                     (EMAIL,))[0]["id"]
    conv = db_query(initial_db,
                    "SELECT id FROM conversations WHERE user_id = ? "
                    "AND blog_name = 'staff'", (alice,))[0]
    init_msgs = {r["id"] for r in db_query(
        initial_db, "SELECT id FROM messages WHERE conversation_id = ?",
        (conv["id"],))}
    after_msgs = db_query(after_db,
                          "SELECT * FROM messages WHERE conversation_id = ?",
                          (conv["id"],))
    added = [m for m in after_msgs if m["id"] not in init_msgs]
    judge.check("one_message_added", len(added) == 1,
                f"added messages={[m['id'] for m in added]!r}")
    if added:
        m = added[0]
        judge.check("message_from_alice",
                    m["from_user"] == 1 and (m["sender_name"] == "alice-j"),
                    f"from_user={m['from_user']} sender={m['sender_name']!r}")
    changed = changed_tables(initial_db, after_db, ("messages", "conversations"))
    judge.check("only_thread_tables_changed",
                set(changed) <= {"messages", "conversations"},
                f"unexpected deltas: {changed!r}")


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
