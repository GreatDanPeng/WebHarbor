#!/usr/bin/env python3
"""Emit sites/spothero/tasks.jsonl (contributor keys only, no answers)."""
import json

TASKS = [
    # 0 — guest hourly booking with filter + sort + facility cross-check
    "I'm spending Saturday afternoon, October 3rd, at Millennium Park in Chicago (12:00 PM to 6:00 PM) and want covered parking nearby. Find parking for that window, keep only covered garages, and sort by price. Open the cheapest one's facility page to check its height restriction and how drivers rate it, then book it as a guest with the email saturday.market@example.com. Report the facility, its star rating, the height restriction, the total, and the reservation code.",
    # 1 — monthly parking: featured rate + compare (two facility pages) + book
    "I'm starting a new job in downtown Chicago and want monthly parking beginning October 1st. Check the monthly parking page's Chicago section and report the cheapest featured monthly rate, then search monthly parking in downtown Chicago, open the two cheapest options' facility pages to compare their access hours, and book the cheaper of the two as a guest with the email new.commuter@example.com. Report the featured rate, the facility you booked, its monthly rate, its access hours, and the reservation code.",
    # 2 — two-event window compare + book + walking-time check
    "I have tickets to Tyler Childers - Snipe Hunt on October 2nd and JUNGLE - World Tour 2026 on October 3rd, both at Climate Pledge Arena in Seattle, but only need parking for one night. Find event parking for each show and report both parking windows SpotHero sets. Tell me which show's parking window starts earlier, then book that show's cheapest option as a guest with the email show.night@example.com. Report the show, the garage, its walking time from the arena, and the total.",
    # 3 — cross-airport compare (ORD vs MDW) + book + getting-there
    "I'm flying out of Chicago in early October and can use either airport. For a noon October 3rd to noon October 6th rental, compare the cheapest shuttle-served lot at O'Hare with the cheapest shuttle-served lot at Midway by per-day rate, then reserve the cheaper option as a guest with the email ord.flyer@example.com. Report the airport, the facility, the total, and the first step of its getting-there directions.",
    # 4 — disambiguation via both detail pages + extend + cancel + card
    "Log in as Alice Johnson (email: alice.j@test.com, password: TestPass123!). She has two upcoming reservations and can't remember which one ends sooner — open each reservation's page to compare their end times. Extend the sooner-ending one by two hours, then cancel the other reservation and quote the refund message. Finally report which card on file the extension charge would go to.",
    # 5 — cancel + rebook (david)
    "Sign in as David Kim (email: david.k@test.com, password: TestPass123!). His plans changed: cancel his upcoming airport reservation and quote the refund message the site shows, then book the cheapest shuttle-served O'Hare lot for October 10th noon through October 14th noon and report the new reservation's total.",
    # 6 — promo code discovery + apply
    "I heard SpotHero gives first-time customers a discount. Find the promo code advertised on the site for new customers, then use it to book four hours of parking near Fenway Park in Boston on October 3rd starting at 4:00 PM as a guest with the email first.timer@example.com. Report the code, the discount it took off, and the final total you paid.",
    # 7 — tall vehicle + height restriction + book
    "I drive a cargo van that is 6 feet 9 inches tall. I need covered parking near Times Square in New York for October 3rd from 7:00 PM to midnight. Find the cheapest covered garage whose height restriction actually fits my van, book it as a guest with the email van.driver@example.com, and report the garage, its height restriction, and the total.",
    # 8 — two-facility comparison + book better-reviewed
    "I need to park near Millennium Park in Chicago on October 3rd from noon to 6:00 PM. Compare the garages at 225 N Michigan Ave. and 318 S Federal Street: check each facility's star rating and what drivers like most about it, then book the better-reviewed one as a guest with the email jury.duty@example.com and report the facility and the total.",
    # 9 — policy research + booking
    "Before I trust SpotHero with my team's parking, quote from the FAQ: (1) the cancellation policy and (2) when your card is charged for a reservation. Then find what the parking guarantee promises if a spot isn't available, and finally book the cheapest spot near Union Square in San Francisco for October 3rd, 9:00 AM to 5:00 PM as policy.check@example.com.",
    # 10 — city facts + loop booking + facility height check
    "I'm visiting Chicago for a Saturday game on October 3rd. From the Chicago parking page, report the price ranges shown for commuter and weekend parking. Then find covered parking near the Loop for October 3rd from 5:00 PM to 11:00 PM, sort by price, open the cheapest garage's facility page to check its height restriction, and book it as a guest with the email weekend.fan@example.com. Report the ranges, the garage, its height restriction, and the total.",
    # 11 — Wrigley destination search + featured spot + height + Getting There
    "I'm driving my SUV to the Cubs game at Wrigley Field on October 5th from 5:00 PM to 11:00 PM. From the Wrigley Field destination page, search for parking over that window and sort by price. Find the spot the destination page features first in its nearby list, open its facility page to check whether a height restriction applies to an SUV and quote its first Getting There instruction, then book it as a guest with the email cubs.fan@example.com. Report the height finding, the instruction, and the total.",
    # 12 — stadium directory counts + Soldier Field + in-and-out check
    "From the Stadium Parking page, report how many NFL stadiums and how many NHL arenas are listed. Then find parking near Soldier Field in Chicago for October 4th from noon to 6:00 PM: sort the options by price, open the cheapest lot's facility page to check whether it allows in-and-out privileges, and reserve it as a guest with the email bears.tailgate@example.com. Report the counts, the facility, the in-and-out finding, and the total.",
    # 13 — payment methods CRUD + which reservations charge (carol)
    "Sign in as Carol Davis (email: carol.d@test.com, password: TestPass123!). Add a Visa card ending in 4242 that expires in September 2029 with the label 'Cubs Season', make it the default payment method, and remove the Mastercard ending in 6742 from the account. Then report which of her upcoming reservations would be charged to the new default card and what other card remains on file.",
    # 14 — profile update + persistence verification + payment + history (bob)
    "Sign in as Bob Chen (email: bob.c@test.com, password: TestPass123!). I bought a new car — update the license plate on the profile to WI-BO1180 and the vehicle to Honda CR-V Hybrid, save, then log out and log back in to confirm the plate persisted. Finally report the brand and last four digits of the default payment method and how many past reservations the account shows.",
    # 15 — favorites: two saves (one via search) + prune expensive (alice)
    "Log in as Alice Johnson (email: alice.j@test.com, password: TestPass123!). Save the Millennium Park Garage on 6 S Columbus Dr. to her saved spots from its facility page. Then find the cheapest covered garage near Union Square in San Francisco for October 3rd, 9:00 AM to 5:00 PM, open its facility page, and save that one too. Finally go to the saved spots list and remove every spot whose starting price is above $20. Report which spots remain and their prices.",
    # 16 — airport FAQ (3 quotes) + covered cheapest + getting-there + pass type
    "I'm parking at Chicago O'Hare for four days starting October 3rd at noon. From the O'Hare page's FAQs, quote what the site says about (1) when you pay for airport parking, (2) accessible parking, and (3) long-term economy parking. Then find the cheapest covered shuttle-served lot for that window, open its page to quote the first getting-there instruction, and reserve it as a guest with the email ord.trip@example.com. Report the total and the parking pass type.",
    # 17 — signup + book
    "Create a new SpotHero account with the first name Jordan, last name Reyes, email jordan.reyes@example.com, and password BookSpot2026!. Then book the cheapest parking near the United Center in Chicago for October 3rd from 5:00 PM to 11:00 PM, and report the reservation code and the total.",
    # 18 — two-city comparison + book cheaper
    "I can see a concert near Fenway Park in Boston or a show near Times Square in New York on October 3rd from 7:00 PM to midnight. Compare the cheapest covered parking near each venue for that window, tell me which city is cheaper and by how much, then book the cheaper option as a guest with the email city.hopper@example.com and report the facility and total.",
    # 19 — Denver monthly compare (facility pages) + book with Nov 1 start
    "My Denver office needs monthly parking for two employees starting November 1st. Find the monthly parking options in Denver, compare the two cheapest by monthly rate and access hours (check each facility page), then reserve the cheaper one as a guest with the email denver.office@example.com and report its monthly rate and the access hours you found.",
    # 20 — destination events table + covered+in-out filter + height + fees + book
    "I'm going to the Seattle Kraken vs. Calgary Flames game at Climate Pledge Arena on October 4th. From the arena's destination page, find that game in the upcoming events list and open its parking search — report the parking window SpotHero sets. Keep only covered garages that allow in-and-out, sort by price, open the cheapest one's facility page to check its height restriction and quote its first Getting There instruction, switch the results to totals with fees, then book it as a guest with the email kraken.fan@example.com. Report the garage, its height restriction, and the total with fees.",
]

rows = []
for i, ques in enumerate(TASKS):
    assert len(ques.split()) <= 100, f"task {i} too long"
    rows.append({
        "web_name": "SpotHero",
        "id": f"SpotHero--{i}",
        "ques": ques,
        "web": "http://localhost:40140/",
        "upstream_url": "https://spothero.com/",
    })

with open('tasks.jsonl', 'w') as f:
    for row in rows:
        f.write(json.dumps(row) + '\n')
print(f"wrote {len(rows)} tasks")
for i, ques in enumerate(TASKS):
    print(f"  {i:2d}: {len(ques.split()):3d} words")
