#!/usr/bin/env python3
"""Emit verify_0.py .. verify_19.py for the thumbtack review contract.

Ground truths are frozen from the reviewer's independent honest walks
(2026-09-27, review container wh-tt-review @ 127.0.0.1:46100 -> container
port 40099, seed md5 0c1320fd…). Navigation gates mirror the walk URLs; DB
deltas mirror the deterministic application writes (PYTHONHASHSEED=0 seed +
det_hash quotes for project id 6).

Audit-rail re-freeze (2026-09-28, re-sync of re-review observation R1):
tasks 2,3,6,7,8,9,10,11,12,13,14,16,17,18,19 re-frozen from the AUDIT
walks on the audit container wh-tt-audit @ 127.0.0.1:49100 (same
deterministic seed md5 0c1320fd…, per-task reset + fresh context,
visible-element interaction only); tasks 0/1/4/5/15 keep the reviewer's
r2-frozen ground truth (the audit walks pass them unchanged).
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent

HEADER = '''#!/usr/bin/env python3
"""Verify Thumbtack--{n}.

{ques}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (Judge, check_answer_any, check_answer_number,
                        check_answer_phrase, check_input_action,
                        check_new_user, check_only_tables_changed,
                        check_read_only, check_row_updated,
                        check_table_added, check_table_removed,
                        check_trajectory_identity, check_visited_path,
                        final_answer, run_verifier)

TASK_ID = "Thumbtack--{n}"

# frozen ground truth (reviewer honest walk 2026-09-27, seed md5 0c1320fd…)
{constants}


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
{nav}
{ans}
{db}


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
'''

# ---------------------------------------------------------------- per-task specs
def V(n, ques, constants, nav, ans, db):
    return HEADER.format(n=n, ques=ques, constants=constants, nav=nav, ans=ans, db=db)


TASKS = {}

# ---------------------------------------------------------------- task 0
TASKS[0] = V(0,
"""Log in with the demo account (email: alice.j@test.com, password: TestPass123!). I'm choosing between the Seattle wedding photographers Jeshua Frees (Clearline Production) and Tanner Schmidt. Compare how many Thumbtack hires each of them has, save the one with more hires to my saved pros, and tell me how many years that pro has been in business and how many employees they have.""",
"""JESHUA_HIRES = 69
TANNER_HIRES = 30
WINNER = "Jeshua Frees"
WINNER_YEARS = 7
WINNER_EMPLOYEES = 19
WINNER_PRO_ID = 169""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "Jeshua profile",
                       r"/wa/seattle/wedding-photographers/jeshua-frees-clearline-production/service/510542342918987781")
    check_visited_path(judge, traj, "Tanner profile",
                       r"/wa/seattle/wedding-photographers/tanner-schmidt/service/508112018197602315")''',
'''    check_answer_phrase(judge, answer, "winner name", "Jeshua")
    check_answer_number(judge, answer, "winner hires", JESHUA_HIRES, "hire")
    check_answer_number(judge, answer, "years in business", WINNER_YEARS, "year")
    check_answer_number(judge, answer, "employees", WINNER_EMPLOYEES, "employee")
    check_answer_any(judge, answer, "saved confirmation",
                     ["saved", "save"])''',
'''    check_only_tables_changed(judge, initial_db, after_db, {"saved_pros"})
    check_table_added(judge, initial_db, after_db, "saved_pros",
                      [(None, 1, WINNER_PRO_ID, None)])''')

