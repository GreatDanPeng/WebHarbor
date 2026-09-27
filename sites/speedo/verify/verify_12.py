#!/usr/bin/env python3
"""Verify Speedo--12.

I want my kit to last. Find the Speedo blog article about caring for swimming
goggles and report its key rules, then check the Help Centre FAQ about caring
for a swimsuit and report the rinse advice. Finally open a contact case
(category Product Enquiry, sub-category Goggles) asking which goggles suit a
chlorinated pool, and report the case reference.
"""
from verify_lib import (Judge, check_answer_phrase,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier,
                        table_diff)

TASK_ID = "Speedo--12"

CASE = "CAS100001"
BLOG_SLUG = "4-easy-ways-to-care-for-your-swimming-goggles"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    check_visited_path(judge, traj, "visited_blog_index", r"/blogs/news/?")
    check_visited_path(judge, traj, "visited_goggle_care_article",
                       rf"/blogs/news/{BLOG_SLUG}")
    check_visited_path(judge, traj, "visited_faqs", r"/pages/faqs")
    check_visited_path(judge, traj, "visited_contact", r"/pages/contact")
    check_answer_phrase(judge, answer, "mentions_rinse", "rinse")
    check_answer_phrase(judge, answer, "mentions_case", CASE)

    check_only_tables_changed(judge, initial_db, after_db,
                              allowed={"contact_messages"})
    added, removed, _ = table_diff(initial_db, after_db, "contact_messages")
    judge.check("one_case_added", len(added) == 1 and len(removed) == 0,
                f"added={list(added.values())!r}")
    if added:
        row = list(added.values())[0]
        judge.check("case_ref", row["case_ref"] == CASE, f"case_ref={row['case_ref']!r}")
        judge.check("case_category", row["category"] == "Product Enquiry",
                    f"category={row['category']!r}")
        judge.check("case_subcategory", row["subcategory"] == "Goggles",
                    f"subcategory={row['subcategory']!r}")


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
