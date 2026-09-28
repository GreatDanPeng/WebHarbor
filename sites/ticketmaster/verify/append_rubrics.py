#!/usr/bin/env python3
"""append_rubrics.py — append verifier_path + judge_rubric to tasks.jsonl.

Review-track contract writer (orch/review/ticketmaster): for every task row
the original five keys (web_name, id, ques, web, upstream_url) keep their
exact bytes/values; exactly two keys are appended — verifier_path
(deterministic verifier module) and judge_rubric (English, rule-style judge
instructions; no frozen numeric ground truth). No answer key is ever
written. Idempotent: rows that already carry both keys are left untouched.

Usage: python3 sites/ticketmaster/verify/append_rubrics.py [--check]
  --check  verify every line's 5-key prefix is byte-identical to the
           contributor's tasks.jsonl at 73b29ac8 and exit non-zero otherwise.
           The one sanctioned exception is the `web` port: the audit-phase
           slot normalization moves it to the site's assigned merge port
           (40146; the slot formula index = registered sites on main (99) + 47).
"""
import json
import subprocess
import sys
from pathlib import Path

TASKS = Path(__file__).resolve().parents[1] / "tasks.jsonl"
CONTRIB_REF = "73b29ac8:sites/ticketmaster/tasks.jsonl"
OLD_WEB = '"web": "http://localhost:40101/"'
NEW_WEB = '"web": "http://localhost:40146/"'