# ---------------------------------------------------------------- task 1
TASKS[1] = V(1,
"""Log in with the demo account (email: bob.c@test.com, password: TestPass123!). My 2-bedroom apartment in zip 98101 needs a deep cleaning before I move out next month. Request house cleaning quotes for a one-time deep clean of 2 bedrooms and 2 bathrooms, hire the cheapest pro who responded, and leave them a 5-star review that mentions "move-out".""",
"""HIRED_PRO = "Ipanema Cleaning Service"
HIRED_PRO_ID = 66
LOWEST_QUOTE = 184
EXPECTED_QUOTES = (191, 184, 244, 245, 227)""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "house cleaning category", r"/k/house-cleaning/near-me")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\\?category=house-cleaning")
    check_visited_path(judge, traj, "project page", r"/projects/6")
    check_visited_path(judge, traj, "review form", r"/projects/6/review")''',
'''    check_answer_phrase(judge, answer, "hired pro name", "Ipanema")
    check_answer_number(judge, answer, "cheapest quote", LOWEST_QUOTE,
                        ["quote", "cheapest", "lowest", "responder", "ipanema"])
    check_answer_any(judge, answer, "5-star review", ["5-star", "five-star", "5 star"])
    check_answer_any(judge, answer, "move-out mention", ["move-out", "move out", "moveout"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"projects", "project_matches", "reviews"})
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 2, 1, "98101", None, None, None, "completed", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 73, 1, 191, None, None, 0),
                       (27, 6, HIRED_PRO_ID, 1, 184, None, None, 1),
                       (28, 6, 76, 1, 244, None, None, 0),
                       (29, 6, 67, 1, 245, None, None, 0),
                       (30, 6, 65, 1, 227, None, None, 0)])
    check_table_added(judge, initial_db, after_db, "reviews",
                      [(857, HIRED_PRO_ID, "Bob Chen", "Sep 26, 2026", 5,
                        None, "project:6", 1, "user")])''')

# ---------------------------------------------------------------- task 2
TASKS[2] = V(2,
"""Log in with the demo account (email: carol.d@test.com, password: TestPass123!). I'm planning a wedding on a tight budget. Using Thumbtack's cost guides, compare the national average cost of hiring a wedding DJ with a wedding photographer's, and tell me which service is more expensive and by roughly how much. Then find the highest-rated DJ based in Everett, message them to confirm they're available for an October wedding date, and request an estimate from them describing your four-hour wedding reception.""",
"""DJ_AVG = 550
PHOTO_AVG = 150
EVERETT_DJ = "Cessionnation"
EVERETT_DJ_PK = 376863969460043777
DJ_REPLY = "love to be part of it"
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "wedding DJ cost guide", r"/p/wedding-djs-cost")
    check_visited_path(judge, traj, "photographer cost guide", r"/p/wedding-photographer-prices")
    check_visited_path(judge, traj, "DJs category sorted", r"/k/djs/near-me\?sort=highest_rated")
    check_visited_path(judge, traj, "Everett DJ profile", r"/wa/everett/djs/cessionnation/service/376863969460043777")
    check_visited_path(judge, traj, "DJ message flow", r"/message/376863969460043777|/account/messages/2")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\?category=djs")
    check_visited_path(judge, traj, "project page", r"/projects/6")''',
'''    check_answer_number(judge, answer, "DJ national average", DJ_AVG, "dj")
    check_answer_number(judge, answer, "photographer national average", PHOTO_AVG,
                        "photographer")
    check_answer_phrase(judge, answer, "DJ more expensive", "dj")
    check_answer_phrase(judge, answer, "Everett DJ", EVERETT_DJ)
    check_answer_phrase(judge, answer, "DJ reply", DJ_REPLY)
    check_answer_phrase(judge, answer, "four-hour reception", "four-hour")
    check_answer_any(judge, answer, "estimate requested",
                     ["estimate", "quote", "request"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"threads", "messages", "projects", "project_matches"})
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 3, 19, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None)])
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 3, 16, "98004", None, None, None, "matched", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 23, 1, 527, None, None, 0),
                       (27, 6, 19, 1, 567, None, None, 0),
                       (28, 6, 20, 0, None, None, None, 0),
                       (29, 6, 26, 1, 586, None, None, 0),
                       (30, 6, 22, 1, 520, None, None, 0)])''')

# ---------------------------------------------------------------- task 3
TASKS[3] = V(3,
"""Log in with the demo account (email: alice.j@test.com, password: TestPass123!). On Paty House Cleaning's profile, find the word customers mention most often in their reviews and check whether that theme also appears in the newest review. Message Paty asking whether they bring their own cleaning supplies. Then ask a second house cleaner the same question, and follow up with Paty asking whether they could come on a Sunday. Report all three replies.""",
"""MOST_MENTIONED = "clean"
PATY_PRO_ID = 71
SECOND_CLEANER = "Empire Cleaning Services"
SECOND_PRO_ID = 65
SUPPLIES_REPLY = "we bring all of our own supplies and equipment"
SUNDAY_REPLY = "happy to work around your schedule"
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "Paty profile", r"/wa/lynnwood/house-cleaning/paty-house-cleaning/service/491085485275881476")
    check_visited_path(judge, traj, "Paty message flow", r"/message/491085485275881476|/account/messages/2")
    check_visited_path(judge, traj, "house cleaning category sorted", r"/k/house-cleaning/near-me\?sort=highest_rated")
    check_visited_path(judge, traj, "second cleaner profile", r"/wa/kirkland/house-cleaning/empire-cleaning-services/service/476683242989297681")
    check_visited_path(judge, traj, "second cleaner thread", r"/account/messages/3")
    check_visited_path(judge, traj, "Paty Sunday follow-up", r"/account/messages/2")''',
'''    check_answer_phrase(judge, answer, "most-mentioned word", MOST_MENTIONED)
    check_answer_phrase(judge, answer, "second cleaner", SECOND_CLEANER)
    check_answer_phrase(judge, answer, "supplies reply", SUPPLIES_REPLY)
    check_answer_phrase(judge, answer, "Sunday reply", SUNDAY_REPLY)''',
'''    check_only_tables_changed(judge, initial_db, after_db, {"threads", "messages"})
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 1, PATY_PRO_ID, None, None),
                       (3, 1, SECOND_PRO_ID, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None),
                       (5, 3, "user", None, None),
                       (6, 3, "pro", None, None),
                       (7, 2, "user", None, None),
                       (8, 2, "pro", None, None)])''')

