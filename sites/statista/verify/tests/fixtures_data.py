"""Frozen per-task fixture specs for the statista verifier tests (review track).

URLs and honest answers come from the reviewer's live honest walks against the
review container (wh-statista-review @ http://localhost:46095, deterministic
seed md5 d6302969…). MUTATIONS reproduces the exact stateful writes the
application performs (registered users get id 5; favorites/download ids follow
the seed's 15/12 rows). No LLM."""

BASE = "http://localhost:46095"

SPECS = {
    0: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=average+inflation+rate+worldwide', 'http://localhost:46095/statistics/256598/global-inflation-rate-compared-to-previous-year/', 'http://localhost:46095/statistics/256598/global-inflation-rate-compared-to-previous-year/?chart=table', 'http://localhost:46095/login?next=%2Ffavorite%2Fstat%2F256598', 'http://localhost:46095/register', 'http://localhost:46095/account', 'http://localhost:46095/statistics/256598/global-inflation-rate-compared-to-previous-year/', 'http://localhost:46095/statistics/256598/global-inflation-rate-compared-to-previous-year/?chart=line', 'http://localhost:46095/account/favorites'],
        answer="The average world inflation rate for 2025 was 4.13 percent and the forecast value for 2031 is 3.2 percent. I saved the statistic 'Average inflation rate worldwide from 1980 to 2031' to my Statista favorites (it appears under my account > favorites).",
    ),
    1: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=most+popular+social+networks', 'http://localhost:46095/statistics/272014/global-social-networks-ranked-by-number-of-users/', 'http://localhost:46095/statistics/272014/global-social-networks-ranked-by-number-of-users/?chart=table', 'http://localhost:46095/login?next=%2Fdownload%2Fstat%2F272014', 'http://localhost:46095/register', 'http://localhost:46095/account', 'http://localhost:46095/statistics/272014/global-social-networks-ranked-by-number-of-users/', 'http://localhost:46095/account/downloads'],
        answer='The most popular social network worldwide is Facebook* with about 3,070 million monthly active users (October 2025). I downloaded the statistic as a PNG with my account; the download can be retrieved later in my Statista account under the download history (Account > Downloads).',
    ),
    2: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=countries+with+the+largest+nominal+GDP', 'http://localhost:46095/statistics/268173/countries-with-the-largest-gross-domestic-product-gdp/', 'http://localhost:46095/statistics/268173/countries-with-the-largest-gross-domestic-product-gdp/?chart=table', 'http://localhost:46095/login?next=%2Ffavorite%2Fstat%2F268173', 'http://localhost:46095/register', 'http://localhost:46095/account', 'http://localhost:46095/statistics/268173/countries-with-the-largest-gross-domestic-product-gdp/', 'http://localhost:46095/statistics/268173/countries-with-the-largest-gross-domestic-product-gdp/?chart=bar', 'http://localhost:46095/account/favorites'],
        answer="The top economy is the United States with a projected nominal GDP of 32.38 trillion U.S. dollars in 2026; Germany's GDP is 5.45 trillion. The U.S. economy is larger, by 26.93 trillion U.S. dollars. I saved the statistic to my Statista favorites so the deck's sources are traceable.",
    ),
    3: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/login', 'http://localhost:46095/account', 'http://localhost:46095/', 'http://localhost:46095/serp?q=renewable+energy+capacity+by+country', 'http://localhost:46095/statistics/267233/renewable-energy-capacity-worldwide-by-country/', 'http://localhost:46095/statistics/267233/renewable-energy-capacity-worldwide-by-country/?chart=table', 'http://localhost:46095/account/favorites'],
        answer="Using bob.c@test.com's account: China leads in installed renewable energy capacity worldwide with 2,258.02 gigawatts (2025). I added the statistic 'Leading countries in installed renewable energy capacity worldwide in 2025' to his favorites.",
    ),
    4: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/pricing/', 'http://localhost:46095/register', 'http://localhost:46095/account'],
        answer='The cheapest plan that includes premium statistics is the Starter Account at $199 USD per month (billed annually). The Professional Account costs $2,388 USD per year. According to the pricing page, the Personal Account and the Professional Account include report access. I registered the free Basic Account for frank.miller@test.com (username frank_m) so the team can start with the free statistics today.',
    ),
    5: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=consumer+trends+2026', 'http://localhost:46095/study/206237/consumer-trends-2026/', 'http://localhost:46095/study/123559/video-gaming-worldwide/'],
        answer="The Consumer Trends 2026 report has 37 pages, was released in 2025, and costs $595 USD. The first three chapters in its table of contents are 'Consumer sentiment', 'Consumer spending and cautious optimism', and 'How tariffs are shaping consumption'. The video gaming report has 62 pages, so it has more pages than Consumer Trends 2026.",
    ),
    6: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/outlook/', 'http://localhost:46095/outlook/mobility-markets/', 'http://localhost:46095/outlook/mmo/shared-mobility/ride-hailing/worldwide/'],
        answer='Statista Market Insights projects worldwide ride-hailing revenue of US$188.60bn in 2026 and a market volume of US$229.98bn by 2030, with China expected to generate the most revenue.',
    ),
    7: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/register', 'http://localhost:46095/account', 'http://localhost:46095/', 'http://localhost:46095/serp?q=global+CO2+emissions', 'http://localhost:46095/statistics/276629/global-co2-emissions/', 'http://localhost:46095/statistics/276629/global-co2-emissions/?chart=table', 'http://localhost:46095/account/favorites'],
        answer="I registered the free account casey.r@test.com (username casey_r). The most recent year shown for annual global CO2 emissions is 2025 with 38.11 billion metric tons. After saving the statistic to my favorites it appears in my new account's favorites list.",
    ),
    8: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=leading+eSports+games', 'http://localhost:46095/statistics/501853/leading-esports-games-worldwide-total-prize-pool/', 'http://localhost:46095/statistics/501853/leading-esports-games-worldwide-total-prize-pool/?chart=table'],
        answer='The video game with the biggest cumulative eSports prize pool is Counter-Strike 2 with 18.97 million U.S. dollars; second is Dota 2 with 16.47 million. The table view confirms the third-placed game, Fortnite, with 12.91 million U.S. dollars.',
    ),
    9: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=average+inflation+rate+worldwide', 'http://localhost:46095/statistics/256598/global-inflation-rate-compared-to-previous-year/', 'http://localhost:46095/statistics/256598/global-inflation-rate-compared-to-previous-year/?citation=APA', 'http://localhost:46095/statistics/256598/global-inflation-rate-compared-to-previous-year/?citation=MLA&chart=line'],
        answer='APA: Statista Research Department. (2026). Average inflation rate worldwide from 1980 to 2031. Statista. https://www.statista.com/statistics/256598/global-inflation-rate-compared-to-previous-year/ — the publisher is the Statista Research Department and the cited URL is the statistic\'s statista.com URL. MLA: Statista Research Department. "Average inflation rate worldwide from 1980 to 2031." Statista, Aug 13, 2026, https://www.statista.com/statistics/256598/global-inflation-rate-compared-to-previous-year/ The survey time period shown on the page is from 01/01/1980 to 31/12/2031.',
    ),
    10: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=TikTok', 'http://localhost:46095/topics/6077/tiktok/', 'http://localhost:46095/statistics/1299829/tiktok-penetration-worldwide-by-country/'],
        answer="Statista's TikTok topic page key insights: TikTok has about 1.99bn global users and a brand value of 75.67bn USD. The report Statista offers on this topic is the 'TikTok' report. The editor's pick 'TikTok penetration in selected countries and territories' was last updated Jun 12, 2026.",
    ),
    11: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/login', 'http://localhost:46095/account', 'http://localhost:46095/account/downloads', 'http://localhost:46095/account/favorites', 'http://localhost:46095/forecasts/1474143/global-ai-market-size/', 'http://localhost:46095/forecasts/1474143/global-ai-market-size/?chart=line', 'http://localhost:46095/account/favorites'],
        answer="Alice's most recent download is the statistic 'Market size of AI worldwide 2020-2032' (downloaded as PNG). It was saved in her favorites, so I removed it from there; her favorites list no longer shows it.",
    ),
    12: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=Instagram+audience+size', 'http://localhost:46095/statistics/578364/countries-with-most-instagram-users/', 'http://localhost:46095/statistics/578364/countries-with-most-instagram-users/?chart=table'],
        answer="India has the largest Instagram audience with 480.55 million users (October 2025). Three countries in the chart are above 100 million: India, the United States (181.75M) and Brazil (147.0M). The exact release/update date shown on the statistic's page is Oct 21, 2025.",
    ),
    13: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=artificial+intelligence', 'http://localhost:46095/serp?q=artificial%20intelligence&content_type=Reports', 'http://localhost:46095/study/50485/in-depth-report-artificial-intelligence/', 'http://localhost:46095/login', 'http://localhost:46095/account', 'http://localhost:46095/study/50485/in-depth-report-artificial-intelligence/', 'http://localhost:46095/account/favorites'],
        answer="Statista's in-depth market analysis of artificial intelligence has 295 pages, was released in September 2025, and costs $1,995 USD. The first entry in its table of contents is 'Description' (the visible contents list begins with the Description / Content / Tables headings). I saved the report to carol.d@test.com's favorites.",
    ),
    14: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=inflation+rate+selected+global+regions', 'http://localhost:46095/statistics/256626/inflation-rate-in-selected-global-regions/'],
        answer="In 2025 the region with the highest annual inflation rate was Sub-Saharan Africa at 12.48 percent; the European Union's rate was 2.46 percent. The statistic covers the survey period from 01/01/2025 to 31/12/2025 and its page shows last update Apr 15, 2026.",
    ),
    15: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/login', 'http://localhost:46095/account', 'http://localhost:46095/study/206237/consumer-trends-2026/', 'http://localhost:46095/account/downloads'],
        answer="With carol.d@test.com's Professional Account I downloaded the 'Consumer Trends 2026' report. Her download history shows that download in PDF format, and the other statistic she downloaded most recently before it is 'Leading countries in installed renewable energy capacity worldwide in 2025' (downloaded as PPT).",
    ),
    16: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=weekly+oil+prices+Brent', 'http://localhost:46095/statistics/326017/weekly-crude-oil-prices/', 'http://localhost:46095/statistics/326017/weekly-crude-oil-prices/?chart=table'],
        answer="For the most recent week shown (Jul 21 '26), the Brent price was 91.47 U.S. dollars per barrel, the WTI price for the same week was 84.91, and the OPEC basket price for that week was 88.5.",
    ),
    17: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/markets/', 'http://localhost:46095/markets/424/internet/', 'http://localhost:46095/statistics/1044012/us-digital-audience/', 'http://localhost:46095/statistics/1044012/us-digital-audience/?chart=table'],
        answer="From the Internet industry page: as of October 2025 the United States had 324 million internet users and 254 million social media users. The exact release/update date shown on the statistic's page is Mar 18, 2026.",
    ),
    18: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=year-on-year+audience+growth', 'http://localhost:46095/statistics/1294062/social-media-year-on-year-growth/', 'http://localhost:46095/statistics/1294062/social-media-year-on-year-growth/?chart=table'],
        answer='Pinterest grew fastest year-on-year with +67.3 percent audience growth; X/Twitter shrank the most (-20.1 percent). Three platforms in the chart grew by more than 15 percent (Pinterest 67.3%, TikTok 20.0%, Reddit 17.2%).',
    ),
    19: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/serp?q=global+retail+e-commerce+sales', 'http://localhost:46095/statistics/379046/worldwide-retail-e-commerce-sales/', 'http://localhost:46095/pricing/'],
        answer="The 'Global retail e-commerce sales 2022-2030' statistic is a premium statistic: Statista says you need a paid Statista Account (Starter Account or higher) to see the exact figures. The account types that include premium statistics are the Starter, Personal, and Professional Accounts.",
    ),
    20: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/login', 'http://localhost:46095/account', 'http://localhost:46095/', 'http://localhost:46095/serp?q=artificial+intelligence+worldwide', 'http://localhost:46095/topics/3104/artificial-intelligence-ai-worldwide/', 'http://localhost:46095/forecasts/1474143/global-ai-market-size/', 'http://localhost:46095/forecasts/1474143/global-ai-market-size/?chart=line', 'http://localhost:46095/account/favorites'],
        answer="From the 'Artificial intelligence (AI) worldwide' topic page key insights: the global AI market size is 617.62bn USD and the generative AI market size for 2025 is 63bn U.S. dollars. I saved the editor's pick 'Market size of AI worldwide 2020-2032' to david.k@test.com's favorites.",
    ),
    21: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/contact/', 'http://localhost:46095/serp?q=video+gaming', 'http://localhost:46095/study/123559/video-gaming-worldwide/'],
        answer="I sent Statista a contact inquiry with the name 'Dana White', the email dana.white@example.com, asking about volume licensing for the video gaming report. The site confirms: 'Thank you for your message.' The video gaming report currently costs $495 USD.",
    ),
    22: dict(
        urls=['http://localhost:46095/', 'http://localhost:46095/recent/statistics/', 'http://localhost:46095/serp?q=average+inflation+rate+worldwide', 'http://localhost:46095/statistics/256598/global-inflation-rate-compared-to-previous-year/', 'http://localhost:46095/serp?q=global+carbon+dioxide+emissions+worldwide', 'http://localhost:46095/statistics/276629/global-co2-emissions/'],
        answer="The most recently updated statistic about worldwide inflation is 'Average inflation rate worldwide from 1980 to 2031' (last update Aug 13, 2026, region Worldwide). The most recently updated global CO2 emissions statistic is 'Annual global emissions of carbon dioxide 1940-2025' (last update April 2026, region Worldwide). The inflation statistic was refreshed more recently.",
    ),
}

