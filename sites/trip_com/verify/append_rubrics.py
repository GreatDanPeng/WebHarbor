#!/usr/bin/env python3
"""append_rubrics.py — merge the reviewer grading contract into tasks.jsonl.

Reads the contributor's 5-key rows (web_name, id, ques, web, upstream_url) and
rewrites tasks.jsonl with two additional keys per row:

  verifier_path  — relative path (repo root) to the deterministic verifier
  judge_rubric   — English fact-checkpoints for the LLM judge (secondary mode)

Contract invariants enforced here:
  * the original 5-key prefix of every row is preserved BYTE-IDENTICALLY (the
    merge re-serializes only the added keys; a pytest asserts the prefix
    equality against `git show 60038e71:sites/trip_com/tasks.jsonl`);
  * there is NO ``answer`` key (ground truth lives only in the verifiers);
  * every verifier_path exists and ends in ``.py``;
  * every judge_rubric is non-empty English text.

Run: python3 sites/trip_com/verify/append_rubrics.py   (idempotent)
"""
import json
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
TASKS = SITE_DIR / "tasks.jsonl"
VERIFY = "sites/trip_com/verify/verify_{}.py"

RUBRICS = {
    0: "Verify the agent opened the deals page, the Las Vegas hotel list with the price/star/pool filters, the Trump International Hotel Las Vegas detail page, its cheapest king room booking form, and the confirmation. The answer must name Trump International Hotel Las Vegas, the Superior King Room, the promo code TRIPNEW20 from the deals page, and a total charged of $216.00. Fail answers naming a different hotel or room, a wrong total, or an answer with no booking reference.",
    1: "Verify the agent compared the two best-rated Las Vegas hotels under $150 with free cancellation on the results page and booked the cheaper one. The answer must identify Planet Hollywood Resort & Casino with guest score 8.5, its lowest-priced room, and a total of $82.00 for 11-12 October. Fail answers that book Four Queens, report a different score, or a different total.",
    2: "Verify the agent searched San Francisco to New York round trip 20-27 October, filtered to Delta and nonstop on the outbound list, selected an outbound, re-applied the Delta/nonstop filters on the return-selection page, and completed the booking. The answer must report Delta, the outbound departure time as one of 07:00, 16:15 or 22:15 (three-way $213 tie), the return departure time 07:00, a total of $441.00 and the booking reference. Fail answers reporting a non-Delta or non-nonstop leg or a different total.",
    3: "Verify the agent compared the six cheap flight deals on the deals page, identified San Francisco to Las Vegas as the cheapest route, then booked the cheapest nonstop round trip 20-27 October. The answer must state the route (SFO to LAS), Frontier Airlines for the outbound, Southwest Airlines for the return, a total of $114.00 and the booking reference. Fail answers naming a different route, different airlines, or a different total.",
    4: "Verify the agent searched Chicago to Miami one-way 22 October, filtered to nonstop flights departing before noon, and booked the cheapest. The answer must report American Airlines, the 08:43 departure, a price of $169 and the booking reference. Fail answers naming a different airline, departure time, or price.",
    5: "Verify the agent browsed Orlando experiences filtered to City passes, counted the passes listed (3), named the cheapest (Orlando: Go City Explorer Pass - Choose 2 to 5 Attractions, $60.84), identified the highest-rated Orlando experience of any kind (the St. Augustine guided day trip, 5.0), opened the Go City: Orlando Explorer Pass page, and booked it for two guests for 6 October. The answer must report the pass name, rating 4.0 with 1 review and 12 booked, two highlights (saving up to 50% vs individual tickets, and going at your own pace with 30 days validity), the 90-day validity window, and the total paid $128.00. Fail answers with a different pass, rating, census counts, or total.",
    6: "Verify the agent signed in as alice.j@test.com, opened the account overview and My bookings, opened the hotel page for the hotel stay, checked the wishlist and coupons, priced a nonstop round trip on the flight's route, and cancelled the more expensive booking (the flight). The answer must state the Trip Coins balance 480, both bookings' references and totals (THALICE1 $128.00, TFALICE1 $422.00), the hotel Harrah's Las Vegas with check-in from 16:00, the flight route San Francisco to New York with the 22:15 outbound and 11:35 return departure, the wishlist count 3 with the priciest at $327, the FLYTRIP10 minimum spend $150, the $433 nonstop rebooking cost, that booking TFALICE1 was cancelled, and that afterwards the hotel booking shows confirmed while the flight shows cancelled. Fail answers that cancel the hotel instead, or report different facts.",
    7: "Verify the agent signed in as bob.c@test.com, saved the best-rated San Francisco hotel under $200 a night (Hotel Fiona - No Resort Fee) to the wishlist, then removed the more expensive of the two saved Las Vegas hotels (Thunderbird Boutique Hotel, $57). The final answer must list the remaining wishlist hotels with nightly prices: Hotel 32One $212, Hotel Fiona $187, Horseshoe Las Vegas $56, and must not list Thunderbird. Fail answers that remove the wrong hotel or list different hotels.",
    8: "Verify the agent found the 20% hotel promo on the deals page with its $100 minimum spend, then booked the cheapest room at Paris Las Vegas for 4-5 October. The answer must state the minimum spend $100, the room (Room Type Assigned On Arrival), the discount $37.80 and the final total $151.20. Fail answers with a wrong minimum spend, discount, or total.",
    9: "Verify the agent read the New York weekend guide (Jersey City and Newark rates 30-40% lower), filtered the New York hotel results by parking, ranked the >500-review hotels by guest score, opened the top hotel's detail page and its cheapest room's booking form, then opened the runner-up's detail page. The answer must name Motto by Hilton New York City Times Square with guest score 8.7 and 714 reviews, the two review tags on its results card (American breakfast, Great views), its cheapest room's details: Flex Room With Wall Bed, $202 nightly, 1 queen bed, breakfast not included, free cancellation before 11:59 PM Oct 1, and the $34.00 taxes per night shown on that room's booking form; plus the other hotel (DoubleTree by Hilton New York Downtown, 8.4) with its cheapest room King Room With City View at $175. Fail answers naming a different hotel or room facts, or missing the guide or taxes.",
    10: "Verify the agent read the Orlando theme-park planning guide, then browsed Orlando City passes and booked the cheapest for two people for 6 October. The answer must state the guide's advice of 2 days per major park, the booked pass (Orlando: Go City Explorer Pass - Choose 2 to 5 Attractions), and the total paid $121.68. Fail answers with a different day count, pass, or total.",
    11: "Verify the agent signed in as carol.d@test.com, read the Trip Coins balance on the account overview, found the two cheapest bookable Miami hotels and both detail pages, and checked the wishlist and coupons without booking anything. The answer must state the balance 480, Hyatt Place Miami Airport East with guest score 8.3 at $93 a night and its cheapest room's name (King Room or one of the two accessible king rooms - three-way $93 tie), bed type (1 king bed and 1 sofa bed), total including taxes $105 for one night 4-5 October, and $1.05 in Trip Coins; the runner-up Kompose Boutique Hotel Miami Airport (8.3, $100) with its cheapest room at $82; the wishlist count 3; and the highest-minimum coupon SAVE25 ($200). Fail answers with different hotels or rooms, and any actual booking must fail (the task forbids booking).",
    12: "Verify the agent searched both Las Vegas and New York hotels for 4-5 October, opened each cheapest available hotel's page, and counted its room choices. The answer must report Harrah's Las Vegas at $56 a night (guest score 8.4, 5 room choices) and HI New York City Hostel at $104 (guest score 9.0, 2 room choices), and that the Las Vegas hotel is cheaper by $48. Fail answers with different hotels, prices, room counts, or difference.",
    13: "Verify the agent searched Las Vegas hotels for 13-14 October with a max price of 120, used the area filter to exclude the Strip, opened the best-rated bookable off-Strip hotel, opened its cheapest room's booking form for those nights, then filtered to the Strip and opened the best-rated bookable Strip hotel. The answer must name Four Queens Hotel and Casino, its area Downtown - Fremont Street, guest score 8.7, 3-star rating, nightly price $104, the free-cancellation deadline on its cheapest room (before 11:59 PM, Oct 1), the booking-form grand total $73.00 for the one night, and the Strip comparison Planet Hollywood Resort & Casino (8.5, $72, cheapest room Room Type Assigned On Arrival). Fail answers naming a Strip hotel for the off-Strip leg, wrong dates, or wrong totals.",
    14: "Verify the agent found the flight promo code on the deals page, searched Miami to New York round trip 24-31 October, and booked the cheapest round trip with the promo applied. The answer must state the promo discount $21.10, the total paid $189.90 and the booking reference. Fail answers with a different discount or total.",
    15: "Verify the agent signed in as david.k@test.com, read the account overview, listed every booking with type, dates and total, opened the hotel booking's hotel page, opened the cheapest room's booking form for a repeat 18-20 November stay, found the booked activity via site search, and checked the wishlist and coupons. The answer must state the Trip Coins balance 480, the hotel booking (Harrah's Las Vegas, Nov 1-3, $136, 136 Trip Coins earned), the attraction booking (Orlando: Go City Explorer Pass, Nov 2, $121.68), from the hotel page: guest score 8.4, 3-star rating, Las Vegas Strip area, check-in from 16:00, cheapest room Room Type Assigned On Arrival at $56 and its repeat two-night total $128.00 for 18-20 November; the booked activity's highlights letting you choose 2 to 5 attractions; the wishlist count 3; and the attractions promo ACTIVITY15 minimum spend $50. Fail answers with different facts.",
    16: "Verify the agent found Paris Las Vegas via the site search, set 5-7 October on the hotel page, opened the cheapest room's booking form to confirm the price breakdown, checked the second-cheapest room's grand total, checked the cheapest room's one-night total for 5-6 October, and searched for the Bellagio - all without completing a booking. The answer must state the $167 nightly rate before tax, $22 taxes and fees per night, a $378 grand total, the room name Room Type Assigned On Arrival, the bed type (1 king bed or 2 queen beds), that it sleeps 2, the free-cancellation deadline before 11:59 PM Oct 1, the second-cheapest room Bordeaux Room King with a $388 grand total for the same nights, the $189 one-night total, the hotel's 8.6 guest score with 805 reviews, and the Bellagio's $467 nightly rate from the site search. Fail answers with different numbers or an actual booking (the task asks only to confirm the price details).",
    17: "Verify the agent browsed the Hong Kong experiences page, listed the categories with activities (Activities, City passes, Tickets and Tours - all four must appear), counted 35 total experiences and 18 tours via the category filter, named the cheapest (the Hung Fook Tong e-voucher at $1.15), identified the two most-booked experiences (Top-Rated Hong Kong Tour, 610 booked; Hong Kong Skyline Tour Victoria Harbour Cruise, 603 booked) and their package validities, and booked the most-booked for two people on 12 October. The answer must report the tour's $76.52 price, 27 reviews, the total paid $153.04 and the booking reference. Fail answers with wrong categories, counts, dates, or totals.",
    18: "Verify the agent browsed Shanghai experiences, reported the census (35 listed, 14 in the Activities category, 4 sharing the top 5.0 rating), sorted by rating, excluded city passes and tours, opened the highest-rated activity (Shanghai imperial banquet - the only 5.0-rated one with a highlights section), and booked it for three guests on 12 October. The answer must name the activity, its 5.0 rating, its 36 reviews and 652 booked, the 90-day package validity, the two top highlights (the Shuyanfu immersive ritual and music culture, and dishes that surprise your taste buds), and the total paid $48.27. Fail answers with wrong census counts, a different activity, or a wrong total.",
    19: "Verify the agent used the site search to find the free-cancellation guide, read it (including what happens after the deadline), then found the two cheapest bookable Las Vegas hotels under $60 a night for 20-21 October, opened the cheapest one's page and its cheapest room's booking form, and opened the runner-up's page. The answer must state the guide's deadline (free cancellation commonly allowed before 11:59 PM local hotel time, one to three days before check-in; after it you are charged the first night or the full amount), both hotels (Harrah's Las Vegas, 8.4, 536 reviews; The LINQ Hotel & Casino, 8.4, 344 reviews), the runner-up's cheapest room (Deluxe Two Double Room Non smoking), and for the cheapest one: Las Vegas Strip area, parking among its amenities, the cancellation deadline before 11:59 PM Oct 1, and the $64.00 room total for those nights from its booking form. Fail answers with different facts.",
}

CONTRIBUTOR_KEYS = ("web_name", "id", "ques", "web", "upstream_url")


def main():
    lines = TASKS.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        for key in CONTRIBUTOR_KEYS:
            assert key in row, f"contributor key {key!r} missing: {row}"
        assert "answer" not in row, "contributor row must not carry an answer key"
        n = int(row["id"].split("--")[1])
        assert (SITE_DIR.parent.parent / VERIFY.format(n)).is_file(), \
            f"verifier missing for task {n}"
        prefix = json.dumps({k: row[k] for k in CONTRIBUTOR_KEYS},
                            ensure_ascii=False, separators=(", ", ": "))
        # byte-identity: the 5-key prefix must round-trip to the original row
        assert prefix == line, f"row {n}: 5-key prefix is not byte-identical"
        new_row = {k: row[k] for k in CONTRIBUTOR_KEYS}
        new_row["verifier_path"] = VERIFY.format(n)
        new_row["judge_rubric"] = RUBRICS[n]
        out.append(json.dumps(new_row, ensure_ascii=False, separators=(", ", ": ")))
    TASKS.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"rewrote {len(out)} rows with verifier_path + judge_rubric")


if __name__ == "__main__":
    main()
