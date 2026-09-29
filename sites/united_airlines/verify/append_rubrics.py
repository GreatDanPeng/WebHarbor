#!/usr/bin/env python3
"""Append verifier_path + judge_rubric to sites/united_airlines/tasks.jsonl.

The original 5-key rows (web_name, id, ques, web, upstream_url) are preserved
byte-for-byte: this script only appends two new keys to each line's JSON
object and asserts that the reconstructed 5-key prefix is byte-identical to
`git show 93a2638f:sites/united_airlines/tasks.jsonl` (the r2 fix-round
contribution head) — i.e. the original bytes are untouched, no answer key is
added, and every rubric is pure English rules with no ground-truth values.
"""
import json
import subprocess
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]          # sites/united_airlines
REPO = SITE.parents[2]                              # WebHarbor root
CONTRIB_REF = "93a2638f:sites/united_airlines/tasks.jsonl"

RUBRICS = {}

RUBRICS[0] = (
    "FACT CHECKPOINTS: The agent must have searched flights from Chicago O'Hare (ORD) "
    "to Denver (DEN) for October 15, 2026 in United Economy and completed the guest "
    "booking chain through the passenger-details, payment and confirmation pages. "
    "The answer must list the United Economy (not Basic Economy) fare for every "
    "flight shown that day, name the cheapest Economy flight with its exact price, "
    "and report the confirmation number shown on the confirmation page and the total "
    "charged for the booking. An empty answer is a FAIL."
)
RUBRICS[1] = (
    "FACT CHECKPOINTS: The agent must have searched the round trip Hancock (CMX) to "
    "Chicago O'Hare departing October 14 and returning October 21, 2026 in United "
    "Economy, selecting the cheapest outbound and the cheapest return flight, and "
    "paid as guest with the specified Mastercard. The answer must name both selected "
    "flight numbers, report the confirmation number from the confirmation page and "
    "the total charged. An empty answer is a FAIL."
)
RUBRICS[2] = (
    "FACT CHECKPOINTS: The agent must have signed in with the given credentials, "
    "searched one-way San Francisco (SFO) to Chicago O'Hare for October 5, 2026 in "
    "United Economy, and completed an award booking redeeming miles for the fare "
    "through the payment page's miles option. The answer must report the confirmation "
    "number, the exact number of miles redeemed as shown by the site, and the award "
    "miles balance afterwards exactly as shown on the account page. An empty answer "
    "is a FAIL."
)
RUBRICS[3] = (
    "FACT CHECKPOINTS: The agent must have signed in with the given credentials, "
    "searched Washington-Dulles (IAD) to Denver for October 8, 2026 in Economy Plus, "
    "booked the cheapest Economy Plus flight with the traveler's MileagePlus number "
    "on the passenger, and paid with the specified Visa card. The answer must report "
    "the confirmation number, the total charged as shown on the confirmation page, "
    "and the award miles this booking credits to the account. An empty answer is a FAIL."
)
RUBRICS[4] = (
    "FACT CHECKPOINTS: The agent must have checked flight status by number for UA 2855 "
    "today, opened the route status page for San Francisco to Chicago O'Hare, and "
    "opened the operating aircraft's fleet page. The answer must report the scheduled "
    "departure and arrival times, the aircraft type, its Wi-Fi provider, and the "
    "number of United Polaris (First/Business) and Premium Plus rows on the aircraft, "
    "as shown on the fleet page. An empty answer is a FAIL."
)
RUBRICS[5] = (
    "FACT CHECKPOINTS: The agent must have searched Rome (FCO) to Denver for October "
    "19, 2026 and compared the fare table. The answer must report the Basic Economy, "
    "United Economy, Economy Plus, Premium Plus and United Business fares for every "
    "flight shown that day, and name which flight is cheapest in Premium Plus and "
    "which aircraft operates it. An empty answer is a FAIL."
)
RUBRICS[6] = (
    "FACT CHECKPOINTS: The agent must have looked up trip KX42LM in My trips, added "
    "the next checked bag for the traveler (the trip already includes one free bag), "
    "and picked a standard (non-Economy Plus) window or aisle seat on the seat map. "
    "The answer must report the fee charged for the added bag, the seat chosen, and "
    "how many free bags her Premier status gives her on this trip. An empty answer "
    "is a FAIL."
)
RUBRICS[7] = (
    "FACT CHECKPOINTS: The agent must have signed in with the given credentials, "
    "checked in for trip HD19RK from the check-in flow, confirmed seat 12A, and viewed "
    "the boarding pass. The answer must report the boarding group, the gate, the "
    "boarding time, the seat, and the aircraft flying the route. An empty answer is a "
    "FAIL."
)
RUBRICS[8] = (
    "FACT CHECKPOINTS: The agent must have signed in with the given credentials, opened "
    "trip QT83NB's details in My trips, used the change-flight flow, and completed the "
    "change to the latest United flight from O'Hare to Denver later today. The answer "
    "must compare the itinerary before and after the change: report the original and "
    "new flight numbers with their departure times, the fare difference charged "
    "(if any), and the change fee United applied. An empty answer is a FAIL."
)
RUBRICS[9] = (
    "FACT CHECKPOINTS: The agent must have booked the cheapest United Economy flight "
    "from Denver to Salt Lake City on October 16, 2026 for the given guest traveler "
    "with the specified Visa card, and then canceled the trip from My trips. The "
    "answer must report the confirmation number, the total paid, the refund amount, "
    "and where the refund went. An empty answer is a FAIL."
)
RUBRICS[10] = (
    "FACT CHECKPOINTS: The agent must have looked up trip ZW57PC in My trips, attempted "
    "the flight change, canceled the trip, and read the flight-change policy page. "
    "The answer must state whether Basic Economy tickets can be changed, what happened "
    "to the ticket value when the trip was canceled, and the exact refund/ticket-value "
    "amount. An empty answer is a FAIL."
)
RUBRICS[11] = (
    "FACT CHECKPOINTS: The agent must have used the checked bag fee calculator for both "
    "scenarios: (1) a Member in United Economy flying ORD to DEN with 2 bags, prepaid "
    "online versus paid at the airport, and (2) a Premier Gold member in United "
    "Business flying London Heathrow to DEN with 2 bags online. The answer must report "
    "the per-bag and total fees the calculator shows for each scenario, and each "
    "traveler's weight limit per bag. An empty answer is a FAIL."
)
RUBRICS[12] = (
    "FACT CHECKPOINTS: The agent must have researched the site's baggage pages. The "
    "answer must report the maximum size of a checked bag, the weight limit for United "
    "Economy versus Premier members, the fee for a 60-pound bag, the exact size limits "
    "for a carry-on and a personal item, and whether a Basic Economy domestic fare "
    "includes a full-size carry-on. The agent must also have run the checked bag fee "
    "calculator for three checked bags prepaid online for one United Economy traveler "
    "from Chicago O'Hare to Denver and report the per-bag fees and the total it shows. "
    "Every number must come from the site's pages. An empty answer is a FAIL."
)
RUBRICS[13] = (
    "FACT CHECKPOINTS: The agent must have joined MileagePlus as a new member with the "
    "given name, email and password, then booked the cheapest United Economy flight "
    "San Francisco to Portland on October 9, 2026 with the new MileagePlus number on "
    "the traveler, paying with the specified Visa card. The answer must report the "
    "MileagePlus number, the confirmation number, and the award miles the flight "
    "credits. An empty answer is a FAIL."
)
RUBRICS[14] = (
    "FACT CHECKPOINTS: The agent must have signed in with the given credentials, read "
    "her account page's Premier qualification progress, and opened the MileagePlus "
    "program page's qualification table. The answer must report her current PQF and "
    "PQP, the Premier Silver PQF and PQP thresholds as stated on both pages and "
    "whether the two pages agree, the PQP-only alternative, how many more PQF and PQP "
    "she still needs for Premier Silver, and how many award miles per dollar Premier "
    "1K members earn. An empty answer is a FAIL."
)
RUBRICS[15] = (
    "FACT CHECKPOINTS: The agent must have opened the cabin experience pages for Basic "
    "Economy, Economy Plus, Premium Plus and United Polaris, and the 787-9 fleet page. "
    "The answer must report (1) the two Basic Economy carry-on and change rules, (2) "
    "the Economy Plus price per flight and who gets it free, (3) the Premium Plus "
    "baggage allowance, and (4) the Polaris seat pitch from the 787-9 fleet page. An "
    "empty answer is a FAIL."
)
RUBRICS[16] = (
    "FACT CHECKPOINTS: The agent must have opened both the Boeing 787-9 and Boeing "
    "777-300ER fleet pages. The answer must report each aircraft's total seat rows, "
    "how many rows are United Polaris versus Premium Plus versus Economy Plus, each "
    "cabin's seat count from the interior specifications, the Wi-Fi provider, and the "
    "wing or engine facts listed. An empty answer is a FAIL."
)
RUBRICS[17] = (
    "FACT CHECKPOINTS: The agent must have answered all four questions using only the "
    "site's Help Center articles: (1) when online check-in opens and closes, (2) the "
    "same-day flight change fee and when standby is free, (3) the redeposit fee after "
    "canceling an award flight and the fee that applies on a no-show instead, and (4) "
    "the lowest Economy Plus price per flight. For each question, the answer must "
    "report the exact title of the Help Center article that provided it. An empty "
    "answer is a FAIL."
)
RUBRICS[18] = (
    "FACT CHECKPOINTS: The agent must have checked today's flight status by route from "
    "Newark (EWR) to Denver, opened the earliest-arrival aircraft's fleet page, and "
    "opened the Denver airport guide. The answer must report each of the three listed "
    "flights' departure and arrival times and aircraft, which one arrives earliest, "
    "its duration, its Wi-Fi provider from the fleet page, and whether Denver is a "
    "United hub. An empty answer is a FAIL."
)
RUBRICS[19] = (
    "FACT CHECKPOINTS: The agent must have found the San Francisco to Sydney deal on "
    "the deals page, opened it, checked the route's flight details, and booked the "
    "cheapest United Economy seat departing October 26, 2026 for the given guest "
    "traveler with the specified Visa card. The answer must report the confirmation "
    "number, the flight number, the deal's starting price, and the total charged. An "
    "empty answer is a FAIL."
)
RUBRICS[20] = (
    "FACT CHECKPOINTS: The agent must have read the change and cancellation policy "
    "pages, booked the cheapest Economy flight from Chicago O'Hare to Austin on "
    "October 21, 2026 for the given guest traveler with the specified Visa card, and "
    "then canceled it from My trips. The answer must report (1) the change fee for "
    "standard United Economy tickets and the Basic Economy rule, and (2) the "
    "confirmation number and the refund outcome (amount and destination). An empty "
    "answer is a FAIL."
)