# ---------------------------------------------------------------- task 4
TASKS[4] = V(4,
"""Log in with the demo account (email: alice.j@test.com, password: TestPass123!). My TV mounting project is on hold — cancel it, but first tell me which pro had quoted the lowest price and how many quotes the project had received in total. Then start a replacement request in zip 98033 to hire a handyman for hanging a heavy mirror instead.""",
"""LOWEST_PRO = "Wa Pro Builders"
LOWEST_QUOTE = 121
TOTAL_QUOTES = 5
REPLACEMENT_CAT = 4  # handyman""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "TV mounting project page", r"/projects/2")
    check_visited_path(judge, traj, "handyman category", r"/k/handyman/near-me")
    check_visited_path(judge, traj, "replacement wizard", r"/projects/new\\?category=handyman")
    check_visited_path(judge, traj, "replacement project page", r"/projects/6")''',
'''    check_answer_number(judge, answer, "lowest quote", LOWEST_QUOTE,
                        ["lowest", "quote", "wa pro", "cheapest"])
    check_answer_phrase(judge, answer, "lowest pro name", "Wa Pro Builders")
    check_answer_number(judge, answer, "total quotes", TOTAL_QUOTES, "quote")
    check_answer_any(judge, answer, "cancelled", ["cancel"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"projects", "project_matches"})
    check_row_updated(judge, initial_db, after_db, "projects", "id = 2",
                      "status", "cancelled")
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 1, REPLACEMENT_CAT, "98033", None, None, None,
                        "matched", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 61, 1, 80, None, None, 0),
                       (27, 6, 55, 1, 68, None, None, 0),
                       (28, 6, 63, 1, 77, None, None, 0),
                       (29, 6, 54, 1, 75, None, None, 0),
                       (30, 6, 59, 1, 62, None, None, 0)])''')

# ---------------------------------------------------------------- task 5
TASKS[5] = V(5,
"""Log in with the demo account (email: carol.d@test.com, password: TestPass123!). I've just moved to Kirkland (zip 98033). Update my profile's zip code and address, then find the highest-rated lawn care professional who serves that area and request a quote for a weekly mowing service.""",
"""NEW_ZIP = "98033"
TARGET_PRO = "Slc - Simple Lawn Care"
LAWN_CAT = 5""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "profile edit", r"/account/profile")
    check_visited_path(judge, traj, "lawn care category sorted",
                       r"/k/lawn-care/near-me\\?sort=highest_rated")
    check_visited_path(judge, traj, "target pro profile",
                       r"/wa/kirkland/lawn-care/slc-simple-lawn-care/service/230942537935791237")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\\?category=lawn-care")
    check_visited_path(judge, traj, "project page", r"/projects/6")''',
'''    check_answer_number(judge, answer, "new zip", "98033", "zip")
    check_answer_phrase(judge, answer, "target pro name", "Simple Lawn Care")
    check_answer_any(judge, answer, "quote requested",
                     ["quote", "estimate", "request"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"users", "projects", "project_matches"})
    check_row_updated(judge, initial_db, after_db, "users", "id = 3",
                      "zip", NEW_ZIP)
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 3, LAWN_CAT, NEW_ZIP, None, None, None,
                        "matched", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 105, 1, 255, None, None, 0),
                       (27, 6, 113, 0, None, None, None, 0),
                       (28, 6, 112, 1, 407, None, None, 0),
                       (29, 6, 107, 1, 194, None, None, 0),
                       (30, 6, 110, 1, 378, None, None, 0)])''')

# ---------------------------------------------------------------- task 6
TASKS[6] = V(6,
"""Log in with the demo account (email: david.k@test.com, password: TestPass123!). My kitchen faucet has been dripping for a week. Find a plumber who is background checked and accepts Venmo, save them to my saved pros, and message them to confirm they can handle the leak urgently. Then request a pipe-repair quote within a week describing the leaky faucet, and tell me the lowest quote and how it compares to the cost guide's typical range for plumbers.""",
"""PLUMBER = "Velichkoremodels"
PLUMBER_PRO_ID = 6
URGENT_REPLY = "same-day or next-day"
LOWEST_QUOTE = 51
GUIDE_RANGE = "$50 - $200"
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "plumbers category sorted", r"/k/affordable-plumbing-services/near-me\?sort=highest_rated")
    check_visited_path(judge, traj, "plumber profile", r"/wa/everett/affordable-plumbing-services/velichkoremodels-llc-emergency-restoration-247/service/550902459815264257")
    check_visited_path(judge, traj, "urgent message flow", r"/message/550902459815264257|/account/messages/2")
    check_visited_path(judge, traj, "pipe-repair wizard", r"/projects/new\?category=affordable-plumbing-services")
    check_visited_path(judge, traj, "project page", r"/projects/6")
    check_visited_path(judge, traj, "plumbers cost guide", r"/p/plumbers-cost")''',
'''    check_answer_phrase(judge, answer, "plumber name", PLUMBER)
    check_answer_any(judge, answer, "background checked", ["background checked"])
    check_answer_any(judge, answer, "venmo", ["venmo"])
    check_answer_phrase(judge, answer, "urgent reply", URGENT_REPLY)
    check_answer_number(judge, answer, "lowest quote", LOWEST_QUOTE,
                        ["quote", "lowest", "cheapest"])
    check_answer_phrase(judge, answer, "guide range", GUIDE_RANGE)''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"saved_pros", "threads", "messages",
                               "projects", "project_matches"})
    check_table_added(judge, initial_db, after_db, "saved_pros",
                      [(14, 4, PLUMBER_PRO_ID, None)])
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 4, PLUMBER_PRO_ID, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None)])
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 4, 2, "98033", None, "Within a week", None, "matched", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 6, 1, 189, None, None, 0),
                       (27, 6, 3, 1, 135, None, None, 0),
                       (28, 6, 1, 1, 51, None, None, 0),
                       (29, 6, 5, 1, 184, None, None, 0),
                       (30, 6, 2, 1, 169, None, None, 0)])''')

