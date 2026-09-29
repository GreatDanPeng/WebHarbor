#!/usr/bin/env python3
"""Verify Tumblr--5.

Find the answered ask where someone tells the Paokai blog their art is
gorgeous (search for the blog name plus 'gorgeous'). Open it and report the
asker's username, the question, the first line of the answer, the post's note
count, and its tags. Then open the posting blog and report its title, its post
count, the newest month shown in its archive, and how many posts that month
has.
"""
from verify_lib import (Judge, check_read_only, check_trajectory_identity,
                        contains_all, contains_number, contains_phrase,
                        final_answer, navigated_path, navigated_search,
                        run_verifier, visited_permalink)

TASK_ID = "Tumblr--5"

POST_ID = "750605550915567616"
BLOG = "paokai"
ASKER = "obi-bae-kenobi"
QUESTION_SNIPPET = "your art is gorgeous"
ANSWER_FIRST_LINE = "hello! thank you"
NOTES = 206
TAGS = ("#refs", "#birds", "#wings")
BLOG_TITLE = "Paokai"
BLOG_POSTS = 148
ARCHIVE_NEWEST_MONTH = "September 2026"
ARCHIVE_NEWEST_COUNT = 4


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("searched_paokai_gorgeous",
                any("/search/" in u and "gorgeous" in u.lower()
                    for u in [str(s.get("url", "")) for s in traj.get("steps") or []
                              if isinstance(s, dict)]),
                "required: search combining the blog name and 'gorgeous'")
    judge.check("opened_ask_post", visited_permalink(traj, BLOG, POST_ID),
                f"required: /blog/paokai/{POST_ID}")
    judge.check("visited_paokai_blog", navigated_path(traj, f"/blog/{BLOG}"),
                "required: /blog/paokai")
    judge.check("visited_paokai_archive",
                navigated_path(traj, f"/blog/{BLOG}/archive"),
                "required: /blog/paokai/archive")

    judge.check("answer_asker", contains_phrase(answer, ASKER),
                "expected the asker obi-bae-kenobi")
    judge.check("answer_question", contains_phrase(answer, QUESTION_SNIPPET),
                "expected the question to mention 'your art is gorgeous'")
    judge.check("answer_first_line", contains_phrase(answer, ANSWER_FIRST_LINE),
                "expected the answer's first line 'Hello! Thank you!!'")
    judge.check("answer_notes_206", contains_number(answer, NOTES),
                "expected 206 notes")
    judge.check("answer_tags", contains_all(answer, TAGS),
                "expected the tags #refs #birds #wings")
    judge.check("answer_blog_title", contains_phrase(answer, BLOG_TITLE),
                "expected the blog title Paokai")
    judge.check("answer_blog_posts_148", contains_number(answer, BLOG_POSTS),
                "expected 148 posts on the Paokai blog")
    judge.check("answer_archive_newest_month",
                contains_phrase(answer, ARCHIVE_NEWEST_MONTH),
                "expected September 2026 as the newest archive month")
    judge.check("answer_archive_newest_count",
                contains_number(answer, ARCHIVE_NEWEST_COUNT),
                "expected 4 posts in September 2026")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
