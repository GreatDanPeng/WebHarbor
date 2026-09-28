#!/usr/bin/env python3
"""append_rubrics.py — append verifier_path + judge_rubric to tasks.jsonl.

Idempotent: rows that already end with the exact verifier_path + judge_rubric
pair are left byte-identical; the original 5-key serialization stays a
byte-identical prefix of every row (no answer key is ever added — the rubrics
are English, pure rules, and the deterministic ground truth lives only in
verify/make_verifiers.py + the generated verify_<N>.py).
"""
import json
from pathlib import Path

TASKS = Path(__file__).resolve().parent.parent / "tasks.jsonl"

RUBRICS = {
 0: "Verify the agent searched parking near Millennium Park for the Oct 3 12:00-18:00 window, filtered to covered garages, sorted by price, and opened the cheapest garage's facility page before booking it as a guest with the required email. The answer must name the cheapest covered garage, its star rating, its height restriction, the total paid, and the reservation code shown on the confirmation page. Fail answers that name a different garage, omit the height restriction, or invent a total or code.",
 1: "Verify the agent opened the monthly parking landing page and its Chicago section, reported the cheapest featured monthly rate, then searched monthly parking in Chicago, opened the two cheapest facilities' pages to compare access hours, and booked the cheaper one as a guest with the required email. The answer must state the featured rate, the booked facility, its monthly rate, its access hours, and the reservation code. Fail answers that book the more expensive option or report a rate not shown on the site.",
 2: "Verify the agent opened the Climate Pledge Arena destination page, inspected the parking search for both the Tyler Childers and the JUNGLE events, and reported both parking windows before deciding which starts earlier. The answer must state both windows, identify the earlier show, name the cheapest option booked for that show with its walking time from the arena, the total, and the reservation code. Fail answers that swap the windows or book the later show.",
 3: "Verify the agent compared the cheapest shuttle-served lot at O'Hare with the cheapest shuttle-served lot at Midway for the Oct 3 noon to Oct 6 noon window by per-day rate, opened the cheaper lot's facility page, and booked it as a guest with the required email. The answer must name the winning airport and facility, the total, the first step of its getting-there directions, and the reservation code. Fail answers that compare totals instead of per-day rates or pick the wrong airport.",
 4: "Verify the agent logged in as Alice Johnson, opened each of her two upcoming reservations to compare their end times, extended the sooner-ending one by two hours, cancelled the other, and quoted the refund message. The answer must identify the sooner-ending reservation, the extension's additional charge, the refund message, and which card on file the extension charge would go to. Fail answers that extend the wrong reservation or invent the charge.",
 5: "Verify the agent logged in as David Kim, cancelled his upcoming airport reservation and quoted the refund message, then booked the cheapest shuttle-served O'Hare lot for Oct 10 noon through Oct 14 noon. The answer must quote the refund message, name the booked lot, and state the new reservation's total. Fail answers that book a non-shuttle lot or report the wrong window.",
 6: "Verify the agent found the promo code advertised on the site for new customers, searched four hours of parking near Fenway Park for the required window, and applied the promo code at checkout as a guest with the required email. The answer must state the code, the discount it took off, and the final total paid. Fail answers that invent a code or report a discount the checkout did not apply.",
 7: "Verify the agent searched covered parking near Times Square for the required window, compared height restrictions against a 6'9\" cargo van, and booked the cheapest covered garage whose restriction actually fits as a guest with the required email. The answer must name the garage, its height restriction, and the total. Fail answers that book a garage the van cannot enter or ignore the height restriction.",
 8: "Verify the agent opened both the 225 N Michigan Ave. and 318 S Federal Street facility pages, compared their star ratings and what drivers like most about each, and booked the better-reviewed one as a guest with the required email. The answer must state both ratings, what drivers like about each, name the booked facility, and the total. Fail answers that book the worse-reviewed garage.",
 9: "Verify the agent quoted the FAQ's cancellation policy and card-charge timing, found what the parking guarantee promises when a spot is not available, and booked the cheapest spot near Union Square for the required window as a guest with the required email. The answer must quote all three policies, name the booked spot, and state the total and reservation code. Fail answers that paraphrase the policies into different commitments or invent prices.",
 10: "Verify the agent read the commuter and weekend price ranges from the Chicago parking page, searched covered parking near the Loop for the required window sorted by price, opened the cheapest garage's facility page for its height restriction, and booked it as a guest with the required email. The answer must state both ranges, the garage, its height restriction, and the total. Fail answers that report ranges not shown on the city page.",
 11: "Verify the agent opened the Wrigley Field destination page, identified the spot its nearby list features first, searched parking over the required window sorted by price, opened that featured spot's facility page, and booked it as a guest with the required email. The answer must state whether a height restriction applies to an SUV, quote the first Getting There instruction, and state the total. Fail answers that book a different spot than the featured-first one.",
 12: "Verify the agent read the NFL stadium and NHL arena counts from the Stadium Parking page, searched parking near Soldier Field for the required window sorted by price, opened the cheapest lot's facility page to check in-and-out privileges, and reserved it as a guest with the required email. The answer must state both counts, the facility, the in-and-out finding, and the total. Fail answers that miscount the leagues or claim privileges the lot does not offer.",
 13: "Verify the agent logged in as Carol Davis, added a Visa card ending in 4242 expiring September 2029 with the label 'Cubs Season', made it the default payment method, and removed the Mastercard ending in 6742. The answer must identify which upcoming reservation would be charged to the new default card and which other card remains on file. Fail answers that leave the old card as default or remove the wrong card.",
 14: "Verify the agent logged in as Bob Chen, updated the profile license plate to WI-BO1180 and the vehicle to Honda CR-V Hybrid, saved, logged out and back in, and confirmed the plate persisted. The answer must state the persisted plate, the brand and last four digits of the default payment method, and how many past reservations the account shows. Fail answers that report a plate the profile does not show after re-login.",
 15: "Verify the agent logged in as Alice Johnson, saved the Millennium Park Garage facility to her saved spots from its facility page (the save button toggles — an already-saved spot must still be saved at the end), found and saved the cheapest covered garage near Union Square for the required window, then reviewed the saved spots list and removed every spot whose starting price is above $20. The answer must report which spots remain and their prices. Fail answers that leave the list without the required saves or remove spots at or below $20.",
 16: "Verify the agent quoted the O'Hare page's FAQs on when you pay for airport parking, accessible parking, and long-term economy parking, searched the cheapest covered shuttle-served lot for the Oct 3 noon four-day window, opened its facility page for the first getting-there instruction, and booked it as a guest with the required email. The answer must quote all three FAQ answers, the instruction, the total, and the parking pass type. Fail answers that invent FAQ text or a pass type.",
 17: "Verify the agent created a new account with the required first name, last name, email, and password, then booked the cheapest parking near the United Center for the required window. The answer must state the reservation code and the total. Fail answers that reuse an existing account or report a total the checkout did not show.",
 18: "Verify the agent compared the cheapest covered parking near Fenway Park with the cheapest covered parking near Times Square for the same Oct 3 7:00 PM to midnight window, identified the cheaper city and the price difference, and booked the cheaper option as a guest with the required email. The answer must name both compared facilities with their prices, the cheaper city, the difference, the booked facility, and the total. Fail answers that mix subtotals with fee-inclusive totals in the comparison or swap the cities.",
 19: "Verify the agent searched monthly parking in Denver for a November 1 start, opened the two cheapest facilities' pages to compare monthly rates and access hours, and reserved the cheaper one as a guest with the required email. The answer must state the reserved facility, its monthly rate, and the access hours found. Fail answers that reserve a facility outside the tied-cheapest set or report a rate not shown.",
 20: "Verify the agent opened the Climate Pledge Arena destination page, found the Seattle Kraken vs. Calgary Flames game in the upcoming events list, reported the parking window SpotHero sets, filtered to covered garages that allow in-and-out, sorted by price, opened the cheapest garage's facility page for its height restriction and first Getting There instruction, switched the results to totals with fees, and booked it as a guest with the required email. The answer must state the window, the garage, its height restriction, the instruction, and the total with fees. Fail answers that report the subtotal instead of the fee-inclusive total or skip the in-and-out filter.",
}