WRONG_ANSWERS = {
    0: 'The average world inflation rate for 2025 was 3.9 percent and the 2031 forecast is 4.4 percent.',
    1: 'The most popular social network is WhatsApp with 3,000 million monthly active users; I downloaded it as a PDF.',
    2: 'The top economy is China with 20.85 trillion; Germany is 4.5 trillion, so China is larger by 16.35 trillion.',
    3: 'The United States leads in installed renewable energy capacity with 467.92 gigawatts.',
    4: 'The cheapest premium plan is the Personal Account at $649; the Professional Account costs $1,199 per year.',
    5: 'Consumer Trends 2026 has 45 pages, released 2026, costs $495; first chapters are Overview, Method, Results. The gaming report has 51 pages.',
    6: 'Ride-hailing revenue for 2026 is US$154.2bn, market volume by 2030 US$188.6bn, with the United States generating the most revenue.',
    7: 'The most recent CO2 year shown is 2024 with 37.78 billion metric tons.',
    8: 'Dota 2 has the biggest cumulative eSports prize pool with 19.5 million U.S. dollars; Counter-Strike 2 is second with 15.2 million; the table view confirms Fortnite third with 11.4 million.',
    9: 'The publisher is IMF; the survey runs from 2000 to 2025.',
    10: 'TikTok has 2.5bn users and a brand value of 100bn USD; the report is Digital & Trends; the penetration stat was updated May 2, 2026.',
    11: "Alice's most recent download is 'Countries with the largest nominal GDP' as XLS; it was not in her favorites.",
    12: 'The United States has the largest Instagram audience with 181.75 million; two countries are above 100 million; released Sep 1, 2025.',
    13: 'The AI report has 250 pages, released March 2026, costs $2,388; the first chapter is Overview.',
    14: 'The region with the highest inflation is the European Union at 2.46 percent; Sub-Saharan Africa was 12.48 percent.',
    15: "The report download shows as XLS; the prior statistic download was 'Countries with the largest nominal GDP' as PNG.",
    16: "For the most recent week (Jul 14 '26) Brent was 85.21, WTI 79.34, OPEC basket 86.16.",
    17: 'The US had 307 million internet users and 245 million social media users in October 2025; released Jan 2, 2026.',
    18: 'TikTok grew fastest at 20 percent; Facebook shrank the most; two platforms grew above 15 percent.',
    19: 'Statista says you need a Personal Account to see the figures; only the Professional plan includes premium statistics.',
    20: 'The global AI market size is 63bn USD and the generative AI market is 617.62bn USD.',
    21: 'I sent the inquiry with the name Dana Smith and email dana.smith@example.com; the video gaming report costs $995 USD.',
    22: 'The inflation statistic was updated April 2026 and the CO2 statistic Aug 13, 2026, so CO2 is more recent; both cover the United States.',
}