# ---------------------------------------------------------------- task 7
TASKS[7] = V(7,
"""Create a new Thumbtack account (name: Nina Patel, email: nina.p@test.com, password: NewHome2026!), then request quotes for assembling a large wardrobe and two bookcases in zip 98101, answering the questionnaire about the three items and the instructions you have and describing the job. Hire the cheapest pro who responded, mark the project complete, and leave them a 5-star review mentioning the smooth assembly. Tell me how many pros responded and what the cheapest quote was.""",
"""NEW_USER = "Nina Patel"
NEW_EMAIL = "nina.p@test.com"
NEW_USERNAME = "nina.p"
N_RESPONDERS = 4
CHEAPEST_QUOTE = 107
HIRED_PRO_ID = 52
WIZARD_ANSWERS = ('[["Number of items", "3 items"], '
                  '["Instructions or make/model provided by client?", '
                  '"Yes, I have assembly instructions or make and model information"]]')
""",
'''    check_visited_path(judge, traj, "registration page", r"/register")
    check_visited_path(judge, traj, "furniture assembly category", r"/k/furniture-assembly/near-me")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\?category=furniture-assembly")
    check_visited_path(judge, traj, "project page", r"/projects/6")
    check_visited_path(judge, traj, "review form", r"/projects/6/review")''',
'''    check_answer_number(judge, answer, "responders", N_RESPONDERS,
                        ["respond", "pros"])
    check_answer_number(judge, answer, "cheapest quote", CHEAPEST_QUOTE,
                        ["quote", "cheapest"])
    check_answer_any(judge, answer, "smooth assembly review",
                     ["smooth assembly", "smooth"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"users", "projects", "project_matches", "reviews"})
    check_new_user(judge, initial_db, after_db, NEW_EMAIL,
                    "nina.p", NEW_USER)
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 5, 9, "98101", None, None, WIZARD_ANSWERS,
                        "completed", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 49, 1, 180, None, None, 0),
                       (27, 6, 44, 0, None, None, None, 0),
                       (28, 6, 46, 1, 131, None, None, 0),
                       (29, 6, HIRED_PRO_ID, 1, 107, None, None, 1),
                       (30, 6, 50, 1, 144, None, None, 0)])
    check_table_added(judge, initial_db, after_db, "reviews",
                      [(857, HIRED_PRO_ID, NEW_USER, "Sep 26, 2026", 5,
                        None, "project:6", 1, "user")])''')

# ---------------------------------------------------------------- task 8
TASKS[8] = V(8,
"""Log in with the demo account (email: alice.j@test.com, password: TestPass123!). I can only be home on Sundays. Find two handymen whose business hours include Sunday, save both to my saved pros, and message the one with more reviews to confirm they can do a Sunday visit. Follow up in the same thread asking which Sunday time slots they have open, then open my saved list and remove the other handyman. Report both replies.""",
"""SUNDAY_ONE = "Evergreen Home Assist"
SUNDAY_ONE_ID = 54
SUNDAY_TWO = "I.d. Handyman"
SUNDAY_TWO_ID = 55
SUNDAY_TWO_REVIEWS = 56
SLOTS_REPLY = "We do have openings"
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "handyman category", r"/k/handyman/near-me")
    check_visited_path(judge, traj, "first Sunday handyman profile", r"/wa/mountlake-terrace/handyman/evergreen-home-assist-llc/service/559530045965762575")
    check_visited_path(judge, traj, "second Sunday handyman profile", r"/wa/lynnwood/handyman/id-handyman/service/557383931483373571")
    check_visited_path(judge, traj, "Sunday message flow", r"/message/557383931483373571|/account/messages/2")
    check_visited_path(judge, traj, "saved list", r"/account/saved")''',
'''    check_answer_phrase(judge, answer, "Sunday handyman one", SUNDAY_ONE)
    check_answer_phrase(judge, answer, "Sunday handyman two", SUNDAY_TWO)
    check_answer_number(judge, answer, "more-reviewed handyman reviews",
                        SUNDAY_TWO_REVIEWS, "review")
    check_answer_phrase(judge, answer, "Sunday slots replies", SLOTS_REPLY)
    check_answer_any(judge, answer, "removal from saved",
                     ["removed", "remove"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"saved_pros", "threads", "messages"})
    check_table_added(judge, initial_db, after_db, "saved_pros",
                      [(15, 1, SUNDAY_TWO_ID, None)])
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 1, SUNDAY_TWO_ID, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None),
                       (5, 2, "user", None, None),
                       (6, 2, "pro", None, None)])''')

# ---------------------------------------------------------------- task 9
TASKS[9] = V(9,
"""Log in with the demo account (email: bob.c@test.com, password: TestPass123!). According to Thumbtack's cost guide, what do most people pay for a one-time house cleaning visit? Then request a one-time deep-cleaning quote for my 3-bedroom, 2-bathroom home in zip 98101, describing the job. Hire the pro with the cheapest quote, mark the project complete, and leave them a 5-star review. Tell me their name and whether their price falls inside the guide's typical range.""",
"""GUIDE_RANGE = "$174 - $256"
HIRED_PRO = "Ipanema Cleaning Service"
HIRED_PRO_ID = 66
CHEAPEST_QUOTE = 184
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "house cleaning cost guide", r"/p/house-cleaning-prices")
    check_visited_path(judge, traj, "house cleaning category", r"/k/house-cleaning/near-me")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\?category=house-cleaning")
    check_visited_path(judge, traj, "project page", r"/projects/6")
    check_visited_path(judge, traj, "review form", r"/projects/6/review")''',
'''    check_answer_phrase(judge, answer, "guide typical range", GUIDE_RANGE)
    check_answer_phrase(judge, answer, "hired pro name", HIRED_PRO)
    check_answer_number(judge, answer, "cheapest quote", CHEAPEST_QUOTE,
                        ["quote", "cheapest", "lowest"])
    check_answer_any(judge, answer, "inside/outside verdict",
                     ["inside", "outside"])
    check_answer_any(judge, answer, "5-star review",
                     ["5-star", "five-star", "5 star"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"projects", "project_matches", "reviews"})
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 2, 1, "98101", None, None, None, "completed", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 73, 1, 191, None, None, 0),
                       (27, 6, HIRED_PRO_ID, 1, 184, None, None, 1),
                       (28, 6, 76, 1, 244, None, None, 0),
                       (29, 6, 67, 1, 245, None, None, 0),
                       (30, 6, 65, 1, 227, None, None, 0)])
    check_table_added(judge, initial_db, after_db, "reviews",
                      [(857, HIRED_PRO_ID, "Bob Chen", "Sep 26, 2026", 5,
                        None, "project:6", 1, "user")])''')

# ---------------------------------------------------------------- task 10
TASKS[10] = V(10,
"""Log in with the demo account (email: bob.c@test.com, password: TestPass123!). My moving plans changed. Remove the moving companies from my saved pros, open my pending moving project, and tell me which pro quoted the lowest price — check that pro's profile for their rating and how fast they respond. Then cancel the project and start a much smaller replacement request for a studio move in zip 98101, telling me how many pros respond this time.""",
"""MOVER_ONE = "At Moving"
MOVER_TWO = "John Frank Moving"
LOWEST_QUOTE = 199
LOWEST_PRO = "Strok Industries Moving Company"
STROK_RATING = "4.9"
STROK_RESPONSE = "within a day"
N_NEW_QUOTES = 5
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "saved list", r"/account/saved")
    check_visited_path(judge, traj, "moving project", r"/projects/3")
    check_visited_path(judge, traj, "lowest-quote pro profile", r"/wa/kent/local-movers/strok-industries-moving-company/service/537096908478578695")
    check_visited_path(judge, traj, "local movers category", r"/k/local-movers/near-me")
    check_visited_path(judge, traj, "replacement wizard", r"/projects/new\?category=local-movers")
    check_visited_path(judge, traj, "replacement project page", r"/projects/6")''',
