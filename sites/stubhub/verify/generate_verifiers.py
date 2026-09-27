#!/usr/bin/env python3
"""Generate sites/stubhub/verify/verify_{0..20}.py with frozen ground truths.

Every ground truth below was extracted from the deterministic seed
(instance_seed/stubhub.db, md5 c71165b3…) and cross-checked against the
reviewer's honest live walks (runs/StubHub--N). Deterministic tie-breaks follow
the site's own sort orders (price, then section string).
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent

HEADER = '''#!/usr/bin/env python3
"""Verify StubHub--{n}.

{ques}
"""
from verify_lib import (Judge, check_answer_any, check_answer_number, check_answer_phrase,
                        check_answer_regex, check_answer_one_of, check_read_only,
                        check_only_tables_changed, check_table_deltas, check_trajectory_identity,
                        check_visited_path, final_answer, run_verifier)

TASK_ID = "StubHub--{n}"

'''

FOOTER_RO = '''

def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    {nav}
    {checks}
    check_read_only(judge, initial_db, after_db)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
'''

FOOTER_ST = '''

def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
    {nav}
    {checks}
    {delta}
    check_only_tables_changed(judge, initial_db, after_db, {allowed})


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
'''

QUES = {}
for line in Path("/data/zhaoyang-user-projects/websyn/wh-stubhub-review-wt/sites/stubhub/tasks.jsonl").read_text().splitlines():
    import json
    row = json.loads(line)
    QUES[int(row["id"].split("--")[1])] = row["ques"]


def nav(*gates):
    return "\n    ".join(f'check_visited_path(judge, traj, "{name}", r"{pattern}")'
                         for name, pattern in gates)


SPECS = {}

# ---------------------------------------------------------------- T0
SPECS[0] = dict(
    ques=QUES[0],
    nav=nav(
        ("visited_seahawks_performer", r"/seattle-seahawks-tickets/performer/1945"),
        ("visited_game_1_chargers", r"/seattle-seahawks-seattle-tickets-10-4-2026/event/160436504"),
        ("visited_game_2_49ers", r"/seattle-seahawks-seattle-tickets-10-11-2026/event/160436498"),
        ("visited_game_3_chiefs", r"/seattle-seahawks-seattle-tickets-10-25-2026/event/160436501"),
        ("visited_game_4_bears", r"/seattle-seahawks-seattle-tickets-11-2-2026/event/160436503"),
        ("visited_game_5_cardinals", r"/seattle-seahawks-seattle-tickets-11-8-2026/event/160436506"),
        ("visited_game_6_cowboys", r"/seattle-seahawks-seattle-tickets-12-7-2026/event/160436508"),
        ("visited_game_7_giants", r"/seattle-seahawks-seattle-tickets-12-13-2026/event/160436500"),
        ("visited_game_8_rams", r"/seattle-seahawks-seattle-tickets-12-25-2026/event/160436502"),
    ),
    checks='''
    games = [("Los Angeles Chargers", 236), ("San Francisco 49ers", 367),
             ("Kansas City Chiefs", 364), ("Chicago Bears", 298),
             ("Arizona Cardinals", 194), ("Dallas Cowboys", 297),
             ("New York Giants", 194), ("Los Angeles Rams", 275)]
    for opp, price in games:
        check_answer_phrase(judge, answer, f"opponent_{opp.split()[0].lower()}_{price}", opp)
        check_answer_number(judge, answer, f"getin_{opp.split()[0].lower()}", price)
    check_answer_number(judge, answer, "cheapest_price", 194)
    # tie at $194: the Cardinals game (get-in 344 Row EE) or the Giants game (300 Row DD)
    judge.check("cheapest_game_named",
                "cardinals" in answer.casefold() or "giants" in answer.casefold(),
                "answer must name the cheapest game (Cardinals or Giants, both $194)")
    judge.check("cheapest_getin_section",
                bool(__import__("re").search(r"344|300", answer)),
                "answer must report the cheapest game's get-in section (344 for Cardinals / 300 for Giants)")
    judge.check("cheapest_getin_row",
                "ee" in answer.casefold().replace(" ", "") or "dd" in answer.casefold().replace(" ", ""),
                "answer must report the cheapest game's get-in row (EE / DD)")
    check_answer_number(judge, answer, "highest_getin", 367)''',
    state="ro",
)

# ---------------------------------------------------------------- T1
SPECS[1] = dict(
    ques=QUES[1],
    nav=nav(
        ("visited_chargers_event", r"/seattle-seahawks-seattle-tickets-10-4-2026/event/160436504"),
        ("applied_qty4_price400_clearview",
         r"/seattle-seahawks-seattle-tickets-10-4-2026/event/160436504\?quantity=4&price_max=400&sort=price&features=Clear\+view|features=Clear\+view[^ ]*quantity=4|quantity=4[^ ]*features=Clear"),
        ("applied_zone_300",
         r"/seattle-seahawks-seattle-tickets-10-4-2026/event/160436504\?[^ ]*zone=300\+Level"),
    ),
    checks='''
    check_answer_number(judge, answer, "matching_listing_count", 5)
    check_answer_phrase(judge, answer, "cheapest_match_section", "Upper 300-Level")
    check_answer_number(judge, answer, "cheapest_match_price", 265)
    check_answer_phrase(judge, answer, "zone_cheapest_section", "307")
    check_answer_phrase(judge, answer, "zone_cheapest_row", "II")
    check_answer_number(judge, answer, "zone_cheapest_price", 324)
    judge.check("cheaper_option_for_four",
                "clear" in answer.casefold() and "1060" in re.sub(r"[\\$,]", "", answer),
                "answer must state the clear-view match is cheaper for four tickets ($1,060 vs $1,296)")
    check_answer_number(judge, answer, "four_ticket_cheaper_total", 1060)''',
    state="ro",
    extra_import="import re\n",
)

# ---------------------------------------------------------------- T2
SPECS[2] = dict(
    ques=QUES[2],
    nav=nav(
        ("visited_pass_event", r"/metallica-las-vegas-tickets-10-1-2026/event/160572545"),
        ("visited_oct1_single", r"/metallica-las-vegas-tickets-10-1-2026/event/160569378"),
        ("visited_oct3_single", r"/metallica-las-vegas-tickets-10-3-2026/event/160569380"),
    ),
    checks='''
    check_answer_number(judge, answer, "pass_listing_count", 29)
    check_answer_number(judge, answer, "pass_getin", 1137)
    check_answer_phrase(judge, answer, "pass_cheapest_section", "310")
    check_answer_number(judge, answer, "oct1_listing_count", 26)
    check_answer_number(judge, answer, "oct1_getin", 749)
    check_answer_phrase(judge, answer, "oct1_cheapest_section", "407")
    check_answer_number(judge, answer, "oct3_listing_count", 10)
    check_answer_number(judge, answer, "oct3_getin", 1124)
    check_answer_phrase(judge, answer, "oct3_cheapest_section", "110")
    check_answer_phrase(judge, answer, "venue_name", "Sphere")
    check_answer_phrase(judge, answer, "venue_city", "Las Vegas")
    judge.check("per_night_computed",
                bool(re.search(r"56[89](?:\\.\d+)?", answer)),
                "answer must compute the pass's implied cost per night (~$568-569)")
    judge.check("pass_vs_singles_verdict",
                "pass" in answer.casefold() and re.search(r"cheaper", answer.casefold()),
                "answer must state the two-day pass is the cheaper way to see both shows")''',
    state="ro",
    extra_import="import re\n",
)

# ---------------------------------------------------------------- T3
SPECS[3] = dict(
    ques=QUES[3],
    nav=nav(
        ("visited_cardinals_event", r"/seattle-seahawks-seattle-tickets-11-8-2026/event/160436506"),
        ("visited_listing", r"/event/160436506/listing/225"),
        ("checkout_review", r"/secure/checkout/review"),
        ("checkout_payment", r"/secure/checkout/payment"),
        ("checkout_confirm", r"/secure/checkout/confirm"),
        ("checkout_confirmation", r"/secure/checkout/confirmation/41801303"),
    ),
    checks='''
    check_answer_number(judge, answer, "order_reference", 41801303)
    check_answer_number(judge, answer, "delivery_fee_ups", "14.95")
    check_answer_number(judge, answer, "processing_fee", "2.95")
    check_answer_number(judge, answer, "final_total", "405.90")''',
    state="st",
    allowed='("orders", "listings", "notifications")',
    delta='''check_table_deltas(judge, initial_db, after_db, {
        "orders": {"added": [(9,)]},
        "listings": {"changed": {(225,): {"is_sold": (0, 1)}}},
        "notifications": {"added_count": 1},
    })
    row = after_db.execute("SELECT * FROM orders WHERE order_number='41801303'").fetchone()
    judge.check("order_row_exact",
                row is not None and row["user_id"] == 2 and row["event_id"] == 134
                and row["listing_id"] == 225 and row["quantity"] == 2
                and row["delivery_method"] == "ups" and row["delivery_fee"] == 14.95
                and row["processing_fee"] == 2.95 and row["total"] == 405.9
                and row["status"] == "Confirmed",
                f"order row must match the frozen delta: {dict(row) if row else None}")''',
)

# ---------------------------------------------------------------- T4
SPECS[4] = dict(
    ques=QUES[4],
    nav=nav(
        ("visited_sell_landing", r"/selltickets(\?|$)"),
        ("visited_sell_form", r"/selltickets/event/160436503"),
        ("visited_my_listings", r"/secure/myaccount/listings"),
    ),
    checks='''
    check_answer_number(judge, answer, "new_price_shown", 180)
    check_answer_number(judge, answer, "alice_listing_count", 2)
    check_answer_number(judge, answer, "seeded_listing_price", 89)
    judge.check("combined_asking_value",
                bool(re.search(r"269|716", answer)),
                "answer must report the combined asking value ($269 per-ticket sum / $716 total)")
    check_answer_phrase(judge, answer, "game_venue", "Lumen Field")
    judge.check("game_date_displayed",
                "Nov 3" in answer or "November 3" in answer or "Nov 2" in answer,
                "answer must report the game's displayed date (Nov 3 as shown on the site)")''',
    extra_import="import re\n",
    state="st",
    allowed='("listings", "events")',
    delta='''check_table_deltas(judge, initial_db, after_db, {
        "listings": {"added": [(20886,)]},
        "events": {"changed": {(132,): {"listing_count": (10, 12)}}},
    })
    row = after_db.execute("SELECT * FROM listings WHERE id=20886").fetchone()
    judge.check("new_listing_row_exact",
                row is not None and row["event_id"] == 132 and row["section"] == "220"
                and row["row"] == "14" and row["quantity"] == 2 and row["price"] == 180
                and row["seller_id"] == 1,
                f"repriced listing must be 220/row 14/qty 2/$180: {dict(row) if row else None}")''',
)

# ---------------------------------------------------------------- T5
SPECS[5] = dict(
    ques=QUES[5],
    nav=nav(
        ("visited_gift_cards_before", r"/gift-cards"),
        ("visited_gift_cards_after", r"/gift-cards"),
    ),
    checks='''
    for amount in (25, 50, 75, 100, 150, 200, 250, 500):
        check_answer_number(judge, answer, f"amount_{amount}", amount)
    for design in ("classic", "birthday", "holiday", "sports", "concert"):
        check_answer_phrase(judge, answer, f"design_{design}", design)
    check_answer_number(judge, answer, "purchased_amount", 150)
    check_answer_phrase(judge, answer, "recipient", "Danny")
    check_answer_regex(judge, answer, "gift_code_format", r"\\bSH[A-Z0-9]{10}\\b",
                       "a SH+10-char gift card code")
    judge.check("code_not_seed_frozen",
                not re.search(r"SHGC\d+", answer),
                "the new gift card code must not be one of the seeded fixture codes")
    check_answer_number(judge, answer, "gift_cards_in_history", 2)
    check_answer_number(judge, answer, "earliest_amount", 100)
    judge.check("earliest_purchase_date",
                "Aug 23" in answer or "August 23" in answer,
                "answer must report the earliest gift card's purchase date (Aug 23, 2026)")''',
    state="st",
    allowed='("gift_card_orders",)',
    delta='''added, removed, changed = table_diff(initial_db, after_db, "gift_card_orders")
    judge.check("gift_card_added", len(added) == 1 and not removed and not changed,
                f"exactly one new gift card row: +{list(added)} -{list(removed)} ~{list(changed)}")
    for key, row in added.items():
        judge.check("gift_card_row_exact",
                   row["user_id"] == 3 and row["amount"] == 150
                   and row["recipient_name"] == "Danny"
                   and row["recipient_email"] == "danny.gift@example.com"
                   and row["design"] == "holiday"
                   and re.fullmatch(r"SH[A-Z0-9]{10}", row["code"] or ""),
                   f"new gift card must be the $150 holiday card for Danny: {dict(row)}")''',
    extra_import="import re\nfrom verify_lib import table_diff\n",
)

# ---------------------------------------------------------------- T6
SPECS[6] = dict(
    ques=QUES[6],
    nav=nav(
        ("visited_metallica_page", r"/metallica-tickets/performer/8147"),
        ("visited_giants_event", r"/seattle-seahawks-seattle-tickets-12-13-2026/event/160436500"),
        ("visited_similar_artist", r"/[\w-]+-tickets/performer/(?!8147)"),
        ("visited_favorites", r"/favorites"),
    ),
    checks='''
    check_answer_number(judge, answer, "favorites_total", 3)
    check_answer_phrase(judge, answer, "favorite_metallica", "metallica")
    check_answer_phrase(judge, answer, "favorite_giants_game", "Giants")
    judge.check("similar_artist_favorited",
                "olivia rodrigo" in answer.casefold() or "similar" in answer.casefold(),
                "answer must include the favorited similar artist (Olivia Rodrigo, the first "
                "similar-artist card on Metallica's page)")''',
    state="st",
    allowed='("favorites", "performers")',
    delta='''added, removed, changed = table_diff(initial_db, after_db, "favorites")
    judge.check("three_favorites_added", len(added) == 3 and not removed,
                f"exactly three new favorite rows: +{list(added)} -{list(removed)}")
    perfs = [r["performer_id"] for r in added.values() if r["performer_id"]]
    events = [r["event_id"] for r in added.values() if r["event_id"]]
    judge.check("favorites_shape",
                393 in perfs and 129 in events and len(perfs) == 2 and len(events) == 1
                and all(r["user_id"] == 4 for r in added.values()),
                f"david must favorite metallica (393), one similar artist, and the Giants game (129): {[(r['performer_id'], r['event_id']) for r in added.values()]}")
    a2, r2, c2 = table_diff(initial_db, after_db, "performers")
    judge.check("follower_bumps",
                (393,) in c2 and all(v[1]["followers"] == v[0]["followers"] + 1 for v in c2.values())
                and len(c2) == 2,
                f"exactly the two favorited performers get +1 follower: {[(k, v[0]['followers'], v[1]['followers']) for k, v in c2.items()]}")''',
    extra_import="import re\nfrom verify_lib import table_diff\n",
)

# ---------------------------------------------------------------- T7
SPECS[7] = dict(
    ques=QUES[7],
    nav=nav(
        ("searched_metal", r"/search\?q=metal"),
        ("suggestions_metal", r"/secure/search/getSuggestedSearches\?q=metal"),
        ("searched_seattle", r"/search\?q=seattle"),
        ("suggestions_seattle", r"/secure/search/getSuggestedSearches\?q=seattle"),
        ("visited_sounders", r"/seattle-sounders-fc-tickets/performer/388488"),
        ("visited_mariners", r"/seattle-mariners-tickets/performer/1043"),
    ),
    checks='''
    check_answer_phrase(judge, answer, "suggestion_metal", "metallica")
    for name in ("seattle kraken", "seattle mariners", "seattle seahawks",
                 "seattle sounders fc"):
        check_answer_phrase(judge, answer, f"suggestion_seattle_{name.split()[1]}", name)
    check_answer_number(judge, answer, "sounders_followers", "56,600")
    check_answer_number(judge, answer, "sounders_events", 5)
    check_answer_phrase(judge, answer, "sounders_next_event", "Minnesota United")
    check_answer_phrase(judge, answer, "sounders_venue", "Lumen Field")
    check_answer_number(judge, answer, "mariners_followers", "75,200")
    check_answer_number(judge, answer, "mariners_events", 2)
    check_answer_phrase(judge, answer, "mariners_next_event", "Los Angeles Angels")
    check_answer_phrase(judge, answer, "mariners_venue", "T-Mobile Park")
    judge.check("more_events_verdict",
                "mariners" in answer.casefold() and "more" in answer.casefold(),
                "answer must state the Mariners have more upcoming events")''',
    state="ro",
)

# ---------------------------------------------------------------- T8
SPECS[8] = dict(
    ques=QUES[8],
    nav=nav(
        ("visited_comedy_subcategory", r"/comedy-tickets/category/209"),
        ("visited_rocky_horror", r"/the-rocky-horror-show-new-york-tickets-9-26-2026/event/161069710"),
        ("visited_little_shop", r"/little-shop-of-horrors-la-mirada-tickets-9-26-2026/event/161174556"),
        ("visited_garry_starr", r"/garry-starr-new-york-tickets-9-26-2026/event/162068544"),
    ),
    checks='''
    for sub in ("Musicals", "Plays", "Comedy", "Family", "Classical", "Broadway"):
        check_answer_phrase(judge, answer, f"subcategory_{sub.lower()}", sub)
    judge.check("subcategory_dance_ballet",
                "Dance" in answer and ("Ballet" in answer or "Dance / Ballet" in answer),
                "answer must list the Dance / Ballet subcategory")
    check_answer_phrase(judge, answer, "comedy_event_1", "Rocky Horror")
    check_answer_phrase(judge, answer, "comedy_event_2", "Little Shop of Horrors")
    check_answer_phrase(judge, answer, "comedy_event_3", "Garry Starr")
    check_answer_number(judge, answer, "rocky_getin", 104)
    check_answer_number(judge, answer, "rocky_count", 14)
    check_answer_number(judge, answer, "little_shop_getin", 400)
    check_answer_number(judge, answer, "little_shop_count", 3)
    check_answer_number(judge, answer, "garry_getin", 162)
    check_answer_number(judge, answer, "garry_count", 24)
    judge.check("most_listings_verdict", "Garry Starr" in answer,
                "answer must name Garry Starr as the event with the most listings")''',
    state="ro",
)

# ---------------------------------------------------------------- T9
SPECS[9] = dict(
    ques=QUES[9],
    nav=nav(
        ("searched_salome", r"/search\?q=salome"),
        ("visited_salome_1017", r"/seattle-opera-seattle-tickets-10-17-2026/event/161306164"),
        ("visited_salome_1023", r"/seattle-opera-seattle-tickets-10-23-2026/event/161306174"),
        ("visited_salome_1025", r"/seattle-opera-seattle-tickets-10-25-2026/event/161306180"),
        ("visited_salome_1028", r"/seattle-opera-seattle-tickets-10-28-2026/event/161306184"),
        ("visited_salome_1031", r"/seattle-opera-seattle-tickets-10-31-2026/event/161306189"),
    ),
    checks='''
    for date, price in (("10-17", 123), ("10-23", 120), ("10-25", 153),
                       ("10-28", 89), ("10-31", 117)):
        check_answer_number(judge, answer, f"getin_{date}", price)
    check_answer_number(judge, answer, "first_listings", 27)
    check_answer_number(judge, answer, "second_listings", 24)
    judge.check("more_listings_verdict", "10-17" in answer,
                "answer must name the Oct 17 performance as having more listings (27 vs 24)")
    check_answer_number(judge, answer, "lower_getin", 120)
    check_answer_phrase(judge, answer, "venue_full", "McCaw Hall")
    check_answer_phrase(judge, answer, "venue_city", "Seattle")
    check_answer_phrase(judge, answer, "first_cheapest_section", "ST 41")
    check_answer_phrase(judge, answer, "second_cheapest_section", "ST 42")''',
    state="ro",
)

# ---------------------------------------------------------------- T10
SPECS[10] = dict(
    ques=QUES[10],
    nav=nav(
        ("visited_purchases", r"/secure/myaccount/purchases"),
        ("visited_order_detail", r"/secure/myaccount/purchases/41810907|/secure/myaccount/purchases/41811044"),
        ("visited_sales", r"/secure/myaccount/sales"),
        ("visited_listings", r"/secure/myaccount/listings"),
        ("visited_payments", r"/secure/myaccount/payments"),
    ),
    checks='''
    check_answer_number(judge, answer, "order_metallica_ref", 41810907)
    check_answer_number(judge, answer, "order_metallica_total", "2,572.95")
    check_answer_phrase(judge, answer, "order_metallica_delivery", "Instant download")
    check_answer_phrase(judge, answer, "order_metallica_status", "Confirmed")
    check_answer_number(judge, answer, "order_rush_ref", 41811044)
    check_answer_number(judge, answer, "order_rush_total", "1,106.95")
    check_answer_phrase(judge, answer, "order_rush_delivery", "Mobile transfer")
    check_answer_phrase(judge, answer, "order_rush_status", "Delivered")
    judge.check("largest_purchase",
                "2,572.95" in answer or "Metallica" in answer,
                "answer must identify the Metallica 2-day-pass order as the largest total")
    check_answer_number(judge, answer, "sale_payout", "118.40")
    check_answer_phrase(judge, answer, "sale_status", "Paid")
    check_answer_number(judge, answer, "active_listing_price", 89)
    check_answer_number(judge, answer, "cards_on_file", 2)''',
    state="ro",
)

# ---------------------------------------------------------------- T11
SPECS[11] = dict(
    ques=QUES[11],
    nav=nav(
        ("visited_payments_before", r"/secure/myaccount/payments"),
        ("added_card_post", r"/secure/myaccount/payments"),
    ),
    checks='''
    check_answer_phrase(judge, answer, "card_before_visa", "4242")
    check_answer_phrase(judge, answer, "card_before_mc", "8321")
    check_answer_phrase(judge, answer, "new_card_last4", "4444")
    judge.check("new_card_default",
                "default" in answer.casefold() and "4444" in answer,
                "answer must state the new Mastercard 4444 is the default")
    judge.check("old_card_removed",
                "8321" in answer and ("remove" in answer.casefold() or "no longer" in answer.casefold()),
                "answer must state the older non-default card 8321 was removed")''',
    state="st",
    allowed='("payment_cards",)',
    delta='''added, removed, changed = table_diff(initial_db, after_db, "payment_cards")
    judge.check("card_delta_shape", len(added) == 1 and len(removed) == 1 and len(changed) == 1,
                f"one card added, one removed, one changed: +{list(added)} -{list(removed)} ~{list(changed)}")
    for key, row in added.items():
        judge.check("new_card_row", row["user_id"] == 1 and row["brand"] == "Mastercard"
                    and row["last4"] == "4444" and row["holder"] == "Alice Johnson"
                    and row["is_default"] == 1,
                    f"new card must be Alice's default Mastercard 4444: {dict(row)}")
    for key, row in removed.items():
        judge.check("removed_card_row", row["last4"] == "8321",
                    f"removed card must be the older non-default Mastercard 8321: {dict(row)}")
    for key, (before, after) in changed.items():
        judge.check("old_default_cleared", before["last4"] == "4242" and after["is_default"] == 0,
                    "the Visa 4242 must no longer be the default")''',
    extra_import="from verify_lib import table_diff\n",
)

# ---------------------------------------------------------------- T12
SPECS[12] = dict(
    ques=QUES[12],
    nav=nav(
        ("visited_register", r"/secure/register"),
        ("visited_49ers_event", r"/seattle-seahawks-seattle-tickets-10-11-2026/event/160436498"),
        ("visited_listing", r"/event/160436498/listing/1189"),
        ("checkout_review", r"/secure/checkout/review"),
        ("checkout_payment", r"/secure/checkout/payment"),
        ("checkout_confirmation", r"/secure/checkout/confirmation/41801303"),
        ("visited_purchase_history", r"/secure/myaccount/purchases"),
    ),
    checks='''
    check_answer_number(judge, answer, "order_reference", 41801303)
    check_answer_number(judge, answer, "final_total", "369.95")
    judge.check("order_in_history_confirmed",
                "appears" in answer.casefold() and "history" in answer.casefold(),
                "answer must confirm the order appears in the purchase history")''',
    state="st",
    allowed='("users", "orders", "listings", "payment_cards", "notifications")',
    delta='''added_u, _, _ = table_diff(initial_db, after_db, "users")
    judge.check("new_user_created", len(added_u) == 1, f"exactly one new user: {list(added_u)}")
    new_uid = next(iter(added_u))[0] if added_u else None
    added_o, _, _ = table_diff(initial_db, after_db, "orders")
    judge.check("new_order_created", len(added_o) == 1, f"exactly one new order: {list(added_o)}")
    for key, row in added_o.items():
        judge.check("order_row_exact",
                   row["order_number"] == "41801303" and row["user_id"] == new_uid
                   and row["event_id"] == 128 and row["listing_id"] == 1189
                   and row["quantity"] == 1 and row["delivery_method"] == "instant"
                   and row["delivery_fee"] == 0.0 and row["processing_fee"] == 2.95
                   and row["total"] == 369.95 and row["status"] == "Confirmed",
                   f"order must be the single 49ers ticket at $369.95: {dict(row)}")
    _, _, changed_l = table_diff(initial_db, after_db, "listings")
    judge.check("listing_1189_sold",
                (1189,) in changed_l and changed_l[(1189,)][1]["is_sold"] == 1,
                "listing 1189 must be marked sold")
    added_c, _, _ = table_diff(initial_db, after_db, "payment_cards")
    judge.check("new_card_created", len(added_c) == 1
                and next(iter(added_c.values()))["user_id"] == new_uid,
                f"the new user's payment card: {list(added_c)}")
    added_n, _, _ = table_diff(initial_db, after_db, "notifications")
    judge.check("notification_created", len(added_n) == 1
                and next(iter(added_n.values()))["user_id"] == new_uid,
                f"one order notification for the new user: {list(added_n)}")''',
    extra_import="from verify_lib import table_diff\n",
)

# ---------------------------------------------------------------- T13
SPECS[13] = dict(
    ques=QUES[13],
    nav=nav(
        ("visited_kraken_page", r"/seattle-kraken-tickets/performer/900000460"),
        ("paginated_to_last_page", r"/seattle-kraken-tickets/performer/900000460\?page=3"),
    ),
    checks='''
    check_answer_number(judge, answer, "total_home_games", 41)
    check_answer_phrase(judge, answer, "venue_name", "Climate Pledge Arena")
    check_answer_phrase(judge, answer, "venue_city", "Seattle")
    check_answer_phrase(judge, answer, "first_opponent", "Calgary Flames")
    check_answer_number(judge, answer, "first_getin", 65)
    check_answer_phrase(judge, answer, "last_opponent", "Winnipeg Jets")
    check_answer_number(judge, answer, "last_getin", 90)
    for opp in ("Vegas Golden Knights", "Detroit Red Wings", "Utah Mammoth"):
        check_answer_phrase(judge, answer, f"next_three_{opp.split()[0].lower()}", opp)''',
    state="ro",
)

# ---------------------------------------------------------------- T14
SPECS[14] = dict(
    ques=QUES[14],
    nav=nav(
        ("visited_49ers_event", r"/seattle-seahawks-seattle-tickets-10-11-2026/event/160436498"),
        ("zone_100_filter", r"/event/160436498\?[^ ]*zone=100\+Level"),
        ("zone_200_filter", r"/event/160436498\?[^ ]*zone=200\+Level"),
        ("zone_300_filter", r"/event/160436498\?[^ ]*zone=300\+Level"),
    ),
    checks='''
    check_answer_phrase(judge, answer, "zone100_section", "150")
    check_answer_number(judge, answer, "zone100_price", 477)
    check_answer_phrase(judge, answer, "zone200_section", "215")
    check_answer_number(judge, answer, "zone200_price", 645)
    check_answer_phrase(judge, answer, "zone300_section", "302")
    check_answer_number(judge, answer, "zone300_price", 367)
    judge.check("cheapest_zone_verdict", "300" in answer and "cheapest" in answer.casefold(),
                "answer must state the 300 Level has the cheapest get-in")
    check_answer_number(judge, answer, "zone_gap", 278)
    check_answer_number(judge, answer, "total_listings", 28)''',
    state="ro",
)

# ---------------------------------------------------------------- T15
SPECS[15] = dict(
    ques=QUES[15],
    nav=nav(
        ("visited_chargers_event", r"/seattle-seahawks-seattle-tickets-10-4-2026/event/160436504"),
        ("qty4_filter", r"/event/160436504\?[^ ]*quantity=4"),
        ("visited_listing_detail", r"/event/160436504/listing/\d+"),
    ),
    checks='''
    check_answer_phrase(judge, answer, "listing_section", "Upper 300-Level")
    check_answer_number(judge, answer, "listing_price", 265)
    check_answer_phrase(judge, answer, "listing_features_clearview", "Clear view")
    judge.check("seat_view_photo_answered",
                "seat view" in answer.casefold(),
                "answer must state whether a seat view photo appears")
    check_answer_number(judge, answer, "subtotal_qty2", 530)
    check_answer_number(judge, answer, "total_qty2", "532.95")
    check_answer_number(judge, answer, "subtotal_qty4", 1060)
    check_answer_number(judge, answer, "total_qty4", "1062.95")
    judge.check("processing_fee_verdict",
                ("does not change" in answer.casefold() or "doesn't change" in answer.casefold()
                 or "same" in answer.casefold()),
                "answer must state the processing fee does not change with quantity")
    check_answer_number(judge, answer, "per_ticket_qty2", "266.48")
    check_answer_number(judge, answer, "per_ticket_qty4", "265.74")''',
    state="ro",
)

# ---------------------------------------------------------------- T16
SPECS[16] = dict(
    ques=QUES[16],
    nav=nav(
        ("visited_chargers_event", r"/seattle-seahawks-seattle-tickets-10-4-2026/event/160436504"),
        ("best_deal_sort", r"/event/160436504\?[^ ]*sort=best_deal"),
    ),
    checks='''
    for section, cur, was, save, pct in (("239", 449, 659, 210, 32),
                                         ("CLB212", 485, 687, 202, 29),
                                         ("337", 244, 409, 165, 40)):
        check_answer_phrase(judge, answer, f"section_{section}", section)
        check_answer_number(judge, answer, f"current_{section}", cur)
        check_answer_number(judge, answer, f"original_{section}", was)
        check_answer_number(judge, answer, f"saving_{section}", save)
        judge.check(f"percent_{section}",
                    re.search(rf"{pct}%", answer) is not None,
                    f"answer must compute the {section} saving as {pct}%")
    judge.check("biggest_discount_section", "239" in answer,
                "answer must name section 239 as the biggest discount")
    check_answer_number(judge, answer, "total_listings", 30)''',
    state="ro",
    extra_import="import re\n",
)

# ---------------------------------------------------------------- T17
SPECS[17] = dict(
    ques=QUES[17],
    nav=nav(
        ("visited_oct1_single", r"/metallica-las-vegas-tickets-10-1-2026/event/160569378"),
        ("visited_nearby_pass", r"/metallica-las-vegas-tickets-10-1-2026/event/160572545"),
        ("visited_nearby_oct3", r"/metallica-las-vegas-tickets-10-3-2026/event/160569380"),
        ("visited_nearby_pass2", r"/metallica-las-vegas-tickets-10-8-2026/event/160611325"),
        ("visited_nearby_oct8", r"/metallica-las-vegas-tickets-10-8-2026/event/160611244"),
    ),
    checks='''
    check_answer_number(judge, answer, "single_night_getin", 749)
    for label, getin, count in (("pass_1_3", 1137, 29), ("oct3", 1124, 10),
                                ("pass_8_10", 1092, 27), ("oct8", 725, 25)):
        check_answer_number(judge, answer, f"nearby_getin_{label}", getin)
        check_answer_number(judge, answer, f"nearby_count_{label}", count)
    judge.check("cheapest_nearby_verdict",
                "725" in answer and ("Oct 8" in answer or "October 8" in answer or "8" in answer),
                "answer must name the Oct 8 single night as the cheapest nearby get-in ($725)")
    judge.check("pass_comparison",
                "1137" in answer and "749" in answer,
                "answer must compare the single-night get-in ($749) with the two-day pass ($1,137)")''',
    state="ro",
)

# ---------------------------------------------------------------- T18
SPECS[18] = dict(
    ques=QUES[18],
    nav=nav(
        ("visited_explore_p1", r"/explore(\?page=1)?$|/explore$"),
        ("visited_explore_p2", r"/explore\?page=2"),
        ("visited_earliest_event", r"/pacific-northwest-ballet-seattle-tickets-9-26-2026/event/161322492"),
    ),
    checks='''
    check_answer_phrase(judge, answer, "p1_event_1", "Serenade")
    check_answer_phrase(judge, answer, "p1_event_2", "Greenshield")
    check_answer_phrase(judge, answer, "p1_event_3", "Lovers Rock")
    check_answer_phrase(judge, answer, "p2_event_1", "Gnash")
    check_answer_phrase(judge, answer, "p2_event_2", "Kamelot")
    check_answer_phrase(judge, answer, "p2_event_3", "Beth Stelling")
    check_answer_number(judge, answer, "total_events", 1267)
    judge.check("earliest_event_named",
                "Serenade" in answer or "Pacific Northwest Ballet" in answer,
                "answer must name the earliest event (Pacific Northwest Ballet - Serenade)")
    check_answer_number(judge, answer, "earliest_getin", 106)
    check_answer_number(judge, answer, "earliest_listing_count", 1)''',
    state="ro",
)

# ---------------------------------------------------------------- T19
SPECS[19] = dict(
    ques=QUES[19],
    nav=nav(
        ("visited_register", r"/secure/register"),
        ("visited_gift_cards", r"/gift-cards"),
        ("visited_kraken_page", r"/seattle-kraken-tickets/performer/900000460"),
        ("visited_favorites", r"/favorites"),
    ),
    checks='''
    check_answer_regex(judge, answer, "gift_code_format", r"\\bSH[A-Z0-9]{10}\\b",
                       "a SH+10-char gift card code")
    check_answer_number(judge, answer, "gift_amount", 50)
    check_answer_phrase(judge, answer, "design", "sports")
    judge.check("kraken_in_favorites",
                "kraken" in answer.casefold() and ("favorites" in answer.casefold()),
                "answer must confirm the Kraken appear in favorites")
    check_answer_number(judge, answer, "kraken_home_games", 41)
    check_answer_phrase(judge, answer, "next_opponent", "Calgary Flames")''',
    state="st",
    allowed='("users", "gift_card_orders", "favorites", "performers")',
    delta='''added_u, _, _ = table_diff(initial_db, after_db, "users")
    judge.check("new_user_created", len(added_u) == 1, f"exactly one new user: {list(added_u)}")
    new_uid = next(iter(added_u))[0] if added_u else None
    added_g, _, _ = table_diff(initial_db, after_db, "gift_card_orders")
    judge.check("gift_card_created", len(added_g) == 1, f"exactly one new gift card: {list(added_g)}")
    for key, row in added_g.items():
        judge.check("gift_card_row_exact",
                   row["user_id"] == new_uid and row["amount"] == 50
                   and row["design"] == "sports"
                   and re.fullmatch(r"SH[A-Z0-9]{10}", row["code"] or ""),
                   f"new gift card must be the $50 sports card for the new user: {dict(row)}")
    added_f, _, _ = table_diff(initial_db, after_db, "favorites")
    judge.check("kraken_favorite_created", len(added_f) == 1
                and next(iter(added_f.values()))["performer_id"] == 524
                and next(iter(added_f.values()))["user_id"] == new_uid,
                f"the new user must favorite the Kraken (performer 524): {list(added_f)}")
    _, _, changed_p = table_diff(initial_db, after_db, "performers")
    judge.check("kraken_follower_bump",
                (524,) in changed_p
                and changed_p[(524,)][1]["followers"] == changed_p[(524,)][0]["followers"] + 1,
                "the Kraken's follower count must increase by exactly one")''',
    extra_import="import re\nfrom verify_lib import table_diff\n",
)

# ---------------------------------------------------------------- T20
SPECS[20] = dict(
    ques=QUES[20],
    nav=nav(
        ("visited_kraken", r"/seattle-kraken-tickets/performer/900000460"),
        ("visited_seahawks", r"/seattle-seahawks-tickets/performer/1945"),
        ("visited_sounders", r"/seattle-sounders-fc-tickets/performer/388488"),
    ),
    checks='''
    check_answer_number(judge, answer, "kraken_followers", "44,200")
    check_answer_number(judge, answer, "kraken_home_events", 41)
    check_answer_number(judge, answer, "seahawks_followers", "62,800")
    check_answer_number(judge, answer, "seahawks_home_events", 8)
    check_answer_number(judge, answer, "sounders_followers", "56,600")
    check_answer_number(judge, answer, "sounders_home_events", 5)
    check_answer_phrase(judge, answer, "kraken_next", "Calgary Flames")
    check_answer_number(judge, answer, "kraken_next_getin", 65)
    check_answer_phrase(judge, answer, "seahawks_next", "Los Angeles Chargers")
    check_answer_number(judge, answer, "seahawks_next_getin", 236)
    check_answer_phrase(judge, answer, "sounders_next", "Minnesota United")
    check_answer_number(judge, answer, "sounders_next_getin", 18)
    judge.check("most_home_events_verdict",
                "kraken" in answer.casefold() and "most" in answer.casefold(),
                "answer must state the Kraken have the most home events")
    judge.check("largest_followers_verdict",
                "seahawks" in answer.casefold() and ("largest" in answer.casefold()
                                                      or "most" in answer.casefold()),
                "answer must state the Seahawks have the largest follower count")''',
    state="ro",
)


def main():
    for n, spec in SPECS.items():
        body = HEADER.format(n=n, ques=spec["ques"])
        body += spec.get("extra_import", "")
        if spec["state"] == "ro":
            body += FOOTER_RO.format(nav=spec["nav"], checks=spec["checks"])
        else:
            body += FOOTER_ST.format(nav=spec["nav"], checks=spec["checks"],
                                     delta=spec["delta"], allowed=spec["allowed"])
        (OUT / f"verify_{n}.py").write_text(body)
        print(f"wrote verify_{n}.py ({len(body)} bytes)")


if __name__ == "__main__":
    main()
