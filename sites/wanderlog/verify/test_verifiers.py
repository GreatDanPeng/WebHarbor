#!/usr/bin/env python3
"""test_verifiers.py — adversarial contract tests for the wanderlog verifier suite.

Guarantees (run with pytest):
  * each honest fixture (from the reviewer-r2's two independent
    Playwright rounds on the r2 review container wh-wanderlog-r2, seed md5
    b32e9905a17605ce9c983780764c9ee4) PASSES its verify_<n>.py;
  * every adversarial negative FAILS (zero false positives):
      - no-op trajectories (21),
      - answer-only shortcuts with no navigation (21),
      - wrong-answer trajectories (21, fabricated per question point),
      - stale-DB trajectories (all 9 stateful tasks),
      - read-only violations (unexpected DB writes on read-only tasks),
      - tampered packages (wrong task_id / off-site URL / cross-port /
        not-terminated / empty answer / bad PNG / pre-mutated seed),
      - task-specific confusions (wrong guide, swapped sources, swapped
        budget members, shuffled hotel order, swapped leaderboard counts).
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

VERIFY = Path(__file__).resolve().parent
EV = Path("/data/zhaoyang-user-projects/websyn/wh-wanderlog-rereview-evidence")
FIXTURES = EV / "r3" / "runs_round2"
# Wanderlog--16 was deepened on the audit rail (seventh-restaurant coordinates
# question point): its honest fixture is the audit walk run directory.
AUDIT_EV = Path("/data/zhaoyang-user-projects/websyn/wh-wanderlog-audit-evidence")
AUDIT_FIXTURES = {16: AUDIT_EV / "runs" / "task16"}


def fixture_for(n: int) -> Path:
    return AUDIT_FIXTURES.get(n, FIXTURES / str(n))
TMP = EV / "verify_runs" / "_pytest_tmp"
PY = sys.executable

TASK_IDS = [f"Wanderlog--{n}" for n in range(21)]
READ_ONLY = [n for n in range(21) if n not in (4, 5, 6, 7, 8, 9, 10, 15, 18)]
STATEFUL = [4, 5, 6, 7, 8, 9, 10, 15, 18]


def run_verifier(n: int, run_dir: Path):
    proc = subprocess.run(
        [PY, str(VERIFY / f"verify_{n}.py"), "--run_dir", str(run_dir)],
        capture_output=True, text=True, timeout=120)
    try:
        verdict = json.loads(proc.stdout)
    except json.JSONDecodeError:
        verdict = {"pass": False, "reason": proc.stdout[-300:] or proc.stderr[-300:]}
    return verdict


def clone(n: int, tag: str) -> Path:
    dst = TMP / f"{n}_{tag}"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(fixture_for(n), dst)
    return dst


def set_traj(run_dir: Path, **changes):
    p = run_dir / "trajectory.json"
    traj = json.loads(p.read_text())
    traj.update(changes)
    p.write_text(json.dumps(traj, indent=2))


def mutate_answer(run_dir: Path, new_answer: str):
    set_traj(run_dir, final_answer=new_answer)


def mutate_db(run_dir: Path, which: str, sql: str):
    db = sqlite3.connect(run_dir / which)
    db.execute(sql)
    db.commit()
    db.close()


def drop_nav(run_dir: Path):
    """Strip all step URLs down to the bare start page (no tool navigation)."""
    p = run_dir / "trajectory.json"
    traj = json.loads(p.read_text())
    start = traj["start_url"]
    for step in traj.get("steps", []):
        step["url"] = start
        step["url_after"] = start
    p.write_text(json.dumps(traj, indent=2))


# ---------------------------------------------------------------- happy path
@pytest.mark.parametrize("n", range(21))
def test_honest_fixture_passes(n):
    verdict = run_verifier(n, fixture_for(n))
    assert verdict["pass"], verdict["reason"]


# ---------------------------------------------------------------- no-op
@pytest.mark.parametrize("n", range(21))
def test_noop_fails(n):
    run_dir = clone(n, "noop")
    set_traj(run_dir, steps=[], final_answer="", terminated=False,
             termination_reason="max_steps")
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]


# ---------------------------------------------------------------- shortcuts
@pytest.mark.parametrize("n", range(21))
def test_answer_only_shortcut_fails(n):
    run_dir = clone(n, "shortcut")
    drop_nav(run_dir)
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]
    assert any("nav_" in e for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- wrong answers
WRONG = {
    0: ("The guide with the most places is 'Paris 5 Day Tourist Itinerary "
        "+Recommendations' by elisa (@alilies) — 177,509 views, 771 likes, "
        "distinction badge pro-only, and its only comment is by Alice Johnson "
        "dated 2026-09-18. Her profile shows 214 geos and 38 countries. Three "
        "guides match an Iceland search; the more-viewed one was edited "
        "2026-09-23 by @Julia_Jablonka, whose profile shows 107 geos. Sorting "
        "by recently edited puts 'Tokyo Food Guide' by @shogobusiness on top."),
    1: ("The attractions ranking is 'Top 50 things to do and attractions in "
        "Tokyo' covering 50 places. Ranked sixth and seventh: Ueno Park and "
        "Shinjuku Gyoen National Garden. The number-one attraction is cited "
        "by Times of India (#4) and Condé Nast Traveler (#5). Ueno Park's "
        "first tip: 'Visit during cherry blossom season'; categories [Park, "
        "Museums]; coordinates 35.7148, 139.7734. The cafes ranking 'The 50 "
        "best coffee shops in Tokyo' (49) tops with Fuglen Tokyo "
        "(35.6666, 139.6924) and Onibus Coffee ('Cocktails, coffee & "
        "Scandinavian baked goods'; Cafe, Coffee shop). The seventh-ranked "
        "restaurant Tempura Motoyoshi's categories: Tempura restaurant, "
        "Japanese restaurant."),
    2: ("Louvre Museum: About — 'A famous art museum in central Paris.' "
        "Wanderlog ranks it #2 in Attractions; categories [Tourist "
        "attraction, Monument]; coordinates 48.8530, 2.3500. It appears in "
        "'The 49 best free attractions in Paris' ranked #2 and 'Top 49 "
        "things to do' ranked #8. The attractions list ranks Notre-Dame "
        "first and Eiffel Tower third; the Louvre's first source is Condé "
        "Nast Traveler (#5). Eiffel Tower's first tip: 'Visit at night for "
        "the lights.' The free list's top two places are Jardin du "
        "Luxembourg ('17th-century park with formally laid-out gardens.') "
        "and Panthéon ('Neo-classical church housing a famous crypt.'), "
        "whose descriptions read as shown. The restaurants ranking's sixth "
        "entry Le Servan serves 'French-Asian dishes' (Restaurant, Bistro) "
        "and the seventh Mokonuts is 'Petite space rustling up imaginative "
        "breakfasts' (French restaurant, Restaurant)."),
    3: ("Day 1's first stop is Sainte-Chapelle at 14:30 for 60 minutes; the "
        "Septime note reads 'Tasting menu reserved for two.' The accepted "
        "collaborator is Carol Davis; dates 2027-05-10 to 2027-05-14, 3 "
        "travelers, badge Private. Septime's categories: [Seafood "
        "restaurant, Bar]; it appears in the free-attractions list ranked "
        "#1 with first source The Infatuation (#7). Day 4's first stop has "
        "categories [Church, Cathedral]. The budget shows Alice paid $232.50 "
        "and Bob paid $1,704.20, settling with 'Alice Johnson owes Bob Chen "
        "$735.85'. The undone to-do is 'Pre-book Sky Lagoon slots'; the "
        "share link is parisinspring; Bob's profile shows 23 geos."),
    4: "The new stop now lists on the Day 2 · Oct 18 card; Day 1 has 3 stops after adding it. The trip's sharing badge is Private.",
    5: ("Day 1's first stop was Sainte-Chapelle (of 3). After moving it down "
        "and removing the stop that became first, the confirmation read "
        "'Stop moved.' The new first stop is Eiffel Tower at 17:30; 3 stops "
        "remain and Musée d'Orsay is now second. After adding the Arc de "
        "Triomphe at 10:00 for 45 minutes with note 'Photo stop', the final "
        "Day 1 order is Eiffel Tower → Arc de Triomphe → Musée d'Orsay, and "
        "the collaborator badge shows Pending."),
    6: ("4 of 4 packing items are done. The unfinished packing item is "
        "'Aurora forecast app' and the unfinished to-do is 'Pre-book Sky "
        "Lagoon slots'. After adding 'Aurora forecast app' to the packing "
        "list and marking it done, the to-dos read 1 of 3 done. After "
        "adding 'Thermal base layers' and marking it done, the final "
        "packing count is 5 of 5."),
    7: ("The Iceland Ring Road budget totals $2,204.50; Dana paid $1,105.50 "
        "and Bob paid $1,099.00, settling with 'Bob Chen owes Dana Kim "
        "$3.25'; Transport totals $890.00. After recording the two Transport "
        "expenses for 2026-11-08 (fuel $87.30 by Dana, parking $12.50 by "
        "Alice), the new total is $2,204.50, Dana paid $1,186.30, Bob paid "
        "$1,118.00, and the settlement reads 'Dana Kim owes Bob Chen "
        "$34.15'."),
    8: "The invitation produced the confirmation 'Invitation sent to Bob.' After Carol accepted, the planner shows Day 2's first stop as Septime at 19:30, with trip owner Bob Chen.",
    9: ("The trip's current privacy is Public and the share link is "
        "nycfoodcrawl; it spans 4 days. After the change the planner shows "
        "'Day 5 · Dec 8'. The shared page shows 'NYC Food Crawl' with Day 2 "
        "stops Katz's Delicatessen at 12:30 and Rubirosa at 17:30, and Day "
        "3's second stop note 'Tie-dye pizza.' Rubirosa's categories: [Pizza "
        "restaurant, Pasta shop]; it is ranked #6 on the NYC restaurants "
        "list with first source Female Foodie (#15)."),
    10: "Wanderlog creates the section headings 'Day 1' and 'Day 2'. After adding the new section, the planner shows 4 sections.",
    11: ("The map draws 9 pins; pin 1 to pin 2 is 2.1 km (1.3 mi); pin 1's "
         "coordinates 48.8554, 2.3450. Pin 4 is Septime on Day 3 and the "
         "last pin is Bistrot Paul Bert. The budget's Lodging total is "
         "$860.00 and Food $14,200.00. The pin-1 place's admission and "
         "first tip: 'Book tickets in advance'. Clamato's categories: "
         "[Seafood restaurant, Sushi bar]; it is ranked #2 on the Paris "
         "restaurants list with first source Eater (#12). The collaborator "
         "shows 23 geos."),
    12: ("The hotel search page's main heading is 'Find hotels and Airbnbs' "
         "and its first feature block is 'Never miss a price drop'. The "
         "Paris list 'Best hotels in Paris' (49) ranks Le Meurice, Ritz "
         "Paris, Shangri-La Paris, Le Bristol Paris and The Peninsula Paris "
         "first through fifth. Shangri-La Paris: 'Elegant rooms & suites in "
         "a luxe lodging.' (Spa; 48.8681, 2.3289). Ritz Paris: 'Renowned "
         "luxury hotel.' Le Meurice: 'Opulent quarters in a regal hotel.' "
         "Rome's list 'Best hotels in Rome' (50) tops with Hotel Eden and "
         "J.K. Place Roma, both 'High-end hotel featuring an acclaimed "
         "restaurant with a garden, plus a bar & a spa.'"),
    13: ("The matching traveler is Lizzy S (@LizzyS): 265 geos, 53 "
         "countries, 3 followers, 980 following, no Pro badge, 2 guides. "
         "Her guide shows 93,144 views and 282 likes, edited 2024-01-07; "
         "its first section with places is 'General tips' and its comments "
         "are by Brandon Jackson (2026-09-24) and Dana Kim (2026-09-19), "
         "whose profiles show 4 and 9 geos. Searching 'rachel' matches 3 "
         "profiles (Rachel IRL, Rachel Lang, Rachel Zoe); Rachel Lang shows "
         "46 geos and her guide 1,910 views with commenter alice.j at 42 "
         "geos."),
    14: ("Destinations board: top traveler Los compas Niñis with 3526 geos; "
         "second Muhammad Baqi El Vatikan with 1787. Countries board: top "
         "traveler Muhammad Baqi El Vatikan with 219 countries. The "
         "usernames in the top three of both boards are ron1968 and tkerr. "
         "Third on the destinations board: Tyler Kerr with 1414. LizzyS's "
         "profile shows 53 geos, 38 countries and 1 guide. Her most-viewed "
         "guide 'London Guide' shows 33,965 views, 377 likes, edited "
         "2024-09-14; its Statue of Liberty place reads 'Iconic National "
         "Monument opened in 1886.', ranked #3 on the NYC attractions list "
         "with first source Time Out (#11). The 'maru' profile shows 74 "
         "countries and two guides with 1,910 and 3,215 views."),
    15: ("The guide showed 225 likes before; after liking it shows 226. "
         "The comment is displayed with the date 2026-09-28. The author, "
         "Shogo Akiyama (@shogobusiness), shows 55 geos and 10 countries. "
         "The other commenter, dana.k, shows 4 geos and one public trip, "
         "'Tokyo Weekend'."),
    16: ("Rome's restaurants ranking is 'Where to eat: the 50 best "
         "restaurants in Rome' (49 upstream); sixth and seventh are "
         "Retrobottega and SantoPalato, and the fourth's first source is "
         "The Telegraph (#17). Armando al Pantheon: 'A modern eatery near "
         "the Pantheon' (Restaurant, Caterer). Roscioli: 'Bustling "
         "destination with an eatery serving Italian fare.' (Roman "
         "restaurant, Italian restaurant). The seventh restaurant "
         "Retrobottega sits at coordinates 41.8956, 12.4769. The "
         "attractions ranking 'Top 50 things to do and attractions in "
         "Rome' (50) ranks Saint Peter's Basilica sixth and Piazza Navona "
         "seventh; the top attraction Colosseum reads 'Iconic temple built "
         "circa 118' (coordinates 41.8902, 12.4922). The hotels ranking "
         "'Best hotels in Rome' (50) tops with Hotel Eden ('High-end hotel "
         "featuring an acclaimed restaurant')."),
    17: ("Dana Kim (@dana.k) shows 4 geos and 9 countries. Her public trip "
         "'Rome Essentials' runs 2026-10-17 to 2026-10-19; Day 2 plans "
         "Sistine Chapel at 08:30, Saint Peter's Basilica at 11:30 and "
         "Roscioli at 13:30 (note 'Best pizza al taglio near the "
         "Vatican.'); members are Dana Kim and Bob Chen; the total budget "
         "is $1,462.00. Day 1's first stop Colosseum: 'Iconic temple built "
         "circa 118' (Historical landmark, Sights & Landmarks), ranked #2 "
         "with first source Time Out (#6). The third stop Spanish Steps: "
         "'Aqueduct-fed rococo fountain', ranked #1 (Condé Nast Traveler, "
         "#17). The other member, Bob Chen, shows 6 geos; his public trip "
         "'Iceland Ring Road' has Day 1's first stop Sky Lagoon."),
    18: "The new stop shows on the Day 2 · Apr 11 card, which now has 3 stops. The packing-list progress line reads: Packing: 4 / 5 done.",
    19: ("Three guides match a London search. The most-viewed one is "
         "'London Guide' with 33,965 views — by @LizzyS, 377 likes, edited "
         "2024-09-14. Its Tate Modern place reads 'Modern-art gallery with "
         "international works', ranked #2 on the London attractions list "
         "with first source Time Out (#25). LizzyS's profile shows 265 "
         "geos and 0 countries. The other guide 'Slices of London' is by "
         "@taraabraham with 42,922 views, edited 2022-04-01, first section "
         "with places 'Central London'; Tara shows 92 geos, 3 followers "
         "and 714 following."),
    20: ("Tokyo's destination line reads 'Japan · city · popularity "
         "251,550'; the chips linking to ranked lists are Photo spots, "
         "Bars and Museums; the first two nearby destinations are Minato "
         "and Bunkyo; the fifth place in each top-picks section is Sensō-ji "
         "and L'Effervescence. The attractions ranking 'Top 50 things to do "
         "in Tokyo' ranks Imperial Palace eighth and Ghibli Museum ninth; "
         "the eighth reads 'Sprawling wholesale fish market.' The cafes "
         "ranking tops with Onibus Coffee (35.6432, 139.6980). The hotels "
         "ranking 'Best hotels in Tokyo' tops with The Ritz-Carlton, Tokyo "
         "('Luxe quarters with city views.'; first source Travel + Leisure "
         "#11). The restaurants ranking tops with SÉZANNE, first cited "
         "source Fodors Travel Guide (#19)."),
}


@pytest.mark.parametrize("n", range(21))
def test_wrong_answer_fails(n):
    run_dir = clone(n, "wrong")
    mutate_answer(run_dir, WRONG[n])
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]


# ---------------------------------------------------------------- stale DB (stateful)
@pytest.mark.parametrize("n", STATEFUL)
def test_stale_db_fails(n):
    """Stateful task with NO DB change (agent self-reported but never acted)."""
    run_dir = clone(n, "stale")
    shutil.copyfile(run_dir / "initial.db", run_dir / "after.db")
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]
    assert any("db_" in e for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- read-only violations
@pytest.mark.parametrize("n", [0, 2, 12, 14])
def test_read_only_violation_fails(n):
    """Read-only task whose DB acquired an unexpected write."""
    run_dir = clone(n, "dirty")
    mutate_db(run_dir, "after.db",
              "INSERT INTO users (email, username, display_name, password_hash, "
              "created_at) VALUES ('sneaky@test.com','sneaky','Sneaky','x','2026-09-29')")
    verdict = run_verifier(n, run_dir)
    assert not verdict["pass"]
    assert any("db_read_only" in e for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- tampered packages
def test_tampered_task_id_fails():
    run_dir = clone(2, "tampered_id")
    set_traj(run_dir, task_id="Wanderlog--0")
    verdict = run_verifier(2, run_dir)
    assert not verdict["pass"]


def test_tampered_offsite_url_fails():
    run_dir = clone(1, "offsite")
    set_traj(run_dir, start_url="https://wanderlog.com/")
    verdict = run_verifier(1, run_dir)
    assert not verdict["pass"]


def test_tampered_cross_port_fails():
    run_dir = clone(3, "crossport")
    p = run_dir / "trajectory.json"
    traj = json.loads(p.read_text())
    for step in traj["steps"]:
        step["url"] = step["url"].replace(":46113", ":48113")
        if "url_after" in step:
            step["url_after"] = step["url_after"].replace(":46113", ":48113")
    p.write_text(json.dumps(traj, indent=2))
    verdict = run_verifier(3, run_dir)
    assert not verdict["pass"]


def test_tampered_not_terminated_fails():
    run_dir = clone(7, "notterm")
    set_traj(run_dir, terminated=False, termination_reason="max_steps")
    verdict = run_verifier(7, run_dir)
    assert not verdict["pass"]


def test_tampered_empty_answer_fails():
    run_dir = clone(11, "emptyans")
    mutate_answer(run_dir, "")
    verdict = run_verifier(11, run_dir)
    assert not verdict["pass"]


def test_tampered_bad_png_fails():
    run_dir = clone(13, "badpng")
    victim = run_dir / "screenshots" / "step_001.png"
    if victim.exists():
        victim.write_bytes(b"not a png at all")
    verdict = run_verifier(13, run_dir)
    assert not verdict["pass"]


def test_tampered_seed_fails():
    """A pre-mutated initial DB must fail the seed identity gate."""
    run_dir = clone(5, "premutated")
    mutate_db(run_dir, "initial.db",
              "INSERT INTO users (email, username, display_name, password_hash, "
              "created_at) VALUES ('pre@test.com','pre','Pre','x','2026-09-29')")
    verdict = run_verifier(5, run_dir)
    assert not verdict["pass"]
    assert any("seed_" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_wrong_stateful_row_fails():
    """T4's added stop recorded with the wrong place (Eiffel Tower id 161)."""
    run_dir = clone(4, "wrongplace")
    mutate_db(run_dir, "after.db",
              "UPDATE trip_entries SET place_id=161 WHERE place_id=126")
    verdict = run_verifier(4, run_dir)
    assert not verdict["pass"]
    assert any("db_entry_added" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t7_wrong_amount_fails():
    """T7's fuel expense recorded with the wrong amount."""
    run_dir = clone(7, "wrongamount")
    mutate_db(run_dir, "after.db",
              "UPDATE expenses SET amount_cents=7830 WHERE description='Fuel'")
    verdict = run_verifier(7, run_dir)
    assert not verdict["pass"]
    assert any("db_both_added" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t9_wrong_privacy_fails():
    """T9's trip flipped to public instead of link."""
    run_dir = clone(9, "wrongpriv")
    mutate_db(run_dir, "after.db", "UPDATE trips SET privacy='public' WHERE id=4")
    verdict = run_verifier(9, run_dir)
    assert not verdict["pass"]
    assert any("db_privacy_link" in e for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t15_unliked_fails():
    """T15's like row missing: DB unchanged (stale) while the answer claims 227."""
    run_dir = clone(15, "unliked")
    shutil.copyfile(run_dir / "initial.db", run_dir / "after.db")
    verdict = run_verifier(15, run_dir)
    assert not verdict["pass"]
    assert any("db_" in e for e in verdict["evidence"] if e.startswith("FAIL"))


# ---------------------------------------------------------------- task confusions
def test_t0_wrong_guide_confusion_fails():
    run_dir = clone(0, "parisguide")
    mutate_answer(run_dir,
                  "The guide with the most places is 'Paris 5 Day Tourist "
                  "Itinerary +Recommendations' — 177,509 views, 771 likes, "
                  "distinction badge pro-only. Author: elisa (@alilies). Its "
                  "Tokyo animal cafes section starts with Harajuku Owl Forest. "
                  "Its only comment is by Carol Davis dated 2026-09-21. "
                  "Profile: 214 visited geos, 38 countries. One guide matches "
                  "an Iceland search; the more-viewed match was edited "
                  "2026-09-23 by @rachelirl_ (140 geos). The recently-edited "
                  "top guide is 'Tokyo Food Guide' by @lgtwsokjcd.")
    verdict = run_verifier(0, run_dir)
    assert not verdict["pass"]


def test_t1_swapped_sources_fails():
    run_dir = clone(1, "swapsrc")
    mutate_answer(run_dir,
                  "The Tokyo attractions ranking is 'Top 49 things to do and "
                  "attractions in Tokyo' covering 49 places. Ranked sixth and "
                  "seventh: Ueno Park and Shinjuku Gyoen National Garden. The "
                  "number-one attraction is cited by Times of India (#4) and "
                  "Condé Nast Traveler (#5). Shinjuku Gyoen's first tip: "
                  "'Visit during cherry blossom season in spring or autumn "
                  "for vibrant foliage colors'; categories [Garden, Nature & "
                  "Parks]; coordinates 35.6852, 139.7101. Ueno Park: 'Popular "
                  "city park featuring ample walking paths, a lake with boat "
                  "rentals, a zoo & several museums.' The cafes ranking tops "
                  "with Fuglen Tokyo and Onibus Coffee. Butagumi's categories: "
                  "[Tonkatsu restaurant, Restaurant].")
    verdict = run_verifier(1, run_dir)
    assert not verdict["pass"]
    assert any("src1_assoc" in e or "src2_assoc" in e or "ranks_6_7" in e
               for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t3_budget_confusion_fails():
    """Swapped member paid amounts and reversed settlement direction."""
    run_dir = clone(3, "badbudget")
    mutate_answer(run_dir,
                  "Day 1's first stop is Musée d'Orsay at 10:00 for 120 "
                  "minutes. The Septime stop carries the note 'Reserved — "
                  "tasting menu.' Accepted collaborator: Bob Chen. Dates "
                  "2027-04-10 to 2027-04-13, 2 travelers, sharing badge "
                  "Link. Septime's categories: Fine dining restaurant, "
                  "Bistro; it appears in the Paris restaurants list ranked #1 "
                  "with first source The Infatuation (#7). Day 4's first "
                  "stop's categories: Basilica, Sights & Landmarks. The "
                  "budget shows Alice paid $232.50 and Bob paid $1,704.20, "
                  "settling with 'Alice Johnson owes Bob Chen $735.85'. The "
                  "checklist's undone to-do is 'Check gravel-road coverage "
                  "on rental'; the share link is parisinspringv; the second "
                  "member shows 17 geos.")
    verdict = run_verifier(3, run_dir)
    assert not verdict["pass"]
    assert any("alice_paid" in e or "bob_paid" in e or "settlement" in e
               for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t12_hotel_order_confusion_fails():
    run_dir = clone(12, "hotelorder")
    mutate_answer(run_dir,
                  "The hotel search page's main heading is 'Search for hotel "
                  "and Airbnb stays in one place' and its first feature block "
                  "is 'All-in-one hotel search'. Choosing Paris: the ranked "
                  "list is 'The 50 best hotels in Paris' (50); hotels ranked "
                  "first through fifth: Le Meurice, Ritz Paris, Shangri-La "
                  "Paris, The Peninsula Paris, Four Seasons Hotel George V, "
                  "Paris. First hotel's description: Elegant rooms & suites "
                  "in a luxe lodging offering Eiffel Tower views, a renowned "
                  "restaurant & a spa. Its first category: Hotel. Rome's list "
                  "'The 49 best hotels in Rome' (49) tops with Hotel Eden "
                  "and Hotel de Russie, a Rocco Forte hotel.")
    verdict = run_verifier(12, run_dir)
    assert not verdict["pass"]
    assert any("top5_order" in e or "rome_top2" in e
               for e in verdict["evidence"] if e.startswith("FAIL"))


def test_t14_leaderboard_swap_fails():
    run_dir = clone(14, "lbswap")
    mutate_answer(run_dir,
                  "Destinations board: top traveler Los compas Niñis with "
                  "3526 geos; second Muhammad Baqi El Vatikan with 1787. "
                  "Countries board: top traveler Muhammad Baqi El Vatikan "
                  "with 219 countries. The usernames in the top three of "
                  "both boards are ron1968 and tkerr. Third on the "
                  "destinations board: Tyler Kerr with 1414. LizzyS's "
                  "profile shows 265 geos, 53 countries and 1 guide; her "
                  "most-viewed guide 'London Guide' shows 33,965 views. The "
                  "'maru' profile shows 74 geos and two guides with 1,910 "
                  "and 3,215 views.")
    verdict = run_verifier(14, run_dir)
    assert not verdict["pass"]
    assert any(e.startswith("FAIL") for e in verdict["evidence"])