RUBRICS = {
 0: ("Verify the agent signed in with the demo account, searched for the Knicks vs. "
     "Pistons game at Madison Square Garden, completed the checkout of the two cheapest "
     "available Standard Admission tickets on the event page, and confirmed the order in "
     "My Account. The answer must report the runtime order number exactly as shown on the "
     "confirmation page and in My Account, the purchased seats (section and row as "
     "selected), and the all-in total for the two tickets as shown at checkout. An answer "
     "with no order number, seats/total that do not match the purchased Standard "
     "Admission listing, or a non-Standard (e.g. accessible) purchase is a FAIL. An empty "
     "answer is a FAIL."),
 1: ("Verify the agent compared Standard Admission prices across the listed Metallica at "
     "Sphere dates before choosing, then completed a guest checkout with the given email. "
     "The answer must report the chosen event date, the section and row of the tickets "
     "actually purchased, and the total charged on the confirmation page. Answers that "
     "pick a date without comparing standard prices, or that report seats/total not "
     "matching the purchase, are FAILs. An empty answer is a FAIL."),
 2: ("Verify the agent opened the Lion King performance page at the Hollywood Pantages "
     "Theatre on January 2, 2027, read its Citi cardmember presale information, checked "
     "what presales the theatre's other January dates list, and consulted the help "
     "centre's presale article. The answer must state when the Citi presale window opens "
     "and closes (as shown on the event page), what must be entered during checkout to "
     "buy with it (the presale code requirement and the payment-card requirement "
     "described in the presale notes), which presale runs right after the Citi window, "
     "what presales the other January dates list (so whether a Citi presale can be used "
     "there), how many tickets one order can contain, and whether the help centre says "
     "presale access guarantees tickets. An answer that invents dates, code instructions, "
     "presale types, a limit, or a guarantee not shown on the site is a FAIL. An empty "
     "answer is a FAIL."),
 3: ("Verify the agent opened the Lion King performance page at the Hollywood Pantages "
     "Theatre on January 2, 2027, used the accessible ticket filter on that page, and "
     "consulted the help centre's accessible-tickets article. The answer must report how "
     "many accessible options that performance lists, the section, the row, and the "
     "all-in price for 2 accessible tickets together (exactly as listed), how much cheaper "
     "that is than 2 of the cheapest Standard Admission seats at the same show, and what "
     "the help centre says about how accessible seating is bought. An answer with a "
     "different section/row, a price not matching the accessible listing, a wrong "
     "comparison, or guidance not from the help centre is a FAIL. An empty answer is a "
     "FAIL."),
 4: ("Verify the agent opened both venue pages (Sphere in Las Vegas and TD Garden in "
     "Boston) to compare their upcoming event counts, and opened the Bruins vs. Winnipeg "
     "Jets event page for the ticket price. The answer must state which venue lists more "
     "events, the street address of the venue with fewer events as shown on its venue "
     "page, and the cheapest all-in price for a Standard Admission ticket to the game as "
     "listed on the event page. An answer with swapped counts, a wrong address, or a "
     "price not matching the cheapest Standard Admission listing is a FAIL. An empty "
     "answer is a FAIL."),
 5: ("Verify the agent used the discovery filters (city and date window) to find Music "
     "events in Las Vegas across the last weekend of October 2026, compared them by "
     "their Standard Admission prices, and opened the winning event page. The answer "
     "must report the winning event's name and date, its cheapest Standard Admission "
     "section and row, the all-in total for 2 of those tickets, and which day of the week "
     "each show falls on. An answer naming an event outside the window, picking a "
     "winner without comparing Standard Admission prices, or reporting seats/total not "
     "matching the cheapest Standard listing is a FAIL. An empty answer is a FAIL."),
 6: ("Verify the agent opened the gift cards page and checked the balance of each of "
     "the three given gift card numbers through the balance form, and opened the Bruins "
     "vs. Winnipeg Jets event page. The answer must report the balance of each card as "
     "returned by the site, what the three add up to, whether that covers 2 of the "
     "cheapest Standard Admission tickets for the game (with that price as listed), and "
     "the maximum amount a single gift card can carry as stated on this site's gift "
     "cards page. An answer without the checked balances, a wrong sum or coverage call, "
     "or a maximum not stated on the page is a FAIL. An empty answer is a FAIL."),
 7: ("Verify the agent signed in with the demo account, found the Aladdin - The Musical "
     "order in My Account and opened its detail page, and consulted the help centre's "
     "transfer-tickets and mobile-tickets articles. The answer must report the order "
     "number, how many tickets it covers, the seats, and the card charged (all as shown "
     "on the order page), and per the help centre: from which page a ticket transfer "
     "starts, what the recipient needs to do, what happens to the original ticket once "
     "she accepts it, and when mobile tickets usually arrive. An answer that invents "
     "order details or a transfer process/outcome not on the site is a FAIL. An empty "
     "answer is a FAIL."),
 8: ("Verify the agent signed in as the demo account bob.c@test.com, reviewed Bob's order "
     "history and favorites in the member area. The answer must report which event he "
     "bought 3 tickets for, the section and row of those seats, the venue, the total "
     "charged (all as shown on the order detail page), and the two events saved under My "
     "Favorites. An answer that confuses the two orders or lists a non-event favorite as "
     "an event is a FAIL. An empty answer is a FAIL."),
 9: ("Verify the agent signed in as the demo account carol.d@test.com, added the described "
     "Discover card in Payment Options, confirmed it appears there, and removed the card "
     "that was already on file. The answer must name which card remains saved. An answer "
     "that leaves the old card, fails to add the Discover card, or names the wrong "
     "remaining card is a FAIL. An empty answer is a FAIL."),
 10: ("Verify the agent signed in as the demo account david.k@test.com, removed the saved "
      "Rod Wave tour event from My Favorites, added the Trans-Siberian Orchestra artist "
      "page as a favorite, and re-opened My Favorites. The answer must list exactly "
      "which items remain under My Favorites after both changes. An answer that omits "
      "the newly added artist or still lists the removed event is a FAIL. An empty "
      "answer is a FAIL."),
 11: ("Verify the agent, as a guest, bought 2 of the cheapest available Standard "
      "Admission tickets for the Bruins vs. Winnipeg Jets game at TD Garden using the "
      "given email. The answer must report the order number from the confirmation page, "
      "the seats (section and row) of the purchased Standard Admission listing, and the "
      "total charged. An answer reporting accessible/VIP seats or a total not matching "
      "the purchase is a FAIL. An empty answer is a FAIL."),
 12: ("Verify the agent opened an Aladdin - The Musical performance page at the New "
      "Amsterdam Theatre, a New York Knicks event page at Madison Square Garden, the "
      "help centre's ticket-limits article, and the site's Terms of Use. The answer must "
      "state the per-order ticket limit shown on each event page, what the help centre "
      "says happens to orders that exceed the published limit, which personal details "
      "it says are checked when enforcing limits, and what the Terms of Use add about "
      "how limits are enforced. An answer with a limit, consequence, detail list, or "
      "terms clause not shown on those pages is a FAIL. An empty answer is a FAIL."),
 13: ("Verify the agent searched for the festival among the near-name events, opened the "
      "Power to the People Festival event page, selected the section 202 row G listing, "
      "read the price breakdown for 3 tickets and for 1 ticket, and compared the "
      "cheapest Standard Admission ticket in section 118. The answer must report the "
      "face-value portion, the service-fee portion, and the order total for the 3 "
      "tickets, the total and service-fee portion for 1 ticket in that row, and the "
      "per-ticket price of the cheapest Standard Admission listing in section 118 — all "
      "exactly as shown on the site. An answer whose amounts do not match the displayed "
      "breakdowns or the 118 listing is a FAIL. An empty answer is a FAIL."),
 14: ("Verify the agent found the Wicked (Touring) artist page, read its full tour list, "
      "identified the first upcoming tour stop, opened that performance, and read its "
      "cheapest Standard Admission option. The answer must report the date, the venue, "
      "and the city of the first stop, how many stops the tour lists in total, when the "
      "last one is, the act's average fan rating and review count, plus the section, "
      "row, and all-in per-ticket price of the cheapest Standard Admission option on "
      "that performance's event page, and how many tickets one order can contain. An "
      "answer with a later stop, a wrong stop count or rating, or a section/row/price "
      "not matching the cheapest Standard listing is a FAIL. An empty answer is a "
      "FAIL."),
 15: ("Verify the agent used the discovery filters (date window and max price) on the "
      "Family category to find the February 2027 event with the lowest starting price "
      "under the cap, then opened that event. The answer must report the event name, "
      "city, date, and starting all-in price, and the section and row of the event's "
      "cheapest Standard Admission option as listed on the event page. An answer naming "
      "an event outside February 2027 or above the cap, or a section/row not matching "
      "the cheapest Standard Admission listing, is a FAIL. An empty answer is a FAIL."),
 16: ("Verify the agent opened the Trans-Siberian Orchestra artist page and the Wicked "
      "(Touring) artist page. The answer must report TSO's average fan rating and the "
      "number of reviews it is based on, how many of their events are listed for "
      "December 2026, and when and at which venue their first December show is; plus "
      "Wicked (Touring)'s average rating and review count, how many of its events are "
      "listed in 2026, and which act fans rate higher. An answer with a rating, review "
      "count, event count, first-show detail, or comparison not matching the artist "
      "pages is a FAIL. An empty answer is a FAIL."),
 17: ("Verify the agent signed in with the demo account, filtered the WEEZER: The "
      "Gathering show at Barclays Center for at least 4 seats together, picked the "
      "cheapest Standard Admission option that still has at least 4 seats together, "
      "completed the purchase of 4 tickets, and confirmed the order in My Account. The "
      "answer must report the runtime order number, the section and row of the "
      "purchased 4-together Standard Admission listing, and the total for 4 tickets. "
      "An answer with seats not matching the purchase, a non-Standard purchase, or a "
      "total for a different quantity is a FAIL. An empty answer is a FAIL."),
 18: ("Verify the agent opened the Harry Styles: Together, Together show at Madison "
      "Square Garden on September 30, inspected its VIP Package ticket option "
      "(including its availability), read the 2-ticket price breakdown, and compared it "
      "with the cheapest Standard Admission option at the same show. The answer must "
      "report how many VIP package tickets are available, the section and row of the "
      "VIP seats, the all-in cost of 2 of them, how much of that is service fees, and "
      "how much more 2 VIP tickets cost than 2 of the cheapest Standard Admission "
      "seats. An answer with an availability count, seats, cost, fee portion, or "
      "difference not matching the site is a FAIL. An empty answer is a FAIL."),
 19: ("Verify the agent signed in as the demo account david.k@test.com, confirmed the "
      "Karol G order in the order history, and consulted the sell page and the help "
      "centre. The answer must report the numbered steps Ticketmaster gives for selling "
      "tickets (as shown on the sell page), the page in the account where the listing "
      "starts, and the phone number this site's help centre gives for ordering tickets "
      "by phone. An answer that invents steps, a starting page, or a phone number not "
      "shown on the site is a FAIL. An empty answer is a FAIL."),
}

