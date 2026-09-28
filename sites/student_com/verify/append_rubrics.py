#!/usr/bin/env python3
"""append_rubrics.py — append verifier_path + judge_rubric to tasks.jsonl.

The contributor's 5-key rows (web_name, id, ques, web, upstream_url) are
preserved byte-for-byte as the JSON prefix; the reviewer appends exactly two
keys (verifier_path, judge_rubric). There is no answer key: ground truth lives
only in the verifiers. Rubrics are English fact-checkpoint rules for the LLM
judge (the deterministic verifier is the primary grader).
"""
import json
from pathlib import Path

TASKS = Path(__file__).resolve().parents[1] / "tasks.jsonl"

RUBRICS = {
0: "Verify the agent opened the Georgia Tech homes page, applied the Student Community type filter with a $1,200 max price, and opened the matching property's page. The answer must name The Rive Atlanta, state its distance from campus (0.7 miles), list two amenities it actually offers (e.g. Gym, Swimming Pool, Cinema Room, Rooftop Terrace), and confirm the property was saved to alice.j@test.com's saved properties. Fail answers naming a different property, a fabricated distance, or amenities the page does not list.",
1: "Verify the agent opened the budget calculator and entered the stated finances (income $1,500 financial aid + $600 part-time job, nothing else; expenses $350 tuition, $90 utilities, $70 phone and internet, $280 groceries, $100 transport, $120 fun and subscriptions). The answer must report the safety buffer of $420 and the comfortable monthly rent target of $670. Fail answers with any other buffer or target numbers.",
2: "Verify the agent opened the UT Austin homes page, identified the cheapest dorm-style property, signed in as bob.c@test.com, and submitted an inquiry through the property's contact form. The answer must name Littlefield Hall, report the inquiry reference INQ-000005, and the exact address 2503 Whitis Ave, Austin, TX 78705, USA. Fail answers naming a different dorm, a different reference, or a different address.",
3: "Verify the agent opened both the Georgia Tech and Georgia State University homes pages in their default distance ordering and opened the most expensive of the four closest homes. The answer must report International House (I-House) from $950/mo and Eighth Street Apartments from $1,411/mo for Georgia Tech, Piedmont Pad Apartments from $500/mo and Freeman Ford Lofts from $1,850/mo for Georgia State, and Freeman Ford Lofts' Google rating 4.7 with 36 reviews. Fail answers that swap the pairs or invent numbers.",
4: "Verify the agent signed in as carol.d@test.com, opened her Recently Viewed Properties page, and opened the matching property. The answer must name Eighth Street Apartments, report its price $1,411 and its 36 Google reviews. Fail answers naming University House Midtown or Linea Midtown.",
5: "Verify the agent opened the Gainesville internships page. The answer must report 5 jobs in total, the newest posting 'Medical Assistant - Post-Acute & SNF (Temporary)' by Theoriamedical, and that 1 job is tagged Part-Time. Fail answers with any other counts or companies.",
6: "Verify the agent opened the Austin city page. The answer must report that the FAQ says a non-US citizen needs an F-1 visa from a US embassy or consulate, that rentals typically range $1,000-$1,600 per month, that Student.com lists 30 properties in Austin, and that The University of Texas at Austin is the popular college shown. Fail answers with a different visa type, range, count or college.",
7: "Verify the agent signed in as david.k@test.com, opened his saved properties, removed the Atlanta property, and added the only 5.0-rated property near The Ohio State University under $600. The answer must report 3 saved properties at the end and name the added property Kenny Road Apartments. Fail answers with a different count or property.",
8: "Verify the agent used the AI Search on the University of Central Florida homes page with an apartment / max $800 description, and opened the cheapest apartment in the filtered results. The answer must report 5 results after the filters, and the cheapest apartment Hub On Campus Orlando with rating 4.0 and address 11012 Hub Plz, Orlando, FL 32826, USA. Fail answers with a different count, property, rating or address.",
9: "Verify the agent opened the Case Western Reserve University homes page, switched to the map view, and opened the property closest to the campus marker. The answer must name Parkside Dwellings, from $1,360/month, rated 4.3, at 2040 Stearns Rd, Cleveland, OH 44106, USA. Fail answers naming University East Apartments or Commodore Place.",
10: "Verify the agent used the Texas college finder to locate the university students call 'TAMU' (Texas A&M University), opened its homes page, and opened the most expensive property within one mile. The answer must name 100 Park, from $1,539/month, about 0.3 miles from campus, and confirm it lists a Gym among its amenities. Fail answers naming Hullabaloo Hall or Schuhmacher Hall.",
11: "Verify the agent signed in as alice.j@test.com and opened the Villas on Rio property page. The answer must report the exact validation errors 'Invalid email address' (for alice(at)test.com) and 'Phone number is required' (for the empty phone), and the corrected inquiry's reference INQ-000005. Fail answers with paraphrased error text or a different reference.",
12: "Verify the agent searched for 'Seminoles', identified the university, and opened the cheapest property near its campus. The answer must report Florida State University in Tallahassee, and Southgate Campus Centre — from $455/month, rated 4.3, about 0.3 miles from campus. Fail answers naming Saga Tallahassee or Campus Row.",
13: "Verify the agent opened the Avoid Scams and Fraud guide. The answer must name the two matching red flags 'Off-Platform Payments' (wire transfers) and \"The 'Ghost' Landlord\" ('currently away on vacation'), and the first three emergency-protocol steps: Report anything suspicious (call +44 800 316 2918 or email contact@student.com), Trace the Paperwork, External Authorities (IC3 or FTC). Fail answers naming other red flags or steps.",
14: "Verify the agent registered the Mia Torres account (mia.torres@test.com), opened the University of Georgia homes page, saved the most expensive 5.0-rated property, and sent it an inquiry. The answer must name The Butler and report the inquiry reference INQ-000005. Fail answers naming University Village - Building C or a different reference.",
15: "Verify the agent opened both the Moontower and Villas on Rio property pages. The answer must report Moontower's price range $700-$6,475 per month, 10 gallery photos, rating 3.5 with 178 reviews, Villas on Rio's from-price $989 and rating 4.3, and conclude Moontower is cheaper to start with. Fail answers that swap the two properties or invent numbers.",
16: "Verify the agent opened the University of South Florida homes page with the Student Community type filter and the $900-$1,000 price range, sorted by price ascending, and opened the single result. The answer must report 1 matching result, The Retreat at Tampa at $940/month, its street address 11326 N 46th St, Tampa, FL 33617, USA, and the neighbourhood vibe labels Coffee & food, Music & nightlife, Artsy & cultural. NOTE: the property page currently returns HTTP 500 (site defect found in review) — the address and vibe labels are unobtainable until fixed; a run cannot honestly pass this rubric before the fix.",
17: "Verify the agent browsed three different Texas Tech University properties anonymously, opened the Recently Viewed dropdown, and then signed in as carol.d@test.com and opened her Recently Viewed Properties page. The answer must list the three browsed property names (Stangel Hall, Murray Hall, Murdough Hall in the dropdown) and state that all three also appear on carol's Recently Viewed Properties page. Fail answers claiming they do not carry over.",
18: "Verify the agent opened the Catalyst property page and the budget calculator. The answer must report Catalyst's contact details (email catalystmidtown@crm-living.com, phone (855) 677-3286, website catalystmidtown.com), the calculator's $660 rent target for $2,300 income / $1,180 expenses, and conclude the student could not comfortably afford Catalyst's cheapest room at $1,099/month. NOTE: the mirror never renders the contact email anywhere (site defect found in review) — the email is unobtainable until fixed; a run cannot honestly pass this rubric before the fix.",
19: "Verify the agent signed in as alice.j@test.com and opened her My Inquiries and Saved Properties pages. The answer must report the older inquiry INQ-000001, sent to Moontower on September 20, 2026, with her message asking about a studio with a private bathroom for the fall semester, and that she has 3 saved properties in total. Fail answers reporting the newer inquiry INQ-000002 or a different count.",
20: "Verify the agent opened the University of South Florida homes page with the Student Community type filter and the $900-$1,000 price range, opened the single suburban result, and saved it while signed in as bob.c@test.com. The answer must name The Retreat at Tampa at $940/month, rated 4.0, with 'Key things to know' labels Quiet area, Suburban, Good shopping & grocery, and confirm the save. NOTE: the property page currently returns HTTP 500 (site defect found in review) — the labels are unobtainable and the save button is unreachable until fixed; a run cannot honestly pass this rubric before the fix.",
}


def main():
    rows = [json.loads(l) for l in TASKS.read_text().splitlines() if l.strip()]
    out = []
    for row in rows:
        n = int(row["id"].split("--")[1])
        new = {"web_name": row["web_name"], "id": row["id"], "ques": row["ques"],
               "web": row["web"], "upstream_url": row["upstream_url"],
               "verifier_path": f"sites/student_com/verify/verify_{n}.py",
               "judge_rubric": RUBRICS[n]}
        out.append(json.dumps(new, ensure_ascii=False))
    TASKS.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"appended verifier_path + judge_rubric to {len(out)} rows")


if __name__ == "__main__":
    main()
