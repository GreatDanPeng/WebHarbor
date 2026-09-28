#!/usr/bin/env python3
"""Generate verify_0.py … verify_22.py from the centralized TASKS ground-truth
table (review track). Ground truth is frozen from the review container's
deterministic seed (md5 d6302969…) and the reviewer's honest live walks.

Re-run:  python3 make_verifiers.py   (from sites/statista/verify/)
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

# gates: (name, url-regex) — navigation the task names (anti-shortcut).
# answers: (kind, name, value[, label]) with kind in {phrase, number}.
# state: None (read-only) or dict(new_user=..., fav_add=[(uid, stat, report)],
#        fav_del=[...], dl_add=(uid, stat, report, fmt))
TASKS = {
0: dict(
  gates=[("visited_search", r"/serp\?q=average\+inflation\+rate\+worldwide"),
         ("visited_statistic", r"/statistics/256598/"),
         ("visited_table_view", r"/statistics/256598/[^?]*\?chart=table"),
         ("visited_register", r"/register"),
         ("visited_favorites", r"/account/favorites")],
  answers=[("number", "inflation_2025", "4.13", "2025 average world inflation"),
           ("number", "inflation_2031", "3.2", "2031 forecast value"),
           ("phrase", "mentions_favorites", "favorites")],
  state=dict(new_user=("review.agent0@test.com", "review_agent0", "Review_Agent0"),
             fav_add=[(5, 256598, None)])),
1: dict(
  gates=[("visited_search", r"/serp\?q=most\+popular\+social\+networks"),
         ("visited_statistic", r"/statistics/272014/"),
         ("visited_downloads", r"/account/downloads")],
  answers=[("phrase", "top_network", "Facebook"),
           ("number", "mau_millions", "3,070", "monthly active users"),
           ("phrase", "download_format", "PNG"),
           ("phrase", "retrieval_location", "download")],
  state=dict(new_user=("review.agent1@test.com", "review_agent1", "Review_Agent1"),
             dl_add=(5, 272014, None, "png"))),
2: dict(
  gates=[("visited_search", r"/serp\?q=countries\+with\+the\+largest\+nominal\+GDP"),
         ("visited_statistic", r"/statistics/268173/"),
         ("visited_register", r"/register"),
         ("visited_favorites", r"/account/favorites")],
  answers=[("phrase", "top_economy", "United States"),
           ("number", "top_gdp", "32.38", "top economy GDP"),
           ("phrase", "germany_named", "Germany"),
           ("number", "germany_gdp", "5.45", "Germany GDP"),
           ("number", "difference", "26.93", "difference in trillion")],
  state=dict(new_user=("review.agent2@test.com", "review_agent2", "Review_Agent2"),
             fav_add=[(5, 268173, None)])),
3: dict(
  gates=[("visited_login", r"/login"),
         ("visited_search", r"/serp\?q=renewable\+energy\+capacity"),
         ("visited_statistic", r"/statistics/267233/"),
         ("visited_favorites", r"/account/favorites")],
  answers=[("phrase", "leading_country", "China"),
           ("number", "capacity_gw", "2,258.02", "installed capacity in GW"),
           ("phrase", "mentions_favorites", "favorites")],
  state=dict(fav_add=[(2, 267233, None)])),
4: dict(
  gates=[("visited_pricing", r"/pricing/"),
         ("visited_register", r"/register"),
         ("visited_account", r"/account")],
  answers=[("phrase", "cheapest_premium_plan", "Starter"),
           ("number", "starter_price", "199", "Starter price"),
           ("number", "professional_yearly", "2,388", "Professional yearly"),
           ("phrase", "personal_plan", "Personal"),
           ("phrase", "professional_plan", "Professional"),
           ("phrase", "registered_email", "frank.miller@test.com")],
  state=dict(new_user=("frank.miller@test.com", "frank_m", "Frank_M"))),
5: dict(
  gates=[("visited_search", r"/serp\?q=consumer\+trends\+2026"),
         ("visited_report", r"/study/206237/"),
         ("visited_gaming_report", r"/study/123559/")],
  answers=[("number", "pages", "37", "Consumer Trends pages"),
           ("phrase", "release_year", "2025"),
           ("number", "price", "595", "report price"),
           ("phrase", "chapter1", "Consumer sentiment"),
           ("phrase", "chapter2", "Consumer spending and cautious optimism"),
           ("phrase", "chapter3", "How tariffs are shaping consumption"),
           ("number", "gaming_pages", "62", "video gaming pages"),
           ("phrase", "gaming_has_more", "video gaming")],
  state=None),
6: dict(
  gates=[("visited_outlook", r"/outlook/"),
         ("visited_mobility_segment", r"/outlook/mobility-markets/"),
         ("visited_ridehailing_market", r"/outlook/mmo/shared-mobility/ride-hailing/worldwide/")],
  answers=[("number", "revenue_2026", "188.60", "2026 revenue"),
           ("number", "volume_2030", "229.98", "2030 market volume"),
           ("phrase", "top_country", "China")],
  state=None),
7: dict(
  gates=[("visited_register", r"/register"),
         ("visited_search", r"/serp\?q=global\+CO2\+emissions"),
         ("visited_statistic", r"/statistics/276629/"),
         ("visited_table_view", r"/statistics/276629/[^?]*\?chart=table"),
         ("visited_favorites", r"/account/favorites")],
  answers=[("number", "recent_year_emissions", "38.11", "2025 CO2 level"),
           ("phrase", "recent_year", "2025"),
           ("phrase", "registered_username", "casey_r"),
           ("phrase", "saved_confirmation", "favorites")],
  state=dict(new_user=("casey.r@test.com", "casey_r", "Casey_R"),
             fav_add=[(5, 276629, None)])),
8: dict(
  gates=[("visited_search", r"/serp\?q=leading\+eSports\+games"),
         ("visited_statistic", r"/statistics/501853/"),
         ("visited_table_view", r"/statistics/501853/[^?]*\?chart=table")],
  answers=[("phrase", "top_game", "Counter-Strike 2"),
           ("number", "top_prize_pool", "18.97", "top prize pool"),
           ("phrase", "second_game", "Dota 2"),
           ("number", "second_prize_pool", "16.47", "second prize pool"),
           ("phrase", "third_game", "Fortnite"),
           ("number", "third_prize_pool", "12.91", "third prize pool")],
  state=None),
9: dict(
  gates=[("visited_search", r"/serp\?q=average\+inflation\+rate\+worldwide"),
         ("visited_statistic", r"/statistics/256598/"),
         ("visited_apa_citation", r"citation=APA"),
         ("visited_mla_citation", r"citation=MLA")],
  answers=[("phrase", "publisher", "Statista Research Department"),
           ("phrase", "cited_url", "https://www.statista.com/statistics/256598/global-inflation-rate-compared-to-previous-year/"),
           ("phrase", "survey_start", "01/01/1980"),
           ("phrase", "survey_end", "31/12/2031"),
           ("phrase", "apa_named", "APA"),
           ("phrase", "mla_named", "MLA")],
  state=None),
10: dict(
  gates=[("visited_search", r"/serp\?q=TikTok"),
         ("visited_topic", r"/topics/6077/"),
         ("visited_penetration_stat", r"/statistics/1299829/")],
  answers=[("number", "global_users", "1.99", "global users bn"),
           ("number", "brand_value", "75.67", "brand value bn USD"),
           ("phrase", "report_named", "TikTok"),
           ("phrase", "penetration_update_date", "Jun 12, 2026")],
  state=None),
11: dict(
  gates=[("visited_login", r"/login"),
         ("visited_downloads", r"/account/downloads"),
         ("visited_favorites", r"/account/favorites"),
         ("visited_statistic", r"/forecasts/1474143/")],
  answers=[("phrase", "recent_download_stat", "Market size of AI worldwide"),
           ("phrase", "download_format", "PNG"),
           ("phrase", "removed_from_favorites", "remove")],
  state=dict(fav_del=[(1, 1474143, None)])),
12: dict(
  gates=[("visited_search", r"/serp\?q=Instagram\+audience\+size"),
         ("visited_statistic", r"/statistics/578364/")],
  answers=[("phrase", "largest_country", "India"),
           ("number", "audience_millions", "480.55", "Instagram audience"),
           ("any", "countries_over_100m", ["3", "three"], "countries above 100M"),
           ("phrase", "release_date", "Oct 21, 2025")],
  state=None),
13: dict(
  gates=[("visited_search", r"/serp\?q=artificial\+intelligence"),
         ("visited_reports_filter", r"content_type=Reports"),
         ("visited_report", r"/study/50485/"),
         ("visited_login", r"/login"),
         ("visited_favorites", r"/account/favorites")],
  answers=[("number", "pages", "295", "AI report pages"),
           ("phrase", "release_date", "September 2025"),
           ("number", "price", "1,995", "AI report price"),
           ("phrase", "first_toc_entry", "Description"),
           ("phrase", "saved_with_carol", "carol")],
  state=dict(fav_add=[(3, None, 50485)])),
14: dict(
  gates=[("visited_search", r"/serp\?q=inflation\+rate\+selected\+global\+regions"),
         ("visited_statistic", r"/statistics/256626/")],
  answers=[("phrase", "highest_region", "Sub-Saharan Africa"),
           ("number", "highest_rate", "12.48", "highest inflation rate"),
           ("number", "eu_rate", "2.46", "EU inflation rate"),
           ("phrase", "survey_start", "01/01/2025"),
           ("phrase", "update_date", "Apr 15, 2026")],
  state=None),
15: dict(
  gates=[("visited_login", r"/login"),
         ("visited_report", r"/study/206237/"),
         ("visited_downloads", r"/account/downloads")],
  answers=[("phrase", "download_format", "PDF"),
           ("phrase", "prior_statistic", "renewable energy capacity"),
           ("phrase", "prior_format", "PPT")],
  state=dict(dl_add=(3, None, 206237, "pdf"))),
16: dict(
  gates=[("visited_search", r"/serp\?q=weekly\+oil\+prices\+Brent"),
         ("visited_statistic", r"/statistics/326017/"),
         ("visited_table_view", r"/statistics/326017/[^?]*\?chart=table")],
  answers=[("phrase", "recent_week", "Jul 21"),
           ("number", "brent_price", "91.47", "Brent price"),
           ("number", "wti_price", "84.91", "WTI price"),
           ("number", "opec_price", "88.5", "OPEC basket price")],
  state=None),
17: dict(
  gates=[("visited_industry_overview", r"/markets/"),
         ("visited_internet_industry", r"/markets/424/internet/"),
         ("visited_statistic", r"/statistics/1044012/")],
  answers=[("number", "internet_users", "324", "US internet users millions"),
           ("number", "social_users", "254", "US social media users millions"),
           ("phrase", "release_date", "Mar 18, 2026")],
  state=None),
18: dict(
  gates=[("visited_search", r"/serp\?q=year-on-year\+audience\+growth"),
         ("visited_statistic", r"/statistics/1294062/")],
  answers=[("phrase", "fastest_grower", "Pinterest"),
           ("number", "growth_pct", "67.3", "highest growth percent"),
           ("phrase", "biggest_shrinker", "X/Twitter"),
           ("number", "shrink_pct", "20.1", "largest decline percent"),
           ("any", "over_15pct_count", ["3", "three"], "platforms above 15 percent")],
  state=None),
19: dict(
  gates=[("visited_search", r"/serp\?q=global\+retail\+e-commerce\+sales"),
         ("visited_statistic", r"/statistics/379046/"),
         ("visited_pricing", r"/pricing/")],
  answers=[("phrase", "premium_requirement", "Starter"),
           ("phrase", "premium_word", "premium"),
           ("phrase", "personal_plan", "Personal"),
           ("phrase", "professional_plan", "Professional")],
  state=None),
20: dict(
  gates=[("visited_login", r"/login"),
         ("visited_topic", r"/topics/3104/"),
         ("visited_pick_statistic", r"/forecasts/1474143/"),
         ("visited_favorites", r"/account/favorites")],
  answers=[("number", "global_ai_market", "617.62", "global AI market size"),
           ("number", "gen_ai_market", "63", "generative AI market size"),
           ("phrase", "saved_confirmation", "favorites")],
  state=dict(fav_add=[(4, 1474143, None)])),
21: dict(
  gates=[("visited_contact", r"/contact/"),
         ("visited_gaming_report", r"/study/123559/")],
  answers=[("phrase", "inquiry_name", "Dana White"),
           ("phrase", "inquiry_email", "dana.white@example.com"),
           ("phrase", "confirmation", "sent"),
           ("number", "gaming_report_price", "495", "video gaming report price")],
  state=None),
22: dict(
  gates=[("visited_recent_stats", r"/recent/statistics/"),
         ("visited_inflation_search", r"/serp\?q=average\+inflation\+rate\+worldwide"),
         ("visited_inflation_stat", r"/statistics/256598/"),
         ("visited_co2_search", r"/serp\?q=global\+carbon\+dioxide"),
         ("visited_co2_stat", r"/statistics/276629/")],
  answers=[("phrase", "inflation_update_date", "Aug 13, 2026"),
           ("phrase", "co2_update_date", "April 2026"),
           ("phrase", "region_worldwide", "Worldwide"),
           ("phrase", "more_recent", "inflation")],
  state=None),
}

HEADER = '''#!/usr/bin/env python3
"""Verify {tid}.

