#!/usr/bin/env python3
"""append_rubrics.py — add `verifier_path` + `judge_rubric` to ../tasks.jsonl.

Reviewer contract step (review-env skill): every task gets a deterministic
verifier path and a pure-rule English judge rubric. The five contributor keys
(web_name, id, ques, web, upstream_url) stay byte-identical — each output row
is the original line with the two new keys appended — and no `answer` key is
ever written. Idempotent: re-running leaves an already-annotated file unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

TASKS = Path(__file__).resolve().parent.parent / "tasks.jsonl"

RUBRICS = {
    0: "FACT CHECKPOINTS: (1) The trajectory MUST open the Seattle Seahawks performer page "
       "(/seattle-seahawks-tickets/performer/1945) and all eight 2026 home-game event pages "
       "(/seattle-seahawks-seattle-tickets-10-4-2026/event/160436504, ...-10-11-2026/event/"
       "160436498, ...-10-25-2026/event/160436501, ...-11-2-2026/event/160436503, "
       "...-11-8-2026/event/160436506, ...-12-7-2026/event/160436508, ...-12-13-2026/event/"
       "160436500, ...-12-25-2026/event/160436502). (2) The final answer MUST report every "
       "game's opponent and date in schedule order together with its lowest ticket price "
       "(Los Angeles Chargers Oct 4 $236; San Francisco 49ers Oct 11 $367; Kansas City Chiefs "
       "Oct 25 $364; Chicago Bears Nov 2 $298; Arizona Cardinals Nov 8 $194; Dallas Cowboys "
       "Dec 7 $297; New York Giants Dec 13 $194; Los Angeles Rams Dec 25 $275), name the "
       "cheapest game overall (Arizona Cardinals, or the tied New York Giants, both $194) "
       "with its get-in section and row (Cardinals 344 Row EE / Giants 300 Row DD), and state "
       "the highest get-in price among the eight games ($367). (3) No DB rows may change "
       "(read-only task).",
    1: "FACT CHECKPOINTS: (1) The trajectory MUST open the October 4 Chargers at Seahawks "
       "event page with the 4-ticket / under-$400 / Clear-view filter combination applied and "
       "a separate 300 Level zone query for 4 tickets. (2) The final answer MUST report that "
       "5 listings match all three conditions, the cheapest match (Upper 300-Level, $265 per "
       "ticket), the cheapest 4-ticket 300 Level zone listing (307, Row II, $324 per ticket), "
       "and that the clear-view match is the cheaper option for four tickets ($1,060 vs "
       "$1,296). (3) No DB rows may change (read-only task).",
    2: "FACT CHECKPOINTS: (1) The trajectory MUST open the Metallica two-day-pass event "
       "(October 1 & 3), the October 1 single night and the October 3 single night event "
       "pages. (2) The final answer MUST report each event's total listing count (29 / 26 / "
       "10), get-in price ($1,137 / $749 / $1,124) and cheapest-listing section (310 / 407 / "
       "110), the pass's implied cost per night (~$568-569), the venue's full name and city "
       "(Sphere at The Venetian Resort, Las Vegas), and that the two-day pass ($1,137) is the "
       "cheaper way to see both shows versus the two single nights together ($1,873). "
       "(3) No DB rows may change (read-only task).",
    3: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as bob.c@test.com, open the "
       "November 8 Cardinals at Seahawks event, a matching listing, and walk the checkout "
       "pages (review, payment, confirm) to the confirmation page. (2) The final answer MUST "
       "report the order reference 41801303, the delivery fee $14.95, the processing fee "
       "$2.95 and the final total $405.90. (3) DB: exactly one new order row (user 2, event "
       "134, listing 225, quantity 2, UPS, $405.90, Confirmed), listing 225 marked sold, and "
       "one new notification for Bob; nothing else may change.",
    4: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as alice.j@test.com, use the sell "
       "flow for the November 2 Bears at Seahawks game, create the 220/row 14/seats 5-6 "
       "2-ticket listing, and reprice it from My Listings. (2) The final answer MUST report "
       "the new $180 price shown after the update, the game's displayed date (Nov 3 as shown) "
       "and venue (Lumen Field), that Alice has 2 listings for sale (the new 220 listing at "
       "$180 each and the seeded SECTION 212 listing at $89 each), and their combined asking "
       "value ($269 per-ticket sum / $716 total). (3) DB: exactly one new seller listing row "
       "(220, row 14, quantity 2, $180) and the event's listing_count update; nothing else "
       "may change.",
    5: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as carol.d@test.com, open the gift "
       "cards page before and after the purchase, and check the gift-card order list. (2) The "
       "final answer MUST report the offered amounts ($25/$50/$75/$100/$150/$200/$250/$500) "
       "and designs (classic, birthday, holiday, sports, concert), the purchased $150 holiday "
       "card for Danny (danny.gift@example.com), a SH+10-character gift card code (not a "
       "seeded fixture code), the confirmation message, that 2 gift cards now appear in "
       "Carol's history, and the earliest one ($100 classic, purchased Aug 23, 2026). "
       "(3) DB: exactly one new gift_card_orders row (user 3, $150, holiday, Danny); nothing "
       "else may change.",
    6: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as david.k@test.com, open "
       "Metallica's performer page and follow it, open a similar-artist page from the "
       "similar strip and follow that artist, open the December 13 Giants at Seahawks event "
       "page and favorite it, then open Favorites. (2) The final answer MUST report all "
       "three favorite entries (metallica, the similar artist — Olivia Rodrigo on the "
       "similar strip's first card — and the Giants game) and the total of 3 favorites. "
       "(3) DB: exactly three new favorite rows for david (performer 393, one other "
       "performer, event 129) and exactly +1 follower on each of the two favorited "
       "performers; nothing else may change.",
    7: "FACT CHECKPOINTS: (1) The trajectory MUST search 'metal' and 'seattle', query the "
       "search suggestion service for both terms, and open the Seattle Sounders FC and "
       "Seattle Mariners performer pages. (2) The final answer MUST report the 'metal' "
       "suggestion (metallica), the 'seattle' suggestions (seattle kraken, seattle mariners, "
       "seattle opera, seattle seahawks, seattle sounders fc, seattle symphony, seattle "
       "theatresports improv), the Sounders' 56,600 followers and 5 upcoming events with "
       "their next event (Minnesota United FC at Seattle Sounders FC, Sep 26, Lumen Field), "
       "the Mariners' 75,200 followers and 2 upcoming events with their next event (Los "
       "Angeles Angels at Seattle Mariners, T-Mobile Park), and that the Mariners have more "
       "upcoming events. (3) No DB rows may change (read-only task).",
    8: "FACT CHECKPOINTS: (1) The trajectory MUST open the Comedy subcategory "
       "(/comedy-tickets/category/209) and the three soonest Comedy event pages (The Rocky "
       "Horror Show, Little Shop of Horrors, Garry Starr — all Sep 26). (2) The final answer "
       "MUST list every Theater subcategory (Musicals, Plays, Comedy, Family, Classical and "
       "Opera, Dance / Ballet, Broadway), the three soonest Comedy events with performer, "
       "date and city, each event's get-in price (The Rocky Horror Show $104, Little Shop of "
       "Horrors $400, Garry Starr $162), total listing count (14 / 3 / 24) and venue name "
       "(Studio 54 / La Mirada Theatre / Studio Seaview), and name Garry Starr as the event "
       "with the most available listings. (3) No DB rows may change (read-only task).",
    9: "FACT CHECKPOINTS: (1) The trajectory MUST search Salome and open every Salome event "
       "page (Oct 17, Oct 23, Oct 25, Oct 28, Oct 31). (2) The final answer MUST report each "
       "performance's date and get-in price (Oct 17 $123; Oct 23 $120; Oct 25 $153; Oct 28 "
       "$89; Oct 31 $117), that the Oct 17 performance has more listings than Oct 23 (27 vs "
       "24), that the lower get-in belongs to Oct 23 ($120), the venue's full name and city "
       "(Marion Oliver McCaw Hall at Seattle Center - Complex, Seattle), and the cheapest "
       "listing section for each of the two earliest dates (ST 41 / ST 42). (3) No DB rows "
       "may change (read-only task).",
    10: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as alice.j@test.com and open the "
        "purchases (with at least one order detail), sales, listings and payments pages. "
        "(2) The final answer MUST report every purchase with event name, order date, "
        "delivery method, total and status (Metallica 2 Day Pass, order 41810907, placed Sep "
        "23 2026, Instant download, $2,572.95, Confirmed; Rush, order 41811044, placed Sep 5 "
        "2026, Mobile transfer, $1,106.95, Delivered), the largest total (the Metallica 2 Day "
        "Pass, $2,572.95), her completed sale (Seattle Opera - Salome, SECTION 212 Row 4, "
        "$118.40, Paid), her active listing (SECTION 212 Row 12, $89 each), and that she has "
        "2 payment cards on file. (3) No DB rows may change (read-only task).",
    11: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as alice.j@test.com and open the "
        "payments page before and after the card changes. (2) The final answer MUST report "
        "the cards on file before (Visa ••••4242 exp 08/2028 default; Mastercard ••••8321 "
        "exp 03/2027), the added Mastercard ••••4444 (exp 11/2029) as the new default, the "
        "removal of the older non-default Mastercard ••••8321, and the final card list "
        "(Visa ••••4242 non-default + Mastercard ••••4444 default). (3) DB: exactly one new "
        "payment_cards row (Mastercard 4444, Alice Johnson, default), one removed row "
        "(Mastercard 8321), and the Visa 4242 cleared from default; nothing else may change.",
    12: "FACT CHECKPOINTS: (1) The trajectory MUST register a new account, open the October "
        "11 49ers at Seahawks event, a single-ticket listing, walk the checkout to the "
        "confirmation page, and open the new account's purchase history. (2) The final "
        "answer MUST report the order reference 41801303, the final total $369.95, and "
        "confirm the order appears in the purchase history. (3) DB: exactly one new user row, "
        "one new order (41801303, the new user, event 128, listing 1189, quantity 1, "
        "instant, $369.95, Confirmed), listing 1189 marked sold, one new payment card for the "
        "new user, and one notification; nothing else may change.",
    13: "FACT CHECKPOINTS: (1) The trajectory MUST open the Seattle Kraken performer page "
        "(page 1 and the final schedule page). (2) The final answer MUST report the first "
        "home game (Calgary Flames, Oct 4, get-in $65), the last home game (Winnipeg Jets, "
        "Apr 3 2027, get-in $90), the next three home games after the opener (Vegas Golden "
        "Knights Oct 6; Detroit Red Wings Oct 20; Utah Mammoth Oct 22), the venue's full "
        "name and city (Climate Pledge Arena, Seattle, WA), and the total of 41 Kraken home "
        "games. (3) No DB rows may change (read-only task).",
    14: "FACT CHECKPOINTS: (1) The trajectory MUST open the October 11 49ers at Seahawks "
        "event page with the 100 Level, 200 Level and 300 Level zone filters applied. "
        "(2) The final answer MUST report the lowest-priced listing per zone with section "
        "and row (100 Level: 150, Row Z, $477; 200 Level: 215, Row L, $645; 300 Level: 302, "
        "Row EE, $367), that the 300 Level has the cheapest get-in, the price gap between "
        "the cheapest and most expensive zone ($278), and the event's 28 total listings. "
        "(3) No DB rows may change (read-only task).",
    15: "FACT CHECKPOINTS: (1) The trajectory MUST open the October 4 Chargers at Seahawks "
        "event page with the 4-ticket filter and the cheapest 4-ticket listing's detail "
        "page. (2) The final answer MUST report the listing's section (Upper 300-Level), "
        "row, seat features (4 tickets together, Clear view), zone, and that a seat view "
        "photo appears; the price breakdown at quantity 2 ($265 x 2 = $530 subtotal, "
        "$532.95 total) and at quantity 4 ($1,060 subtotal, $1,062.95 total) including the "
        "$2.95 processing fee; that the processing fee does not change with quantity; and "
        "the per-ticket totals ($266.48 at qty 2, $265.74 at qty 4). (3) No DB rows may "
        "change (read-only task).",
    16: "FACT CHECKPOINTS: (1) The trajectory MUST open the October 4 Chargers at Seahawks "
        "event page with the Best deal sort applied. (2) The final answer MUST report the "
        "three listings with the largest discounts with sections, current prices, original "
        "prices and computed savings (239: $449 from $659, saving $210 / 32%; CLB212: $485 "
        "from $687, saving $202 / 29%; 337: $244 from $409, saving $165 / 40%), name section "
        "239 as the biggest discount, and report the event's 30 total listings. (3) No DB "
        "rows may change (read-only task).",
    17: "FACT CHECKPOINTS: (1) The trajectory MUST open Metallica's October 1 Las Vegas "
        "single-night event page and every nearby event page shown in its nearby rail (the "
        "Oct 1 & 3 two-day pass, the Oct 3 single night, the Oct 8 & 10 two-day pass, the "
        "Oct 8 single night). (2) The final answer MUST report each nearby event's date and "
        "venue, its get-in price and total listing count (pass Oct 1 & 3: $1,137, 29; Oct 3 "
        "single: $1,124, 10; pass Oct 8 & 10: $1,092, 27; Oct 8 single: $725, 25), name the "
        "Oct 8 single night as the cheapest nearby get-in ($725), and compare the "
        "single-night get-in ($749) with the two-day pass ($1,137). (3) No DB rows may "
        "change (read-only task).",
    18: "FACT CHECKPOINTS: (1) The trajectory MUST open the explore page (page 1 and page "
        "2) and the earliest event's page. (2) The final answer MUST report the first three "
        "events on page 1 (Pacific Northwest Ballet - Serenade; Greenshield Industrial "
        "Supply Season End; Lovers Rock Reggae Live — all Sep 26), the first three events "
        "on page 2 (Gnash; Kamelot; Beth Stelling), the total number of events with tickets "
        "available (1,267), and the earliest event's get-in price ($106) and listing count "
        "(1). (3) No DB rows may change (read-only task).",
    19: "FACT CHECKPOINTS: (1) The trajectory MUST register a new account, open the gift "
        "cards page, buy the $50 sports-design gift card, open the Seattle Kraken performer "
        "page and follow the Kraken, then open Favorites. (2) The final answer MUST report "
        "a SH+10-character gift card code (not a seeded fixture code), the $50 sports "
        "design, that the Kraken appear in favorites, the 41 upcoming Kraken home games, "
        "and the next home game (Calgary Flames, Oct 4). (3) DB: exactly one new user row, "
        "one new gift_card_orders row ($50, sports, the new user), one new favorite row "
        "(the new user, performer 524), and exactly +1 on the Kraken's follower count; "
        "nothing else may change.",
    20: "FACT CHECKPOINTS: (1) The trajectory MUST open the Seattle Kraken, Seattle "
        "Seahawks and Seattle Sounders FC performer pages. (2) The final answer MUST "
        "report each team's follower count and number of upcoming home events (Kraken "
        "44,200 / 41; Seahawks 62,800 / 8; Sounders FC 56,600 / 5), each team's next home "
        "game with opponent, date and get-in price (Kraken: Calgary Flames, Oct 4, $65; "
        "Seahawks: Los Angeles Chargers, Oct 4, $236; Sounders FC: Minnesota United FC, "
        "Sep 26, $18), that the Kraken have the most home events, and that the Seahawks "
        "have the largest follower count. (3) No DB rows may change (read-only task).",
}


def main() -> None:
    lines = TASKS.read_text(encoding="utf-8").splitlines()
    out = []
    changed = 0
    for line in lines:
        row = json.loads(line)
        if "verifier_path" in row and "judge_rubric" in row:
            out.append(line)
            continue
        n = int(row["id"].split("--")[1])
        assert n in RUBRICS, f"missing rubric for task {n}"
        # byte-identical contributor prefix: original line + appended keys
        annotated = (line[:-1]
                    + ', "verifier_path": "sites/stubhub/verify/verify_' + str(n) + '.py"'
                    + ', "judge_rubric": ' + json.dumps(RUBRICS[n]) + "}")
        # sanity: still valid JSON, five keys untouched, no answer key
        parsed = json.loads(annotated)
        assert "answer" not in parsed
        for key in ("web_name", "id", "ques", "web", "upstream_url"):
            assert parsed[key] == row[key]
        out.append(annotated)
        changed += 1
    TASKS.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"annotated {changed} rows (idempotent re-runs leave them unchanged)")


if __name__ == "__main__":
    main()