def build_row(line: str, task_no: int) -> str:
    prefix, obj = line, json.loads(line)
    keys = list(obj.keys())
    if keys[:5] != ["web_name", "id", "ques", "web", "upstream_url"]:
        raise SystemExit(f"unexpected key order in row {task_no}: {keys}")
    if "verifier_path" in obj or "judge_rubric" in obj:
        return line  # already appended
    additions = {"verifier_path": f"sites/spothero/verify/verify_{task_no}.py",
                 "judge_rubric": RUBRICS[task_no]}
    suffix = json.dumps(additions, separators=(", ", ": "))[1:-1]
    body = prefix.rstrip("\n").rstrip("}")
    return body + ", " + suffix + "}\n"


def main():
    lines = TASKS.read_text(encoding="utf-8").splitlines(keepends=True)
    if len(lines) != 21:
        raise SystemExit(f"expected 21 rows, found {len(lines)}")
    out = []
    for i, line in enumerate(lines):
        row = json.loads(line)
        if row["id"] != f"SpotHero--{i}":
            raise SystemExit(f"row {i} has unexpected id {row['id']}")
        out.append(build_row(line, i))
    TASKS.write_text("".join(out), encoding="utf-8")
    print(f"tasks.jsonl: {len(out)} rows; verifier_path + judge_rubric appended")


if __name__ == "__main__":
    main()