'''    check_answer_phrase(judge, answer, "removed mover one", MOVER_ONE)
    check_answer_phrase(judge, answer, "removed mover two", MOVER_TWO)
    check_answer_phrase(judge, answer, "lowest-quote pro", LOWEST_PRO)
    check_answer_number(judge, answer, "lowest quote", LOWEST_QUOTE,
                        ["quote", "lowest"])
    check_answer_phrase(judge, answer, "Strok rating", STROK_RATING)
    check_answer_phrase(judge, answer, "Strok response speed", STROK_RESPONSE)
    check_answer_any(judge, answer, "cancelled", ["cancel"])
    check_answer_number(judge, answer, "replacement quotes", N_NEW_QUOTES,
                        ["quotes", "respond", "received"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"saved_pros", "projects", "project_matches"})
    check_table_removed(judge, initial_db, after_db, "saved_pros", 2,
                        "user_id = 2 AND pro_id IN (117, 119)")
    check_row_updated(judge, initial_db, after_db, "projects", "id = 3",
                      "status", "cancelled")
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 2, 15, "98101", None, None, None, "matched", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 119, 1, 274, None, None, 0),
                       (27, 6, 117, 1, 174, None, None, 0),
                       (28, 6, 115, 1, 224, None, None, 0),
                       (29, 6, 124, 1, 233, None, None, 0),
                       (30, 6, 118, 1, 261, None, None, 0)])''')

