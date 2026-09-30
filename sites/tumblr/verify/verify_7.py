#!/usr/bin/env python3
"""Verify Tumblr--7.

Search for 'operating CCTV cameras' and open the top result, the post about
somebody's first time operating CCTV cameras. Report the full chain of blog
usernames in its reblog trail in order, the post's summary text, its total
note count, like count, and reblog count, its tags, and the opening words of
the original post in the trail. Then open the original blog in the trail and
report its title, total post count, and when it was last updated.

r2 (ab8382a9): both r1 gaps are closed — the re-anchored query 'operating
CCTV cameras' ranks the target post FIRST on the mirror, and the original
trail blog (teaboot) is now in the mirror DB (frozen from the live per-blog
API: 'I Like Yellow Now', 42,149 posts, updated 14 hours ago at snapshot
freeze).
"""
from verify_lib import (Judge, check_read_only, check_trajectory_identity,
                        contains_all, contains_number, contains_phrase,
                        final_answer, navigated_path, navigated_search,
                        run_verifier, visited_permalink)

TASK_ID = "Tumblr--7"

POST_ID = "828957539611869184"
BLOG = "nullenvk"
TRAIL_CHAIN = ("teaboot", "teaboot", "teaboot")
SUMMARY_SNIPPET = "extra sensory input"
OPENING = "my first time operating cctv cameras"
NOTES = 76622
LIKES = 44121
REBLOGS = 32259
TAGS = ("#what", "#just cyborg things", "#cyberpunk")
ORIGINAL_BLOG = "teaboot"
ORIGINAL_TITLE = "i like yellow now"
ORIGINAL_POSTS = 42149
ORIGINAL_UPDATED = "14 hours ago"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("searched_cctv",
                navigated_search(traj, "operating CCTV cameras")
                or any("/search/" in u and "cctv" in u.lower()
                       for u in [str(s.get("url", "")) for s in traj.get("steps") or []
                                 if isinstance(s, dict)]),
                "required: search for the CCTV post")
    judge.check("opened_cctv_post", visited_permalink(traj, BLOG, POST_ID),
                f"required: /blog/nullenvk/{POST_ID} (the 76,622-note post)")
    judge.check("visited_original_blog",
                navigated_path(traj, f"/blog/{ORIGINAL_BLOG}"),
                "required: /blog/teaboot (the original blog in the trail)")

    judge.check("answer_trail_chain",
                contains_phrase(answer, TRAIL_CHAIN[0])
                and answer.count("teaboot") >= 2,
                "expected the reblog trail chain teaboot → teaboot → teaboot")
    judge.check("answer_summary", contains_phrase(answer, SUMMARY_SNIPPET),
                "expected the summary 'Maybe I should write that post about how I "
                "got an extra sensory input…'")
    judge.check("answer_notes_76622", contains_number(answer, NOTES),
                "expected 76,622 notes")
    judge.check("answer_likes_44121", contains_number(answer, LIKES),
                "expected 44,121 likes")
    judge.check("answer_reblogs_32259", contains_number(answer, REBLOGS),
                "expected 32,259 reblogs")
    judge.check("answer_tags", contains_all(answer, TAGS),
                "expected at least the tags #what #just cyborg things #cyberpunk")
    judge.check("answer_opening_words", contains_phrase(answer, OPENING),
                "expected the trail opening 'My first time operating CCTV cameras…'")
    judge.check("answer_original_blog_title",
                contains_phrase(answer, ORIGINAL_TITLE),
                "expected the original blog's title 'I Like Yellow Now'")
    judge.check("answer_original_blog_posts",
                contains_number(answer, ORIGINAL_POSTS),
                "expected 42,149 posts on the teaboot blog")
    judge.check("answer_original_blog_updated",
                contains_phrase(answer, ORIGINAL_UPDATED),
                "expected 'Updated 14 hours ago' on the teaboot blog")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