VERIFIER_PATH = "sites/ticketmaster/verify/verify_{}.py"


def check_prefix_bytes() -> int:
    ref = subprocess.run(["git", "show", CONTRIB_REF], capture_output=True,
                         text=True, cwd=str(TASKS.parents[2]))
    if ref.returncode != 0:
        print(f"[append_rubrics] cannot read contributor reference {CONTRIB_REF}")
        return 1
    contrib_lines = ref.stdout.splitlines()
    current_lines = TASKS.read_text(encoding="utf-8").splitlines()
    if len(current_lines) != len(contrib_lines):
        print(f"[append_rubrics] line count changed: {len(current_lines)} vs "
              f"{len(contrib_lines)}")
        return 1
    for cur, con in zip(current_lines, contrib_lines):
        # byte-prefix property holds modulo the sanctioned web-port re-base
        con_rebased = con.replace(OLD_WEB, NEW_WEB)
        if not cur.startswith(con_rebased.rstrip("}")):
            print("[append_rubrics] original 5-key prefix bytes changed for row: "
                  f"{con[:60]}...")
            return 1
        row = json.loads(cur)
        if not (set(row.keys()) - set(json.loads(con).keys())) == {"verifier_path", "judge_rubric"}:
            print(f"[append_rubrics] unexpected key set for row {row['id']}: "
                  f"{sorted(row.keys())}")
            return 1
    print(f"[append_rubrics] all {len(current_lines)} rows keep the original "
          f"5-key bytes as a prefix; only verifier_path + judge_rubric appended")
    return 0


def main() -> int:
    if "--check" in sys.argv:
        return check_prefix_bytes()
    lines = TASKS.read_text(encoding="utf-8").splitlines()
    out = []
    appended = 0
    for line in lines:
        row = json.loads(line)
        if "verifier_path" in row and "judge_rubric" in row:
            out.append(line)
            continue
        n = int(row["id"].split("--")[1])
        # textual append keeps the original 5-key bytes as an exact prefix
        inner = line.rstrip("}")
        new_line = (f'{inner}, "verifier_path": '
                    f'{json.dumps(VERIFIER_PATH.format(n), ensure_ascii=False)}, '
                    f'"judge_rubric": {json.dumps(RUBRICS[n], ensure_ascii=False)}}}')
        # sanity: the new line must parse and extend the original keys
        new_row = json.loads(new_line)
        assert new_row["verifier_path"] == VERIFIER_PATH.format(n)
        assert new_row["judge_rubric"] == RUBRICS[n]
        for k, v in row.items():
            assert new_row[k] == v
        out.append(new_line)
        appended += 1
    TASKS.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"[append_rubrics] appended verifier_path + judge_rubric to {appended} rows "
          f"({len(out) - appended} already carried them)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