MUTATIONS = {
    0: [
        "INSERT INTO users (id, email, username, display_name, password_hash, account_type, company, created_at) VALUES (5, 'review.agent0@test.com', 'review_agent0', 'Review_Agent0', '$2b$12$mTNQa9oqZyOoIJBpKN.0p.LVaApMSu9gZnYufEZrciM5QgBN7EM7u', 'Basic', '', '2026-09-26 12:00:00')",
        "INSERT INTO favorites (id, user_id, stat_id, report_id, created_at) VALUES (16, 5, 256598, NULL, '2026-09-26 12:00:00')",
    ],
    1: [
        "INSERT INTO users (id, email, username, display_name, password_hash, account_type, company, created_at) VALUES (5, 'review.agent1@test.com', 'review_agent1', 'Review_Agent1', '$2b$12$mTNQa9oqZyOoIJBpKN.0p.LVaApMSu9gZnYufEZrciM5QgBN7EM7u', 'Basic', '', '2026-09-26 12:00:00')",
        "INSERT INTO download_events (id, user_id, stat_id, report_id, fmt, created_at) VALUES (13, 5, 272014, NULL, 'png', '2026-09-26 12:00:00')",
    ],
    2: [
        "INSERT INTO users (id, email, username, display_name, password_hash, account_type, company, created_at) VALUES (5, 'review.agent2@test.com', 'review_agent2', 'Review_Agent2', '$2b$12$mTNQa9oqZyOoIJBpKN.0p.LVaApMSu9gZnYufEZrciM5QgBN7EM7u', 'Basic', '', '2026-09-26 12:00:00')",
        "INSERT INTO favorites (id, user_id, stat_id, report_id, created_at) VALUES (16, 5, 268173, NULL, '2026-09-26 12:00:00')",
    ],
    3: [
        "INSERT INTO favorites (id, user_id, stat_id, report_id, created_at) VALUES (16, 2, 267233, NULL, '2026-09-26 12:00:00')",
    ],
    4: [
        "INSERT INTO users (id, email, username, display_name, password_hash, account_type, company, created_at) VALUES (5, 'frank.miller@test.com', 'frank_m', 'Frank_M', '$2b$12$mTNQa9oqZyOoIJBpKN.0p.LVaApMSu9gZnYufEZrciM5QgBN7EM7u', 'Basic', '', '2026-09-26 12:00:00')",
    ],
    7: [
        "INSERT INTO users (id, email, username, display_name, password_hash, account_type, company, created_at) VALUES (5, 'casey.r@test.com', 'casey_r', 'Casey_R', '$2b$12$mTNQa9oqZyOoIJBpKN.0p.LVaApMSu9gZnYufEZrciM5QgBN7EM7u', 'Basic', '', '2026-09-26 12:00:00')",
        "INSERT INTO favorites (id, user_id, stat_id, report_id, created_at) VALUES (16, 5, 276629, NULL, '2026-09-26 12:00:00')",
    ],
    11: [
        'DELETE FROM favorites WHERE user_id = 1 AND stat_id = 1474143',
    ],
    13: [
        "INSERT INTO favorites (id, user_id, stat_id, report_id, created_at) VALUES (16, 3, NULL, 50485, '2026-09-26 12:00:00')",
    ],
    15: [
        "INSERT INTO download_events (id, user_id, stat_id, report_id, fmt, created_at) VALUES (13, 3, NULL, 206237, 'pdf', '2026-09-26 12:00:00')",
    ],
    20: [
        "INSERT INTO favorites (id, user_id, stat_id, report_id, created_at) VALUES (16, 4, 1474143, NULL, '2026-09-26 12:00:00')",
    ],
}