# ---------------------------------------------------------------- task 11
TASKS[11] = V(11,
"""Log in with the demo account (email: carol.d@test.com, password: TestPass123!). I'm budgeting my daughter's quinceañera. Using the cost guides, compare what a makeup artist charges with what a DJ charges, and tell me which is more expensive. Then find the highest-rated Top Pro makeup artist based in Redmond, message them asking whether they're available for an October event, and request an estimate from them describing the quinceañera makeup for my daughter.""",
"""DJ_AVG = 550
MAKEUP_AVG = 167
MAKEUP_RANGE = "$156 - $178"
TARGET_PRO = "Mel Mua"
TARGET_PRO_PK = 549098172844007430
MEL_REPLY = "love to do your makeup"
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "makeup artist cost guide", r"/p/makeup-artist-prices")
    check_visited_path(judge, traj, "wedding DJ cost guide", r"/p/wedding-djs-cost")
    check_visited_path(judge, traj, "makeup artists category sorted", r"/k/makeup-artists/near-me\?sort=highest_rated")
    check_visited_path(judge, traj, "target pro profile", r"/wa/redmond/makeup-artists/mel-mua/service/549098172844007430")
    check_visited_path(judge, traj, "October message flow", r"/message/549098172844007430|/account/messages/2")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\?category=makeup-artists")
    check_visited_path(judge, traj, "project page", r"/projects/6")''',
'''    check_answer_number(judge, answer, "DJ average", DJ_AVG, "dj")
    check_answer_number(judge, answer, "makeup artist average", MAKEUP_AVG,
                        "makeup")
    check_answer_phrase(judge, answer, "makeup guide range", MAKEUP_RANGE)
    check_answer_phrase(judge, answer, "target pro", TARGET_PRO)
    check_answer_any(judge, answer, "Top Pro status", ["top pro"])
    check_answer_phrase(judge, answer, "Mel reply", MEL_REPLY)
    check_answer_phrase(judge, answer, "quinceanera", "quincea")''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"threads", "messages", "projects", "project_matches"})
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 3, 130, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None)])
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 3, 12, "98004", None, None, None, "matched", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 129, 1, 159, None, None, 0),
                       (27, 6, 130, 1, 162, None, None, 0),
                       (28, 6, 128, 1, 156, None, None, 0),
                       (29, 6, 131, 1, 158, None, None, 0),
                       (30, 6, 127, 1, 177, None, None, 0)])''')

# ---------------------------------------------------------------- task 12
TASKS[12] = V(12,
"""Log in with the demo account (email: alice.j@test.com, password: TestPass123!). My house cleaning project is finished but I never left a review. Open the project, note the hired pro's price and their response note, and check their profile's current reviews. Then leave them a 5-star review saying they were thorough, including the word "spotless". Reopen their profile to confirm your review is the most recent one, and message them asking whether they could return for a move-out clean next month — follow up asking whether they'd bring their own supplies. Report both replies.""",
"""HIRED_PRO = "Empire Cleaning Services"
HIRED_PRO_ID = 65
HIRED_PRICE = 244
RESPONSE_NOTE = "adjust after an on-site visit"
MOVEOUT_REPLY = "3-4 hours"
SUPPLIES_REPLY = "we bring all of our own supplies"
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "finished project", r"/projects/1")
    check_visited_path(judge, traj, "hired pro profile", r"/wa/kirkland/house-cleaning/empire-cleaning-services/service/476683242989297681")
    check_visited_path(judge, traj, "review form", r"/projects/1/review")
    check_visited_path(judge, traj, "move-out message flow", r"/message/476683242989297681|/account/messages/2")''',
'''    check_answer_phrase(judge, answer, "hired pro name", HIRED_PRO)
    check_answer_number(judge, answer, "hired price", HIRED_PRICE,
                        ["price", "hired", "quoted"])
    check_answer_phrase(judge, answer, "response note", RESPONSE_NOTE)
    check_answer_any(judge, answer, "spotless review", ["spotless"])
    check_answer_phrase(judge, answer, "move-out reply", MOVEOUT_REPLY)
    check_answer_phrase(judge, answer, "supplies reply", SUPPLIES_REPLY)''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"reviews", "threads", "messages"})
    check_table_added(judge, initial_db, after_db, "reviews",
                      [(857, HIRED_PRO_ID, "Alice Johnson", "Sep 26, 2026", 5,
                        None, "project:1", 1, "user")])
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 1, HIRED_PRO_ID, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None),
                       (5, 2, "user", None, None),
                       (6, 2, "pro", None, None)])''')

# ---------------------------------------------------------------- task 13
TASKS[13] = V(13,
"""Log in with the demo account (email: alice.j@test.com, password: TestPass123!). Read my existing message thread about cleaning supplies and tell me exactly what the pro said they bring. Then ask a different house cleaner the same question, follow up with them about Sunday availability, and ask the first cleaner the Sunday question too. Tell me how the two cleaners' answers compare.""",
"""FIRST_CLEANER = "Ipanema Cleaning Service"
SECOND_CLEANER = "Empire Cleaning Services"
SECOND_PRO_ID = 65
SUPPLIES_REPLY = "we bring all of our own supplies and equipment"
SUNDAY_REPLY = "happy to work around your schedule"
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "existing supplies thread", r"/account/messages/1")
    check_visited_path(judge, traj, "house cleaning category sorted", r"/k/house-cleaning/near-me\?sort=highest_rated")
    check_visited_path(judge, traj, "second cleaner profile", r"/wa/kirkland/house-cleaning/empire-cleaning-services/service/476683242989297681")
    check_visited_path(judge, traj, "second cleaner thread", r"/account/messages/2")
    check_visited_path(judge, traj, "first cleaner Sunday question", r"/account/messages/1")''',
'''    check_answer_phrase(judge, answer, "first cleaner", FIRST_CLEANER)
    check_answer_phrase(judge, answer, "second cleaner", SECOND_CLEANER)
    check_answer_phrase(judge, answer, "supplies replies", SUPPLIES_REPLY)
    check_answer_phrase(judge, answer, "Sunday replies", SUNDAY_REPLY)''',
'''    check_only_tables_changed(judge, initial_db, after_db, {"threads", "messages"})
    check_row_updated(judge, initial_db, after_db, "threads", "id = 1",
                      "updated_at", "2026-09-26 12:32:00.000000")
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 1, SECOND_PRO_ID, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None),
                       (5, 2, "user", None, None),
                       (6, 2, "pro", None, None),
                       (7, 1, "user", None, None),
                       (8, 1, "pro", None, None)])''')

# ---------------------------------------------------------------- task 14
TASKS[14] = V(14,
"""Log in with the demo account (email: bob.c@test.com, password: TestPass123!). Ants have invaded my kitchen. Check the cost guide for what an exterminator typically runs, then find the exterminators who are Top Pros and request quotes for indoor ant treatment in zip 98101 within a week, describing the problem. Hire the responder with the most reviews, mark the project complete, and leave them a 5-star review mentioning the ants. Confirm on their profile that your review shows, and tell me their name, their quote, and the guide's typical range.""",
"""GUIDE_RANGE = "$131 - $341"
HIRED_PRO = "Super Attic Solutions"
HIRED_PRO_ID = 38
HIRED_REVIEWS = 123
HIRED_QUOTE = 315
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "exterminator cost guide", r"/p/exterminators-prices")
    check_visited_path(judge, traj, "exterminators category", r"/k/exterminators/near-me")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\?category=exterminators")
    check_visited_path(judge, traj, "project page", r"/projects/6")
    check_visited_path(judge, traj, "review form", r"/projects/6/review")
    check_visited_path(judge, traj, "hired pro profile", r"/wa/kirkland/exterminators/super-attic-solutions/service/472430256251617281")''',
'''    check_answer_phrase(judge, answer, "guide typical range", GUIDE_RANGE)
    check_answer_phrase(judge, answer, "hired pro name", HIRED_PRO)
    check_answer_number(judge, answer, "hired pro reviews", HIRED_REVIEWS,
                        "review")
    check_answer_number(judge, answer, "hired quote", HIRED_QUOTE,
                        ["quote", "quoted"])
    check_answer_any(judge, answer, "ants review", ["ants", "ant"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"projects", "project_matches", "reviews"})
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 2, 11, "98101", None, "Within a week", None,
                        "completed", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 36, 1, 250, None, None, 0),
                       (27, 6, 40, 1, 170, None, None, 0),
                       (28, 6, 32, 1, 207, None, None, 0),
                       (29, 6, 41, 1, 137, None, None, 0),
                       (30, 6, HIRED_PRO_ID, 1, 315, None, None, 1)])
    check_table_added(judge, initial_db, after_db, "reviews",
                      [(857, HIRED_PRO_ID, "Bob Chen", "Sep 26, 2026", 5,
                        None, "project:6", 1, "user")])''')

# ---------------------------------------------------------------- task 15
TASKS[15] = V(15,
"""Log in with the demo account (email: alice.j@test.com, password: TestPass123!). Using the Kirkland city page, find the house cleaner with the most reviews, message them asking whether they bring their own supplies, and then request a quote from them for a standard cleaning of my 3-bedroom home.""",
"""TARGET_PRO = "Empire Cleaning Services"
TARGET_PRO_ID = 65
SUPPLIES_REPLY = "we bring all of our own supplies and equipment\"""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "Kirkland city page", r"/wa/kirkland")
    check_visited_path(judge, traj, "target profile",
                       r"/wa/kirkland/house-cleaning/empire-cleaning-services/service/476683242989297681")
    check_visited_path(judge, traj, "message flow",
                       r"/message/476683242989297681|/account/messages/")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\\?category=house-cleaning|/projects/new\\?")
    check_visited_path(judge, traj, "project page", r"/projects/6")''',
'''    check_answer_phrase(judge, answer, "target pro name", TARGET_PRO)
    check_answer_phrase(judge, answer, "supplies reply", SUPPLIES_REPLY)
    check_answer_any(judge, answer, "quote requested",
                     ["quote", "estimate", "request"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"threads", "messages", "projects", "project_matches"})
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 1, TARGET_PRO_ID, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None)])
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 1, 1, "98033", None, None, None, "matched", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 73, 1, 191, None, None, 0),
                       (27, 6, 66, 1, 184, None, None, 0),
                       (28, 6, 76, 1, 244, None, None, 0),
                       (29, 6, 67, 1, 245, None, None, 0),
                       (30, 6, 65, 1, 227, None, None, 0)])''')

# ---------------------------------------------------------------- task 16
TASKS[16] = V(16,
"""Log in with the demo account (email: david.k@test.com, password: TestPass123!). I want to get in shape this fall. Using the cost guide, tell me the typical price range for personal training sessions. Then find the highest-rated personal trainer based in Bellevue, message them to confirm they have twice-a-week slots, and request a quote from them describing twice-a-week strength sessions.""",
"""GUIDE_RANGE = "$40 - $100"
GUIDE_AVG = 55
TARGET_PRO = "Gaskill Personal Training"
TARGET_PRO_PK = 285389944820876322
GASKILL_REPLY = "morning and evening slots"
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "personal trainer cost guide", r"/p/personal-trainer-cost")
    check_visited_path(judge, traj, "trainers category sorted", r"/k/personal-trainers/near-me\?sort=highest_rated")
    check_visited_path(judge, traj, "target pro profile", r"/wa/bellevue/personal-trainers/gaskill-personal-training/service/285389944820876322")
    check_visited_path(judge, traj, "twice-a-week message flow", r"/message/285389944820876322|/account/messages/2")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\?category=personal-trainers")
    check_visited_path(judge, traj, "project page", r"/projects/6")''',
