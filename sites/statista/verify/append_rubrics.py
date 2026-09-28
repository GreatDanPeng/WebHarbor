#!/usr/bin/env python3
"""Append verifier_path + judge_rubric to sites/statista/tasks.jsonl (review
track). The original 5-key lines stay byte-identical as prefixes of the new
7-key lines; no answer key is ever added; rubrics are English, pure rules.

Idempotent: re-running rewrites the same appended fields.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASKS = HERE.parent / "tasks.jsonl"

RUBRICS = {
0: ("Verify the agent searched for the worldwide inflation statistic, opened "
    "'Average inflation rate worldwide from 1980 to 2031' (statistic 256598), "
    "used the table view to read the values, and registered or logged into an "
    "account to save the statistic to favorites. The answer must state the 2025 "
    "average world inflation rate of 4.13 percent and the 2031 forecast value of "
    "3.2 percent, and confirm the statistic was saved to the account favorites. "
    "Fail answers that swap the years or invent values."),
1: ("Verify the agent opened 'Most popular social networks worldwide' "
    "(statistic 272014) and downloaded it as a PNG with an account. The answer "
    "must name Facebook* as the top network with about 3,070 million monthly "
    "active users and state that the download is retrieved in the account's "
    "download history (Account > Downloads). Fail answers naming WhatsApp or "
    "Instagram as the top network."),
2: ("Verify the agent opened 'Countries with the largest nominal GDP worldwide "
    "in 2026' (statistic 268173) and saved it to favorites with an account. The "
    "answer must state the top economy is the United States with 32.38 trillion "
    "U.S. dollars, Germany at 5.45 trillion, and that the U.S. is larger by "
    "26.93 trillion. Fail answers that name China as the top economy."),
3: ("Verify the agent logged in as bob.c@test.com, found 'Leading countries in "
    "installed renewable energy capacity worldwide in 2025' (statistic 267233), "
    "and added it to bob's favorites. The answer must state China leads with "
    "2,258.02 gigawatts. Fail answers naming the United States as the leader."),
4: ("Verify the agent opened the pricing page and registered the free account "
    "for frank.miller@test.com (username frank_m). The answer must state the "
    "cheapest plan including premium statistics is the Starter Account at $199 "
    "USD per month (billed annually), the Professional Account costs $2,388 USD "
    "per year, and that the pricing page lists report access for the Personal "
    "and Professional Accounts. Fail answers that misstate the prices."),
5: ("Verify the agent opened the Consumer Trends 2026 report (study 206237) and "
    "the Video gaming worldwide report (study 123559). The answer must state 37 "
    "pages, released 2025, priced $595 USD, the first three table-of-contents "
    "chapters 'Consumer sentiment', 'Consumer spending and cautious optimism', "
    "'How tariffs are shaping consumption', and that the video gaming report has "
    "more pages (62). Fail answers that swap the two reports."),
6: ("Verify the agent navigated Market Insights > Mobility to the worldwide "
    "ride-hailing market page. The answer must state the projected 2026 revenue "
    "of US$188.60bn, the projected market volume of US$229.98bn by 2030, and "
    "that China is expected to generate the most revenue. Fail answers with "
    "other figures or countries."),
7: ("Verify the agent registered the account casey.r@test.com (username "
    "casey_r), opened 'Annual global emissions of carbon dioxide 1940-2025' "
    "(statistic 276629), read the table view, saved it to favorites, and "
    "confirmed it in the new account. The answer must state the most recent year "
    "2025 with 38.11 billion metric tons. Fail answers reporting 2024 or other "
    "values."),
8: ("Verify the agent opened 'Leading eSports games worldwide in 2025' "
    "(statistic 501853) and switched to the table view. The answer must name "
    "Counter-Strike 2 with 18.97 million U.S. dollars as the biggest cumulative "
    "prize pool, Dota 2 second with 16.47 million, and confirm the "
    "third-placed game Fortnite with 12.91 million from the table. Fail answers "
    "that swap the ranking."),
9: ("Verify the agent opened the worldwide inflation statistic (256598), its "
    "citations box, and both the APA and MLA formats. The answer must give the "
    "full APA citation naming the Statista Research Department as publisher with "
    "the cited URL https://www.statista.com/statistics/256598/"
    "global-inflation-rate-compared-to-previous-year/, the MLA citation for the "
    "same statistic, and the survey time period from 01/01/1980 to 31/12/2031. "
    "Fail answers with a different publisher or URL."),
10: ("Verify the agent opened the TikTok topic page (topic 6077) and the TikTok "
     "penetration editor's pick (statistic 1299829). The answer must state about "
     "1.99bn global TikTok users, a brand value of 75.67bn USD, the 'TikTok' "
     "report offered on the topic, and the penetration statistic's last-update "
     "date Jun 12, 2026. Fail answers with other figures or dates."),
11: ("Verify the agent logged in as alice.j@test.com, opened her download "
     "history and favorites, and removed the statistic from favorites. The "
     "answer must identify her most recent download as 'Market size of AI "
     "worldwide 2020-2032' (PNG) and confirm it was removed from her favorites. "
     "Fail answers naming a different download."),
12: ("Verify the agent opened 'Leading countries based on Instagram audience "
     "size' (statistic 578364). The answer must state India has the largest "
     "audience with 480.55 million users, three countries are above 100 million "
     "(India, United States, Brazil), and the release/update date shown is Oct "
     "21, 2025. Fail answers counting two or four countries."),
13: ("Verify the agent used the Reports content-type filter, opened "
     "'Artificial Intelligence: in-depth market analysis' (study 50485), and "
     "saved it to carol.d@test.com's favorites. The answer must state 295 pages, "
     "released September 2025, priced $1,995 USD, and that the visible table of "
     "contents begins with the 'Description' heading. Fail answers with other "
     "page counts or prices."),
14: ("Verify the agent opened 'Annual inflation rate of selected global regions "
     "in 2025' (statistic 256626). The answer must state Sub-Saharan Africa had "
     "the highest inflation at 12.48 percent, the European Union rate was 2.46 "
     "percent, the survey period 01/01/2025 to 31/12/2025, and the update date "
     "Apr 15, 2026. Fail answers that swap the regions."),
15: ("Verify the agent logged in as carol.d@test.com (Professional Account), "
     "downloaded the Consumer Trends 2026 report (study 206237), and opened her "
     "download history. The answer must state the report download appears in PDF "
     "format and the most recent statistic downloaded before it is 'Leading "
     "countries in installed renewable energy capacity worldwide in 2025' "
     "(PPT). Fail answers naming a different prior download."),
16: ("Verify the agent opened 'Weekly oil prices in Brent, OPEC basket, and WTI "
     "futures 2020-2026' (statistic 326017) and switched to the table view. The "
     "answer must report the most recent week Jul 21 '26 with the Brent price "
     "91.47 U.S. dollars per barrel, the WTI price 84.91, and the OPEC basket "
     "price 88.5. Fail answers reading a different week's row."),
17: ("Verify the agent browsed the industry overview, opened the Internet "
     "industry page, and opened 'Number of internet and social media users in "
     "the United States' (statistic 1044012). The answer must state 324 million "
     "internet users and 254 million social media users as of October 2025, and "
     "the release/update date Mar 18, 2026. Fail answers with swapped figures."),
18: ("Verify the agent opened 'Year-on-year audience growth of selected social "
     "media platforms' (statistic 1294062). The answer must state Pinterest grew "
     "fastest at +67.3 percent, X/Twitter shrank the most at -20.1 percent, and "
     "three platforms grew by more than 15 percent (Pinterest 67.3%, TikTok "
     "20.0%, Reddit 17.2%). Fail answers counting two or four platforms."),
19: ("Verify the agent opened 'Global retail e-commerce sales 2022-2030' "
     "(statistic 379046) and the pricing page. The answer must state Statista "
     "requires a paid account (Starter Account or higher) to see the exact "
     "figures, and that the Starter, Personal and Professional Accounts include "
     "premium statistics. Fail answers claiming the Basic Account includes "
     "premium statistics."),
20: ("Verify the agent logged in as david.k@test.com, opened the 'Artificial "
     "intelligence (AI) worldwide' topic page (topic 3104), and saved the "
     "editor's pick 'Market size of AI worldwide' (forecast 1474143) to david's "
     "favorites. The answer must state the global AI market size of 617.62bn USD "
     "and the generative AI market size for 2025 of 63bn U.S. dollars from the "
     "key insights. Fail answers that swap the two figures."),
21: ("Verify the agent submitted the contact form with the name 'Dana White' "
     "and email dana.white@example.com, and opened the Video gaming worldwide "
     "report (study 123559). The answer must confirm the site's thank-you "
     "message after submitting and state the video gaming report's current "
     "price of $495 USD. Fail answers with other prices or without the "
     "confirmation."),
22: ("Verify the agent checked the recently updated statistics and opened both "
     "'Average inflation rate worldwide from 1980 to 2031' (statistic 256598) "
     "and 'Annual global emissions of carbon dioxide 1940-2025' (statistic "
     "276629). The answer must state the inflation statistic's last update Aug "
     "13, 2026 and the CO2 statistic's April 2026, that the inflation statistic "
     "was refreshed more recently, and that both cover the Worldwide region. "
     "Fail answers with swapped dates."),
}


def main() -> int:
    lines = TASKS.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        row = json.loads(line)
        no = int(row["id"].split("--")[1])
        if "verifier_path" in row or "judge_rubric" in row:
            # strip previous append to stay idempotent on the 5-key prefix
            prefix = json.dumps({k: row[k] for k in
                                 ("web_name", "id", "ques", "web", "upstream_url")},
                                ensure_ascii=False)
            line = prefix[:-1]
        appended = (line.rstrip()[:-1]
                    + f', "verifier_path": "sites/statista/verify/verify_{no}.py",'
                    + f' "judge_rubric": {json.dumps(RUBRICS[no], ensure_ascii=False)}}}')
        # byte-identity of the 5-key prefix
        assert appended.startswith(line.rstrip()[:-1]), f"prefix changed for {row['id']}"
        out.append(appended)
    TASKS.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"appended verifier_path + judge_rubric to {len(out)} task rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
