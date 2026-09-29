#!/usr/bin/env python3
"""append_rubrics.py — append verifier_path + judge_rubric to tasks.jsonl.

The original 5-key prefix of every row stays byte-identical (verified by
git diff after the rewrite); no answer key is ever added; rubrics are
English and purely rule-based (no ground-truth values leak into them).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks.jsonl"

RUBRICS = {
0: ("Log in to carol.d's DMV online account and open the license renewal flow. "
    "Report her license number, current expiration date, and REAL ID compliance status "
    "from the account page. Preview the standard eight-year renewal, add the one-time "
    "REAL ID, pay and submit it. Report the per-year license cost the renewal page "
    "quotes, the total charged, the receipt number, the new expiration date shown on "
    "the account page, and when the receipt says the new card arrives. PASS requires "
    "the license facts and all fee amounts exactly as rendered, a receipt number in "
    "the license-renewal format, the post-renewal account state (new expiration, REAL "
    "ID marked, one renewal transaction row) and nothing else written to the database. "
    "FAIL on any wrong number, a missing navigation step, or unexpected database writes."),
1: ("Log in to alice.j's DMV online account and open the registration renewal for her "
    "2019 Toyota Camry. Open BOTH the one-year and the two-year fee previews before "
    "paying. Report each preview total and every fee line the two-year preview lists "
    "with its amount. Select the two-year term, pay and submit, then report the "
    "receipt number and the new registration expiration date on the account page. "
    "PASS requires both preview totals, all two-year fee lines with amounts, a "
    "registration-renewal receipt number, the extended expiration, and exactly one "
    "renewal transaction row plus the vehicle's updated registration fields in the "
    "database. FAIL on any wrong amount, a skipped preview, or extra database writes."),
2: ("Log in to dana.k's DMV online account and preview the one-year online "
    "registration renewal for her 2017 Chevrolet Bolt EV. Report every fee line with "
    "its amount and the total, and her ID card's number and expiration date from the "
    "account page. Then open the registration page and report the electric-vehicle "
    "rule the environment provides (the registration page itself carries no EV rule "
    "text; the highway use fee page holds the fuel-efficient vehicle rule). PASS "
    "requires the ID card facts, the exact fee lines and total of the one-year "
    "preview, a navigation to one of the rule surfaces, and a read-only database. "
    "FAIL on wrong fee amounts, missing navigation, or any database write."),
3: ("Log in to alice.j's DMV online account. Browse specialized plates filtered to "
    "the College category, search within it for Virginia Tech, and open the Go "
    "Hokies design. Report the plate's annual fee, whether it supports personalization, "
    "and the plate type codes listed. Buy it for her Toyota RAV4 with the personalization "
    "HOKIE4 and report the personalized plate fee, the revenue-sharing transfer amount "
    "and threshold, the total charged, and the receipt number. PASS requires the plate "
    "facts exactly as rendered on the plate page, the personalized-plate availability "
    "check for HOKIE4, the purchase receipt, and exactly one plate-purchase transaction "
    "row plus the plate assignment to the RAV4 in the database. FAIL on wrong fees, "
    "a purchase assigned to the wrong vehicle, or extra database writes."),
4: ("Log in to alice.j's DMV online account. Open the 173rd Airborne plate page and "
    "report its annual fee and period, how many characters it allows, the documentation "
    "its requirements section asks for, and whether the disabled symbol is available. "
    "Then start a purchase for her Camry and check the availability of the messages "
    "AIRBORNE and HOOAH, reporting each check's outcome as the page renders it. PASS "
    "requires the plate facts exactly as listed, navigation into the purchase flow, "
    "both availability checks reported as the mirror shows them (the six-character "
    "limit truncates longer messages), and a read-only database. FAIL on wrong plate "
    "facts, missing purchase-flow navigation, or any database write."),
5: ("Use the DMV location finder to research the Alexandria customer service center "
    "and its alternatives. Report Alexandria's street address, telephone number, fax "
    "number, its weekday and Saturday hours, whether motorcycle skills testing and "
    "in-car road skills testing are available there, one nearby alternative office "
    "the page names with its address, and how many DMV Select offices the finder "
    "lists in total. PASS requires every value exactly as shown on the Alexandria "
    "office page and the DMV Select filter, navigation to both surfaces, and a "
    "read-only database. FAIL on any wrong value, a missing navigation, or any "
    "database write."),
6: ("Log in to bob.c's DMV online account and reserve an appointment for a Driver's "
    "License Renewal at the Richmond Central office on 2026-10-08 at any morning time "
    "under his account details. Report the office's address as the booking step shows "
    "it, the confirmation number, the booked time, and the email the confirmation "
    "lists. Then cancel the appointment through the view/cancel page and report the "
    "cancel confirmation text. PASS requires the booking through the reservation "
    "wizard (office, service, date, morning time), the confirmation number in the "
    "appointment format, the lookup and cancel steps, and exactly one appointment "
    "row in the database carrying the Canceled status. FAIL on wrong booking details, "
    "a skipped cancel step, or extra database writes."),
7: ("Without logging in, look up the appointment reserved under alice.j@test.com "
    "using confirmation number VADM9620114A on the View/Cancel page. Report the "
    "service type, the office, the date, the time, and the status. Then open that "
    "office's location page and report its street address, telephone number, the "
    "weekday and Saturday hours, and one service it does not offer. PASS requires "
    "every appointment fact exactly as the lookup shows, the office page facts "
    "exactly as rendered, navigation to both surfaces, and a read-only database. "
    "FAIL on any wrong value, a missing navigation, or any database write."),
8: ("Study for the knowledge exam: from the driver's manual read the Traffic Signals "
    "subsection and report what the manual says to do at a red light and at a flashing "
    "yellow signal. Then take the graded practice exam for the Signals, Signs and "
    "Pavement Markings section, answering every question. Report the number of "
    "questions, your score, the percentage, whether you passed, and the feedback text "
    "shown for one question. PASS requires the two signal rules as the manual states "
    "them, a submitted graded exam (all questions answered), a score of the form N/10 "
    "whose percentage equals ten times the score and whose passed flag matches the "
    "80 percent standard, one real feedback fragment, and a read-only database. FAIL "
    "on inconsistent score reporting, missing exam navigation, or any database write."),
9: ("Using the driver's manual and the DMV exam and permits pages, report: when a "
    "person under 18 who failed the knowledge exam can retake it and the worked "
    "example given, how often the exam may be taken, the passing rule for the ten "
    "sign questions, the passing rule for part two, and whether an audio version is "
    "offered; which out-of-country licenses are exempt from the knowledge exam; the "
    "vision standard for an unrestricted license; the restriction code added if you "
    "need glasses; and the minimum learner's permit holding period stated on the "
    "permits pages. PASS requires each rule exactly as the manual, exam and permits "
    "pages state it, navigation to those surfaces, and a read-only database. FAIL on "
    "any wrong rule, a missing navigation, or any database write."),
10: ("From the DMV taxes and fees page, report the annual registration fee for a "
     "passenger car of 4,000 lbs or less, a motorcycle, and a pickup truck of 6,501 "
     "to 10,000 lbs; the extra yearly fee for vehicles garaged in an emissions "
     "locality; the late fee; and the replacement title cost. Also report the driver's "
     "license per-year cost, the vehicle sales and use tax rate with its minimum, and "
     "the online multi-year renewal discounts the registration page advertises. Open "
     "the fee chart and report its form number. PASS requires every fee exactly as "
     "the fee page lists it, navigation to the fee page, and a read-only database. "
     "FAIL on any wrong amount, a missing navigation, or any database write."),
11: ("Find the DMV form a prospective purchaser uses to request vehicle information. "
     "Search the forms catalog and report the form number, its exact title, its "
     "category, what its description says, the language it is offered in, the total "
     "number of forms the catalog lists, and the total number of Spanish-language "
     "forms. Then report the fee the fee chart charges for a prospective purchaser "
     "inquiry, and the number and exact title of the form for road skills test "
     "translator/interpreter certification (no Spanish version exists in the "
     "catalog; the English form is the only real object). PASS requires the form "
     "facts and counts exactly as the catalog renders them, the PPI fee, navigation "
     "to the forms and fee surfaces, and a read-only database. FAIL on wrong counts, "
     "wrong form identifiers, or any database write."),
12: ("Log in to bob.c's DMV online account and change his mailing address to 4020 "
     "University Drive, Fairfax, VA 22030. Report the confirmation message shown, "
     "the updated address on the account page, and the receipt number the change "
     "adds to his transaction history. Also read the online address-change pages "
     "and report how long you have to notify DMV after moving and one other record "
     "the change updates besides the license. PASS requires the confirmation text, "
     "the new address persisted, an address-change receipt number, the 30-day "
     "notify rule, another affected record, and exactly the user address change "
     "plus one address-change transaction row in the database. FAIL on a wrong "
     "address, missing navigation, or extra database writes."),
13: ("Log in to alice.j's DMV online account and order a certified copy of her own "
     "driving record delivered online. Report the base price of the record, the "
     "extra certified-copy fee, the total charged, the receipt number, and how long "
     "the receipt says the online view stays available at no charge. Also report "
     "the title number and VIN of her RAV4 as the record-request page lists them. "
     "PASS requires the fee breakdown and total exactly as the order page renders "
     "them, a record-request receipt number, the RAV4 title and VIN, and exactly "
     "one record request row plus one record transaction row in the database. FAIL "
     "on wrong fees, wrong vehicle identifiers, or extra database writes."),
14: ("Log in to carol.d's DMV online account and order a replacement for her "
     "driver's license, selecting lost or stolen as the reason. Report the "
     "credential type and class the page shows on file, the license status shown "
     "on the account page, the other replacement reasons the page offers, the "
     "replacement fee, the total charged, the receipt number, and when the receipt "
     "says the card arrives. PASS requires the credential facts and status exactly "
     "as shown, the offered reasons, the fee and total, a replacement receipt "
     "number, and exactly one replacement transaction row in the database. FAIL on "
     "wrong values, missing navigation, or extra database writes."),
15: ("Using the DMV moving pages, report each ordered step the new-resident page "
     "lists, the deadline for getting a Virginia driver's license and for titling "
     "and registering your vehicle, the safety inspection rule, the emissions "
     "counties and cities, the local sticker or decal note, what a current CDL "
     "holder must do and within how many days, what the page says about "
     "maintaining insurance from the moment you register, and the voter "
     "registration note. PASS requires each deadline and rule exactly as the "
     "new-resident page states it, navigation to that page, and a read-only "
     "database. FAIL on any wrong deadline or rule, a missing navigation, or any "
     "database write."),
16: ("Using the DMV buying and selling pages, report the seller's required steps in "
     "order, what to do with your license plates, what the page says about notifying "
     "DMV of the sale (it states no number of days — report that absence), and the "
     "first three steps the page lists for a buyer. Then from the fee page report "
     "the registration transfer fee, the replacement registration card fee, the "
     "vehicle record fee online, and the original title fee the buyer pays. PASS "
     "requires the seller and buyer steps as the page lists them, each fee amount "
     "attached to its own fee label, navigation to both surfaces, and a read-only "
     "database. FAIL on swapped fee labels, wrong steps, or any database write."),
17: ("Using the DMV vehicle pages, report Virginia's minimum liability insurance "
     "requirements — the three coverage limits for policies effective on or after "
     "January 1, 2025 — and the 2022 through 2024 limits. Report how DMV "
     "electronically monitors insurance coverage, what you must do if your "
     "coverage cancels during the registration period, the uninsured-owner "
     "penalties including the statutory fee and SR-22 filing, the payment-plan "
     "option, and the registration page's note about for-hire vehicle limits. "
     "PASS requires the limit values exactly as the insurance page lists them, the "
     "monitoring and penalty rules, the for-hire note, navigation to the insurance "
     "and registration pages, and a read-only database. FAIL on wrong limits, "
     "missing navigation, or any database write."),
18: ("Using the DMV REAL ID page, report the one-time fee, the minimum total "
     "transaction, what a REAL ID looks like, how many steps the page lists to "
     "apply, the federal boarding rule, what happens when you move to a new state, "
     "and what the page says about secure facilities setting their own rules. Then "
     "from the newsroom report the total number of news items, the release date of "
     "the Apple Wallet announcement, one feature detail it announces, and the "
     "second news item's title. PASS requires the REAL ID facts exactly as the "
     "page states them, the newsroom count, the Apple Wallet date and the second "
     "item's title, navigation to both surfaces, and a read-only database. FAIL on "
     "wrong values, missing navigation, or any database write."),
19: ("Using the CDL pages and the fee page, report the HAZMAT background check and "
     "fingerprinting fee, the reduced TWIC-related fee and its qualifying "
     "condition, what the page says TWIC comparability means, the CDL cost per "
     "year with its minimum, the CDL skills test missed-appointment fee, the "
     "endorsement cost per year, and the commercial learner's permit fee. Also "
     "report two services the CDL section's menu lists besides applying. PASS "
     "requires every fee exactly as the fee page lists it, the TWIC rules as the "
     "HAZMAT page states them, two real CDL menu services, navigation to all three "
     "surfaces, and a read-only database. FAIL on wrong fees, missing navigation, "
     "or any database write."),
}

def main():
    rows = [json.loads(l) for l in TASKS.read_text().splitlines() if l.strip()]
    out_lines = []
    for i, row in enumerate(rows):
        assert "verifier_path" not in row and "judge_rubric" not in row
        assert "answer" not in row
        row["verifier_path"] = f"sites/virginia_dmv/verify/verify_{i}.py"
        row["judge_rubric"] = RUBRICS[i]
        # 5-key prefix order preserved: web_name, id, ques, web, upstream_url
        out_lines.append(json.dumps(row, ensure_ascii=False))
    TASKS.write_text("\n".join(out_lines) + "\n")
    print(f"appended verifier_path + judge_rubric to {len(rows)} rows")

if __name__ == "__main__":
    main()