{question}
"""
from verify_lib import (check_answer_any, check_answer_number, check_answer_phrase, check_read_only,
                        check_only_tables_changed, check_trajectory_identity,
                        check_visited_path, check_new_user, check_favorites_delta,
                        check_download_added, final_answer, run_verifier)

TASK_ID = "{tid}"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
{gates}
{answers}
{state}


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
'''

QUESTIONS = {}
for line in (HERE.parent / "tasks.jsonl").read_text().splitlines():
    row = __import__("json").loads(line)
    QUESTIONS[row["id"]] = row["ques"]


def gen_state_block(state):
    if state is None:
        return "    check_read_only(judge, initial_db, after_db)"
    lines = []
    allowed = set()
    if "new_user" in state:
        allowed.add("users")
    if "fav_add" in state or "fav_del" in state:
        allowed.add("favorites")
    if "dl_add" in state:
        allowed.add("download_events")
    allowed_s = ", ".join(f'"{t}"' for t in sorted(allowed))
    lines.append('    check_only_tables_changed(judge, initial_db, after_db, '
                 '{' + allowed_s + '})')
    if "new_user" in state:
        email, username, display = state["new_user"]
        lines.append(
            f'    check_new_user(judge, initial_db, after_db,\n'
            f'                    "{email}", "{username}", "{display}")')
    if "fav_add" in state or "fav_del" in state:
        adds = state.get("fav_add", [])
        dels = state.get("fav_del", [])
        adds_s = ", ".join(f"({a[0]}, {a[1]}, {a[2]})" for a in adds) or ""
        dels_s = ", ".join(f"({d[0]}, {d[1]}, {d[2]})" for d in dels) or ""
        lines.append(f'    check_favorites_delta(judge, initial_db, after_db,\n'
                     f'                        expect_added=[{adds_s}],\n'
                     f'                        expect_removed=[{dels_s}])')
    if "dl_add" in state:
        uid, sid, rid, fmt = state["dl_add"]
        lines.append(f'    check_download_added(judge, initial_db, after_db,\n'
                     f'                        user_id={uid}, stat_id={sid!r},\n'
                     f'                        report_id={rid!r}, fmt="{fmt}")')
    return "\n".join(lines)


def main():
    for no, spec in sorted(TASKS.items()):
        tid = f"Statista--{no}"
        gates = "\n".join(
            f'    check_visited_path(judge, traj, "{name}", r"{rx}")'
            for name, rx in spec["gates"])
        answers = []
        for a in spec["answers"]:
            if a[0] == "number":
                label = f", '{a[3]}'" if len(a) > 3 else ""
                answers.append(
                    f'    check_answer_number(judge, answer, "{a[1]}", "{a[2]}"{label})')
            elif a[0] == "any":
                label = f", '{a[3]}'" if len(a) > 3 else ""
                variants = ", ".join(f'"{v}"' for v in a[2])
                answers.append(
                    f'    check_answer_any(judge, answer, "{a[1]}", [{variants}]{label})')
            else:
                answers.append(
                    f'    check_answer_phrase(judge, answer, "{a[1]}", "{a[2]}")')
        body = HEADER.format(tid=tid, question=QUESTIONS[tid], gates=gates,
                             answers="\n".join(answers),
                             state=gen_state_block(spec["state"]))
        (HERE / f"verify_{no}.py").write_text(body)
    print(f"generated {len(TASKS)} verifiers")


if __name__ == "__main__":
    main()
