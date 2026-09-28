#!/usr/bin/env python3
"""append_rubrics.py — append verifier_path + judge_rubric to tasks.jsonl.

Audit-rail re-sync (2026-09-28): rubrics for the 17 deepened rows
(0,2,3,4,6,7,8,9,10,11,12,13,14,16,17,18,19) rewritten to match the
deepened task texts; rows 1/5/15 keep the reviewer's r2 rubrics.

Review-track contract writer (orch/review/thumbtack): for every task row the
original five keys (web_name, id, ques, web, upstream_url) keep their exact
bytes/values; exactly two keys are appended — verifier_path (deterministic
verifier module) and judge_rubric (English, rule-style judge instructions).
No answer key is ever written. Idempotent: rows that already carry both keys
are left untouched.
"""
import json
from pathlib import Path

TASKS = Path(__file__).resolve().parents[1] / "tasks.jsonl"

RUBRICS = {
 0: ("Verify the agent logged in as alice.j@test.com, compared the Thumbtack hires of the"
     "Seattle wedding photographers Jeshua Frees (Clearline Production), Tanner Schmidt and"
     "Liz Ong, saved all three to the saved pros, and then removed the two less popular ones"
     "from the saved list. The answer must state Jeshua Frees has the most hires (69, versus"
     "Tanner Schmidt's 30 and Liz Ong's 26), that only Jeshua Frees remains saved, and that he"
     "has been in business 7 years with 19 employees. Fail answers that pick a different"
     "remaining pro or invent the years or employee count."),
 1: ("Verify the agent logged in as bob.c@test.com, requested house cleaning quotes for a "
     "one-time deep clean of a 2-bedroom, 2-bathroom apartment in zip 98101, hired the "
     "cheapest responding pro, and left a 5-star review mentioning move-out. The answer must "
     "name Ipanema Cleaning Service as the hired pro with the lowest quote of $184 and "
     "confirm the 5-star move-out review. Fail answers that hire a different pro or report a "
     "different quote."),
 2: ("Verify the agent logged in as carol.d@test.com, opened the wedding DJ and wedding"
     "photographer cost guides, compared the national averages, then found the highest-rated"
     "DJ based in Everett, messaged them about an October wedding date, and requested an"
     "estimate describing the four-hour wedding reception. The answer must state the wedding"
     "DJ national average ($500-$600, national average cost $550) is more expensive than the"
     "photographer's ($122-$450, national average cost $150) by roughly $400, that the Everett"
     "DJ is Cessionnation, and quote their reply about the October date. Fail answers that"
     "swap the two services, skip the message or the estimate request."),
 3: ("Verify the agent logged in as alice.j@test.com, opened Paty House Cleaning's profile,"
     "identified the most-mentioned review word, checked the newest review for that theme,"
     "messaged Paty about cleaning supplies, asked a second house cleaner the same question,"
     "and followed up with Paty about a Sunday visit. The answer must state customers mention"
     "'clean' most often, that the theme also appears in the newest review, name the second"
     "cleaner (Empire Cleaning Services), and report all three replies: both cleaners bring"
     "all their own supplies and equipment, and Paty works around the customer's schedule"
     "including weekends. Fail answers that claim the customer must provide supplies or omit"
     "any of the three replies."),
 4: ("Verify the agent logged in as alice.j@test.com, opened the pending TV mounting project,"
     "reported its lowest quote and total quote count, cancelled it, and started a replacement"
     "handyman request in zip 98033 for hanging a heavy mirror, answering the questionnaire in"
     "full. The answer must state the lowest quote was $121 from Wa Pro Builders with 5 quotes"
     "in total, that the project was cancelled, and report the replacement request's cheapest"
     "quote ($62). Fail answers that report a different lowest pro, amount, count or"
     "replacement cheapest quote, or that skip the replacement request."),
 5: ("Verify the agent logged in as carol.d@test.com, updated the profile zip code to 98033 "
     "with a Kirkland address, found the highest-rated lawn care professional serving "
     "Kirkland, and requested a quote for weekly mowing. The answer must name Slc - Simple "
     "Lawn Care (4.8 rating, 65 reviews) as the pro quoted. Fail answers that name a pro from "
     "another city or skip the profile update."),
 6: ("Verify the agent logged in as david.k@test.com, found a plumber who is background"
     "checked and accepts Venmo (Velichkoremodels Llc Emergency Restoration 24/7), saved them,"
     "messaged them to confirm they can handle the urgent leak, requested a pipe-repair quote"
     "within a week describing the leaky kitchen faucet, and compared the lowest quote with"
     "the plumbers cost guide. The answer must name Velichkoremodels, confirm background check"
     "and Venmo, quote their same-day/next-day reply, state the lowest quote ($51), and place"
     "it against the guide's $50-$200 typical range. Fail answers that name a plumber without"
     "both credentials or invent the quote or range."),
 7: ("Verify the agent created a new account (Nina Patel, nina.p@test.com, NewHome2026!),"
     "requested quotes for assembling a large wardrobe and two bookcases in zip 98101"
     "answering the questionnaire about the three items and the instructions, hired the"
     "cheapest pro who responded, marked the project complete, and left a 5-star review"
     "mentioning the smooth assembly. The answer must state 4 pros responded and the cheapest"
     "quote was $107. Fail answers that report a different responder count or cheapest quote."),
 8: ("Verify the agent logged in as alice.j@test.com, found two handymen whose business hours"
     "include Sunday (Evergreen Home Assist Llc and I.d. Handyman), saved both, messaged the"
     "more-reviewed one (I.d. Handyman, 56 reviews) to confirm a Sunday visit, followed up in"
     "the same thread asking which Sunday time slots they have open, and removed the other"
     "handyman from the saved list. The answer must name both handymen with their Sunday hours"
     "and review counts and report both replies (they have openings and asked for dates). Fail"
     "answers that message the less-reviewed handyman or omit the removal."),
 9: ("Verify the agent logged in as bob.c@test.com, read the house cleaning cost guide,"
     "requested a one-time deep-cleaning quote for a 3-bedroom, 2-bathroom home in zip 98101,"
     "hired the pro with the cheapest quote, marked the project complete, and left a 5-star"
     "review. The answer must state most people pay $174-$256 for a one-time visit, name"
     "Ipanema Cleaning Service as the hired pro with the $184 cheapest quote, and say whether"
     "the price falls inside the guide's typical range (it does). Fail answers that report a"
     "different range, pro or quote, or skip the inside/outside verdict."),
 10: ("Verify the agent logged in as bob.c@test.com, removed the moving companies (At Moving"
     "and John Frank Moving Company) from the saved pros, opened the pending moving project,"
     "reported its lowest quote, checked that pro's profile for rating and response speed,"
     "cancelled the project, and started a smaller studio-move replacement request in zip"
     "98101. The answer must state the lowest quote was $199 from Strok Industries Moving"
     "Company (Excellent 4.9, responds within a day), that the project was cancelled, and that"
     "the studio replacement received 5 quotes. Fail answers that mix up the removed pros, the"
     "lowest quote, or the replacement responder count."),
 11: ("Verify the agent logged in as carol.d@test.com, compared the makeup artist and wedding"
     "DJ cost guides, found the highest-rated Top Pro makeup artist based in Redmond (Mel"
     "Mua), messaged her about an October event, and requested an estimate describing the"
     "quinceanera makeup. The answer must state a DJ is more expensive (averages $550 vs $167,"
     "ranges $500-$600 vs $156-$178), name Mel Mua with Top Pro status, and quote her reply"
     "about the October event. Fail answers that swap the services or skip the message or"
     "estimate request."),
 12: ("Verify the agent logged in as alice.j@test.com, opened the finished house cleaning"
     "project, noted the hired pro's price and response note, checked the pro's profile"
     "reviews, left a 5-star review saying they were thorough including the word 'spotless',"
     "reopened the profile to confirm the review is the most recent one, and messaged the pro"
     "about a move-out clean next month with a supplies follow-up. The answer must state"
     "Empire Cleaning Services was hired at $244, quote the response note, confirm the"
     "spotless review shows as the most recent, and report both message replies. Fail answers"
     "that report a different hired price or omit either reply."),
 13: ("Verify the agent logged in as alice.j@test.com, read the existing message thread about"
     "cleaning supplies, asked a different house cleaner (Empire Cleaning Services) the same"
     "question, followed up with them about Sunday availability, and asked the first cleaner"
     "(Ipanema Cleaning Service) the Sunday question too. The answer must quote what Ipanema"
     "brings (all their own supplies and equipment), state the second cleaner answered the"
     "same way, and report both Sunday replies (both work around the schedule including"
     "weekends) with the comparison. Fail answers that claim either cleaner requires the"
     "customer to provide supplies or omit the comparison."),
 14: ("Verify the agent logged in as bob.c@test.com, read the exterminator cost guide,"
     "requested quotes for indoor ant treatment in zip 98101 within a week from the Top Pro"
     "exterminators, hired the responder with the most reviews, marked the project complete,"
     "left a 5-star review mentioning the ants, and confirmed on the pro's profile that the"
     "review shows. The answer must state exterminators typically run $131-$341, name Super"
     "Attic Solutions (123 reviews) with a $315 quote, and confirm the review appears as the"
     "most recent on the profile. Fail answers that report a different guide range, pro,"
     "review count or quote."),
 15: ("Verify the agent logged in as alice.j@test.com, used the Kirkland city page to find "
      "the house cleaner with the most reviews, messaged them about supplies, and requested "
      "a quote for a standard cleaning of a 3-bedroom home. The answer must name Empire "
      "Cleaning Services (33 reviews), quote their reply that they bring all of their own "
      "supplies and equipment, and confirm the quote request. Fail answers that name a "
      "cleaner not shown on the Kirkland city page."),
 16: ("Verify the agent logged in as david.k@test.com, read the personal trainer cost guide,"
     "found the highest-rated personal trainer based in Bellevue (Gaskill Personal Training),"
     "messaged them to confirm twice-a-week slots, and requested a quote describing"
     "twice-a-week strength sessions. The answer must state sessions typically cost $40-$100"
     "(national average $55), name Gaskill Personal Training, and quote their reply about"
     "morning and evening slots. Fail answers that report a different range or trainer or skip"
     "the message or quote request."),
 17: ("Verify the agent logged in as alice.j@test.com, requested TV mounting quotes in zip"
     "98052 answering the questionnaire to match a 75-inch TV above the fireplace with"
     "concealed cables and a connected sound bar, hired the pro with the lowest quote, marked"
     "the project complete, and left a 5-star review mentioning the tidy cable work. The"
     "answer must state 4 pros responded, that the lowest quote was $127, and name the hired"
     "pro (Mmy). Fail answers that report a different responder count, lowest quote or hired"
     "pro."),
 18: ("Verify the agent logged in as carol.d@test.com, started from the Services near me page,"
     "opened the Events services group's wedding and event makeup category, sorted by Most"
     "hires, checked the top makeup artist's profile for Top Pro status and response speed,"
     "messaged her about an October 18 event, followed up about a pre-event trial, and saved"
     "her to the saved pros. The answer must name Mel Mua with 121 hires and 71 reviews, state"
     "her Top Pro status and 28-minute response time, and report both replies. Fail answers"
     "that name a different artist or invent the hires, reviews or replies."),
 19: ("Verify the agent logged in as bob.c@test.com, found the appliance repair specialist who"
     "responds fastest (Hotwire Hvac Refrigeration & Appliance Repair, about 1 min), requested"
     "a quote describing the emergency repair for the GE refrigerator, hired the pro with the"
     "lowest quote, and left a 5-star review mentioning the refrigerator. The answer must name"
     "Hotwire, state the lowest quote received ($130), and confirm the GE refrigerator"
     "description and the review. Fail answers that name a different specialist or invent the"
     "quote."),
}


def main() -> int:
    lines = TASKS.read_text(encoding="utf-8").splitlines()
    out = []
    changed = 0
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        row = json.loads(line)
        if "verifier_path" in row and "judge_rubric" in row:
            out.append(line)
            continue
        assert set(row) == {"web_name", "id", "ques", "web", "upstream_url"}, \
            f"unexpected key set in line {i + 1}: {sorted(row)}"
        n = int(row["id"].split("--")[1])
        new_row = dict(row)
        new_row["verifier_path"] = f"sites/thumbtack/verify/verify_{n}.py"
        new_row["judge_rubric"] = RUBRICS[n]
        # keep the original 5 keys byte-identical: re-emit their exact json
        # fragments from the original line, then append the two new keys.
        prefix = line.rstrip()
        assert prefix.endswith("}")
        prefix = prefix[:-1].rstrip()
        if prefix and not prefix.endswith(","):
            prefix += ","
        out.append(prefix + ' "verifier_path": ' + json.dumps(new_row["verifier_path"])
                   + ', "judge_rubric": ' + json.dumps(new_row["judge_rubric"]) + "}")
        changed += 1
    TASKS.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"tasks.jsonl: {changed} rows extended, {len(out) - changed} already done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
