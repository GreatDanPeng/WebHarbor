#!/usr/bin/env python3
"""Verify Tumblr--3.

Search for 'NASA' and open NASA's own blog from the results. Report its exact
title and total post count, plus when it was last updated. Open its archive
and report which month has the most posts, how many posts that month
contains, and how many posts the newest month contains. Then open any post
from the newest month and report its note count and summary. Come back to
the blog page, open the second post in its feed, and report its note count
and first tag.

audit rail: the newest-month count and the second-feed-post components
deepen the task above the 15-step depth bar; anchors frozen from the
rendered pages (archive 'September 2026 (3)'; second feed post
828110959105245184 shows 1,157 notes on its permalink, first tag #nasa).
"""
from verify_lib import (Judge, check_read_only, check_trajectory_identity,
                        contains_number, contains_phrase, db_query,
                        final_answer, navigated_path, navigated_search,
                        run_verifier)

TASK_ID = "Tumblr--3"

QUERY = "NASA"
BLOG = "nasa"
TITLE = "NASA"
POSTS_COUNT = 1759
UPDATED_LABEL = "5 days ago"
MOST_MONTH = "April 2026"
MOST_MONTH_COUNT = 13
NEWEST_MONTH = "September 2026"
NEWEST_MONTH_COUNT = 3
NEWEST_MONTH_POSTS = ("828471464226406400", "828110959105245184",
                      "827389442508685312")
SECOND_FEED_POST_ID = "828110959105245184"
SECOND_FEED_POST_NOTES = 1157      # live count on the permalink (1,157)
SECOND_FEED_POST_NOTES_CARD = "1.2k"  # compact count on the blog feed card
SECOND_FEED_POST_FIRST_TAG = "#nasa"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    judge.check("searched_nasa", navigated_search(traj, QUERY),
                "required: /search/NASA")
    judge.check("visited_nasa_blog", navigated_path(traj, f"/blog/{BLOG}"),
                "required: /blog/nasa")
    judge.check("visited_nasa_archive", navigated_path(traj, f"/blog/{BLOG}/archive"),
                "required: /blog/nasa/archive")
    visited = {u.split("/")[-1] for u in
               [str(s.get("url", "")) for s in traj.get("steps") or [] if isinstance(s, dict)]
               if f"/blog/{BLOG}/" in u}
    opened_sept = [p for p in NEWEST_MONTH_POSTS if p in visited]
    judge.check("opened_post_from_newest_month", bool(opened_sept),
                f"required: open one of {NEWEST_MONTH_POSTS} (September 2026)")
    urls_in_order = [str(s.get("url", "")) for s in
                     traj.get("steps") or [] if isinstance(s, dict)]
    archive_at = next((i for i, u in enumerate(urls_in_order)
                       if f"/blog/{BLOG}/archive" in u), None)

    def _is_blog_page(u):
        from urllib.parse import urlparse as _up
        p = _up(u)
        return (p.path.rstrip("/") == f"/blog/{BLOG}")

    judge.check("returned_to_nasa_blog",
                archive_at is not None and any(
                    _is_blog_page(u) for u in urls_in_order[archive_at:]),
                "required: come back to the blog page after the archive")
    judge.check("opened_second_feed_post",
                any(f"/blog/{BLOG}/{SECOND_FEED_POST_ID}" in u for u in
                    [str(s.get("url", "")) for s in traj.get("steps") or []
                     if isinstance(s, dict)]),
                f"required: /blog/nasa/{SECOND_FEED_POST_ID} "
                "(the second post in the blog feed)")

    judge.check("answer_title_nasa", contains_phrase(answer, TITLE),
                "expected the blog title NASA")
    judge.check("answer_post_count_1759", contains_number(answer, POSTS_COUNT),
                "expected 1,759 posts")
    judge.check("answer_updated_5_days",
                contains_phrase(answer, UPDATED_LABEL)
                or contains_phrase(answer, "updated 5 days"),
                "expected 'Updated 5 days ago'")
    judge.check("answer_most_month_april",
                contains_phrase(answer, MOST_MONTH),
                "expected April 2026 as the month with the most posts")
    judge.check("answer_most_month_13", contains_number(answer, MOST_MONTH_COUNT),
                "expected 13 posts in April 2026")
    judge.check("answer_newest_month_count",
                contains_phrase(answer, "september 2026 (3)")
                or (contains_phrase(answer, NEWEST_MONTH)
                    and contains_number(answer, NEWEST_MONTH_COUNT)),
                "expected the newest month September 2026 to contain 3 posts")
    if opened_sept:
        post = db_query(initial_db, "SELECT note_count, summary FROM posts "
                        "WHERE id = ? LIMIT 1", (opened_sept[0],))[0]
        # The permalink's notes head shows the LIVE count (frozen note_count
        # plus seeded like/reblog rows for that post); accept either the
        # stored count or the displayed live count — same duality contract
        # as T8/T9.
        live_extra = db_query(
            initial_db,
            "SELECT (SELECT COUNT(*) FROM likes WHERE post_id = ?) + "
            "(SELECT COUNT(*) FROM reblogs WHERE source_post_id = ?) AS n",
            (opened_sept[0], opened_sept[0]))[0]["n"]
        judge.check("answer_opened_notes",
                    contains_number(answer, post["note_count"])
                    or contains_number(answer, post["note_count"] + live_extra),
                    f"expected {post['note_count']:,} notes for the opened post "
                    f"({post['note_count'] + live_extra:,} as displayed live)")
        head = (post["summary"] or "").strip().split("\n")[0][:45]
        judge.check("answer_opened_summary",
                    contains_phrase(answer, head[:32]),
                    f"expected the opened post summary to start {head!r}")
    judge.check("answer_second_post_notes",
                contains_number(answer, SECOND_FEED_POST_NOTES)
                or SECOND_FEED_POST_NOTES_CARD in answer.lower(),
                f"expected {SECOND_FEED_POST_NOTES:,} notes for the second "
                "feed post (1.2K on the card)")
    judge.check("answer_second_post_first_tag",
                contains_phrase(answer, SECOND_FEED_POST_FIRST_TAG),
                "expected the second feed post's first tag #nasa")
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    run_verifier(TASK_ID, run_checks, dict(globals()))