'''    check_answer_phrase(judge, answer, "guide typical range", GUIDE_RANGE)
    check_answer_number(judge, answer, "guide average", GUIDE_AVG, "average")
    check_answer_phrase(judge, answer, "target pro", TARGET_PRO)
    check_answer_phrase(judge, answer, "Gaskill reply", GASKILL_REPLY)
    check_answer_any(judge, answer, "twice-a-week quote",
                     ["twice-a-week", "twice a week"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"threads", "messages", "projects", "project_matches"})
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 4, 136, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None)])
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 4, 14, "98033", None, None, None, "matched", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 136, 1, 67, None, None, 0),
                       (27, 6, 138, 1, 90, None, None, 0),
                       (28, 6, 135, 1, 98, None, None, 0),
                       (29, 6, 133, 1, 60, None, None, 0),
                       (30, 6, 137, 1, 68, None, None, 0)])''')

# ---------------------------------------------------------------- task 17
TASKS[17] = V(17,
"""Log in with the demo account (email: alice.j@test.com, password: TestPass123!). I want my 75-inch TV mounted above the fireplace with the cables hidden and my sound bar connected. Request TV mounting quotes in zip 98052, answering the questionnaire to match my setup and describing the job. Hire the pro with the lowest quote, mark the project complete, and leave them a 5-star review mentioning the tidy cable work. Tell me how many pros responded and which one you hired.""",
"""N_RESPONDERS = 4
LOWEST_QUOTE = 127
HIRED_PRO = "Mmy"
HIRED_PRO_ID = 160
WIZARD_ANSWERS = ('[["Conceal cables/wires?", "Yes, I need to conceal cables and wires"], '
                  '["Sound system", "Sound bar"], '
                  '["TV installation location", "Wall mount above fireplace"]]')
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "TV mounting category", r"/k/tv-wall-mount-install/near-me")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\?category=tv-wall-mount-install")
    check_visited_path(judge, traj, "project page", r"/projects/6")
    check_visited_path(judge, traj, "review form", r"/projects/6/review")''',
'''    check_answer_number(judge, answer, "responders", N_RESPONDERS,
                        ["respond", "pros"])
    check_answer_number(judge, answer, "lowest quote", LOWEST_QUOTE,
                        ["quote", "lowest"])
    check_answer_phrase(judge, answer, "hired pro", HIRED_PRO)
    check_answer_any(judge, answer, "tidy cable review",
                     ["tidy cable", "tidy"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"projects", "project_matches", "reviews"})
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 1, 8, "98052", None, None, WIZARD_ANSWERS,
                        "completed", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 162, 1, 220, None, None, 0),
                       (27, 6, 163, 0, None, None, None, 0),
                       (28, 6, HIRED_PRO_ID, 1, 127, None, None, 1),
                       (29, 6, 161, 1, 173, None, None, 0),
                       (30, 6, 159, 1, 187, None, None, 0)])
    check_table_added(judge, initial_db, after_db, "reviews",
                      [(857, HIRED_PRO_ID, "Alice Johnson", "Sep 26, 2026", 5,
                        None, "project:6", 1, "user")])''')

# ---------------------------------------------------------------- task 18
TASKS[18] = V(18,
"""Log in with the demo account (email: carol.d@test.com, password: TestPass123!). Starting from the Services near me page, open the Events services group and go to the wedding and event makeup category. Sort the list by Most hires and tell me the top makeup artist's name, number of hires, and review count. Check their profile for Top Pro status and how fast they respond, message them about availability for an October 18 event, follow up asking about a pre-event trial, then save them to my saved pros. Report both replies.""",
"""TOP_PRO_NAME = "Mel Mua"
TOP_PRO_PK = 549098172844007430
TOP_HIRES = 121
TOP_REVIEWS = 71
TOP_RESPONSE = "28 min"
TRIAL_REPLY = "love to do your makeup"
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "services near me", r"/near-me")
    check_visited_path(judge, traj, "makeup category sorted by hires", r"/k/makeup-artists/near-me\?sort=most_hires")
    check_visited_path(judge, traj, "top pro profile", r"/wa/redmond/makeup-artists/mel-mua/service/549098172844007430")
    check_visited_path(judge, traj, "October 18 message flow", r"/message/549098172844007430|/account/messages/2")''',
'''    check_answer_phrase(judge, answer, "top pro name", TOP_PRO_NAME)
    check_answer_number(judge, answer, "top hires", TOP_HIRES, "hire")
    check_answer_number(judge, answer, "top reviews", TOP_REVIEWS, "review")
    check_answer_any(judge, answer, "top pro status", ["top pro"])
    check_answer_phrase(judge, answer, "response speed", TOP_RESPONSE)
    check_answer_phrase(judge, answer, "trial replies", TRIAL_REPLY)
    check_answer_any(judge, answer, "saved", ["saved", "save"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"saved_pros", "threads", "messages"})
    check_table_added(judge, initial_db, after_db, "saved_pros",
                      [(14, 3, 130, None)])
    check_table_added(judge, initial_db, after_db, "threads",
                      [(2, 3, 130, None, None)])
    check_table_added(judge, initial_db, after_db, "messages",
                      [(3, 2, "user", None, None),
                       (4, 2, "pro", None, None),
                       (5, 2, "user", None, None),
                       (6, 2, "pro", None, None)])''')

# ---------------------------------------------------------------- task 19
TASKS[19] = V(19,
"""Log in with the demo account (email: bob.c@test.com, password: TestPass123!). My refrigerator stopped cooling overnight and my food is spoiling. Find the appliance repair specialist who responds fastest, request a quote describing the emergency repair for my GE refrigerator, hire the pro with the lowest quote, and leave them a 5-star review mentioning the refrigerator. Tell me the lowest quote you received.""",
"""FASTEST_PRO = "Hotwire Hvac Refrigeration & Appliance Repair"
FASTEST_RESPONSE = "1 min"
LOWEST_QUOTE = 130
HIRED_PRO_ID = 18
WIZARD_ANSWERS = ('[["Appliance type", "Refrigerator"], '
                  '["Appliance brand", "GE"]]')
""",
'''    check_visited_path(judge, traj, "login page", r"/login")
    check_visited_path(judge, traj, "appliance category sorted by fastest response", r"/k/appliance-repair/near-me\?sort=fastest_response")
    check_visited_path(judge, traj, "fastest pro profile", r"/wa/woodinville/appliance-repair/hotwire-hvac-refrigeration-appliance-repair/service/500453696558571522")
    check_visited_path(judge, traj, "quote wizard", r"/projects/new\?category=appliance-repair")
    check_visited_path(judge, traj, "project page", r"/projects/6")
    check_visited_path(judge, traj, "review form", r"/projects/6/review")''',
'''    check_answer_phrase(judge, answer, "fastest pro", "Hotwire")
    check_answer_phrase(judge, answer, "fastest response", FASTEST_RESPONSE)
    check_answer_phrase(judge, answer, "GE refrigerator", "GE")
    check_answer_number(judge, answer, "lowest quote", LOWEST_QUOTE,
                        ["quote", "lowest"])
    check_answer_any(judge, answer, "refrigerator review", ["refrigerator"])''',
'''    check_only_tables_changed(judge, initial_db, after_db,
                              {"projects", "project_matches", "reviews"})
    check_table_added(judge, initial_db, after_db, "projects",
                      [(6, 2, 6, "98101", None, None, WIZARD_ANSWERS,
                        "completed", None)])
    check_table_added(judge, initial_db, after_db, "project_matches",
                      [(26, 6, 11, 1, 275, None, None, 0),
                       (27, 6, 9, 1, 328, None, None, 0),
                       (28, 6, HIRED_PRO_ID, 1, 130, None, None, 1),
                       (29, 6, 17, 1, 319, None, None, 0),
                       (30, 6, 14, 1, 232, None, None, 0)])
    check_table_added(judge, initial_db, after_db, "reviews",
                      [(857, HIRED_PRO_ID, "Bob Chen", "Sep 26, 2026", 5,
                        None, "project:6", 1, "user")])''')

for n, text in TASKS.items():
    (OUT / f"verify_{n}.py").write_text(text, encoding="utf-8")
    print(f"wrote verify_{n}.py")
print(f"{len(TASKS)} verifiers emitted")