def main() -> int:
    tasks_path = SITE / "tasks.jsonl"
    original = subprocess.run(
        ["git", "show", CONTRIB_REF], cwd=REPO, check=True,
        capture_output=True, text=True).stdout
    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 21, f"expected 21 rows, got {len(lines)}"

    out_lines = []
    for i, line in enumerate(lines):
        row = json.loads(line)
        assert list(row.keys()) == ["web_name", "id", "ques", "web",
                                    "upstream_url"], f"row {i} not the 5-key shape"
        # byte-identity assertion against the contribution head
        expected = json.loads(original.splitlines()[i])
        assert row == expected, f"row {i} drifted from {CONTRIB_REF}"
        # rebuild the original prefix byte-identically, then append two keys
        prefix = json.dumps(row, ensure_ascii=False, separators=(", ", ": "))
        # json.dumps default separators keep the original single-line form
        assert json.loads(prefix) == expected
        new_row = dict(row)
        new_row["verifier_path"] = f"sites/united_airlines/verify/verify_{i}.py"
        new_row["judge_rubric"] = RUBRICS[i]
        out_lines.append(json.dumps(new_row, ensure_ascii=False))
        # ensure the appended serialization still carries the original 5 keys
        # in order with identical values
        again = json.loads(out_lines[-1])
        assert list(again.keys()) == ["web_name", "id", "ques", "web",
                                      "upstream_url", "verifier_path",
                                      "judge_rubric"]
        for k in ("web_name", "id", "ques", "web", "upstream_url"):
            assert again[k] == expected[k]

    tasks_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"appended verifier_path + judge_rubric to {len(out_lines)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
