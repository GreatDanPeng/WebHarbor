#!/usr/bin/env python3
"""test_verifiers.py — adversarial contract tests for the zara verifiers
(r2-synced review contract on orch/review/zara; ground truths frozen from
the reviewer's two independent re-review rounds).

Every case besides the honest fixtures is adversarial and MUST FAIL the
corresponding verifier (zero false positives):

  A. honest fixtures ......... 22 real r2 reviewer walks (runs_round2) -> PASS
  B. no-op runs .............. trajectory with zero steps + a canned
                               answer -> FAIL (navigation gates + identity)
  C. answer-only shortcuts ... terminated trajectory, correct-sounding
                               answer, but NO on-site navigation -> FAIL
  D. wrong answers ........... honest navigation, every anchored fact
                               falsified -> FAIL
  E. stale DB ................ honest run graded against a pre-mutated
                               initial DB -> FAIL (seed identity gate)
  F. injected writes ......... honest walk + an injected cart row in the
                               after DB -> FAIL (read-only or row-delta)
  G. tampered packages ....... wrong task_id / off-site URL / cross-port
                               URL / not terminated / empty answer /
                               bad PNG / deleted navigation -> FAIL
  H. state under-reach ....... honest walk graded against an after DB
                               missing or mutating the required state -> FAIL
"""
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
EV = Path("/data/zhaoyang-user-projects/websyn/wh-zara-audit-evidence")
HONEST = EV / "runs"


def honest(n):
    return HONEST / f"task{n}"
SEED_REF = EV / "seed_ref.db"
PY = sys.executable

TASK_IDS = [f"Zara--{n}" for n in range(22)]


def run_verifier(n, run_dir, extra=()):
    v = HERE / f"verify_{n}.py"
    out = subprocess.run([PY, str(v), "--run_dir", str(run_dir), *extra],
                         capture_output=True, text=True, timeout=120)
    try:
        payload = json.loads(out.stdout)
    except json.JSONDecodeError:
        payload = {"pass": False, "reason": out.stdout[-400:] + out.stderr[-400:]}
    return payload, out.returncode


def clone(run_src: Path, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(run_src, dest)
    return dest


def inject_cart_row(after_db):
    db = sqlite3.connect(after_db)
    db.execute("INSERT INTO cart_items (user_id, guest_token, product_id, color_id, size_id, "
               "quantity, added_at) VALUES (NULL, 'deadbeefdeadbeefdeadbeefdeadbeef', "
               "578162617, 1, 1, 1, '2026-09-29')")
    db.commit()
    db.close()


# ------------------------------------------------------------------ A. honest
@pytest.mark.parametrize("n", range(22))
def test_honest_fixture_passes(n):
    payload, code = run_verifier(n, honest(n))
    assert payload["pass"] is True, payload["reason"]
    assert code == 0


# ------------------------------------------------------------- B. no-op runs
@pytest.mark.parametrize("n", range(22))
def test_noop_run_fails(n, tmp_path):
    run = tmp_path / f"noop{n}"
    (run / "screenshots").mkdir(parents=True)
    (run / "initial.db").write_bytes(SEED_REF.read_bytes())
    (run / "after.db").write_bytes(SEED_REF.read_bytes())
    (run / "trajectory.json").write_text(json.dumps({
        "task_id": f"Zara--{n}", "start_url": "http://localhost:46114/",
        "steps": [], "terminated": True, "termination_reason": "agent_done",
        "final_answer": "I know this from memory: the answer is 533 upstream and "
                        "10 in the snapshot with everything in stock.",
    }))
    payload, code = run_verifier(n, run)
    assert payload["pass"] is False
    assert code == 1


# ---------------------------------------------------- C. answer-only shortcut
@pytest.mark.parametrize("n", range(22))
def test_answer_only_shortcut_fails(n, tmp_path):
    """Correct-sounding answer, zero navigation (knowledge shortcut)."""
    answers = {
        0: "533 upstream, 10 snapshot; BURGUNDY leaves the 100% LEATHER PUFFED-BODY DRESS at USD 459.00; "
           "BLACK leaves the CHIFFON HALTER MIDI DRESS WITH TIE; the USD 69.90 tie is the Z1975 DENIM MIDI "
           "HALTER DRESS and the ANIMAL PRINT DRAPED TULLE DRESS; Brown; XS in stock; 7957/576; subtotal "
           "USD 69.90, shipping USD 4.95, total USD 74.85; final line x2 at USD 139.80, total USD 144.75",
        1: "USD 229.00; 8100/038; WOMAN; DRESS; Ecru; XS, S, M, L all in stock at USD 229.00; SKU of S "
           "578162619; NEW · BAISI GUADAGNINO; wishlist four items; final three: DRAPED SEQUIN MIDI DRESS, "
           "100% CASHMERE CROPPED FIT CARDIGAN, ELONGATED SHOULDER BAG",
        2: "178 upstream, 10 snapshot; five bags under USD 60; USD 49.90; 3 colors Two-tone, Red, Black; "
           "ONE SIZE ONLY; RED SKU 545399255; BLACK SKU 545399257; total USD 54.85; OVAL USD 59.90, "
           "REF. 6214/810; final subtotal USD 99.80, total USD 104.75",
        3: "46 upstream, 10 snapshot; Ecru / Blue; USD 45.90; REF. 6096/811; 8-9 years low on stock; "
           "RUFFLED ROMANTIC DRESS USD 49.90 all COMING SOON; ULTRALIGHT WATER REPELLENT JACKET USD 39.80 "
           "x2 total USD 84.75; PINAFORE: PLEATED PINAFORE DRESS and TWILL POCKET PINAFORE",
        4: "543 results; BLUE 320, WHITE 39; USD 25.90 - 349.00; BASIC SLIM FIT JEANS, PRINTED LOOSE FIT "
           "JEANS, LIGHTWEIGHT REGULAR FIT JEANS; USD 49.90; 0774/333; 6 colors; 7 sizes; 34 (US 34) in "
           "stock; 38 filter leaves BASIC SLIM FIT JEANS and STRAIGHT-FIT JEANS; cheapest LIGHTWEIGHT "
           "REGULAR FIT JEANS; under 50 the same two",
        5: "49 results; Beige 9; USD 49.90 - 199.00; PLAID BELTED TRENCH COAT USD 129.00 Brown-Blue; "
           "XS low on stock; subtotal USD 174.90 then USD 220.80; order 80030000005 total USD 225.75; "
           "card ending 1111",
        6: "25 stores, 20 states, 21 options; ALA MOANA CENTER HONOLULU 10:00 - 20:00 US/Hawaii; 5 California "
           "stores; CENTURY CITY MALL Saturday 10:00 - 22:00; FASHION SHOW MALL US/Pacific; 2 New York "
           "stores; 5TH AV FLATIRON Saturday 10:00 - 21:00; latest close CENTURY CITY MALL",
        7: "SANTA MONICA PROMENADE 1338, THIRD STREET PROMENADE 8332472473; Saturday 10:00 - 21:00; Monday "
           "11:00 - 20:00; 250 POST ST SAN FRANCISCO STREET; Sunday 11:00 - 19:00 US/Pacific; 5TH AV "
           "FLATIRON Monday 10:00 - 21:00 OPEN; SOUTH COAST PLAZA MALL COSTA MESA Sunday 11:00 - 19:00",
        8: "5 California stores; SOUTH COAST PLAZA MALL COSTA MESA 92626; CENTURY CITY MALL LOS ANGELES "
           "Saturday 10:00 - 22:00; FASHION SQUARE MALL SCOTTSDALE America/Phoenix; ALA MOANA CENTER "
           "HONOLULU Sunday 10:00 - 20:00; DISNEY SPRINGS ORLANDO Saturday 10:00 - 23:30",
        9: "MIDI SCARF DRESS Ecru XS x1; LEATHER WIDE HEEL BOOTS Black 7½ x2; USD 587.00; USD 4.95; "
           "USD 591.95; then USD 408.00 / USD 412.95; boots remain; RED bag added; subtotal USD 278.80; "
           "orders 8004193147 and 8004128041; the delivered order holds SHOULDER PAD ZIP JACKET at "
           "USD 79.90 and 100% LEATHER PUFFED-BODY DRESS at USD 459.00",
        10: "MIDI SCARF DRESS x1, LEATHER WIDE HEEL BOOTS x2, ELONGATED SHOULDER BAG x1; subtotal USD "
            "636.80; order 80010000005; total USD 641.75; card ending 4242; WORK 425 W 14th St; 3 orders",
        11: "2 orders: 8004193147 2026-09-21 Shipped USD 223.95, 8004128041 2026-09-08 Delivered USD "
            "538.90; MIDI SCARF DRESS USD 229.00; card ending 4417; member since 2026-08-02; 3 saved "
            "items; 2 saved addresses; subtotal USD 816.00; HOME and WORK",
        12: "DRAPED SEQUIN MIDI DRESS 2026-09-20; 100% CASHMERE CROPPED FIT CARDIGAN 2026-09-22; ELONGATED "
            "SHOULDER BAG 2026-09-25; five items; final four; highest card price 100% CASHMERE CROPPED FIT "
            "CARDIGAN at USD 319.00; CHIFFON HALTER Black; REMOVE FROM WISHLIST",
        13: "order 80050000005; USD 233.95; MIDI SCARF DRESS Ecru XS x1 USD 229.00",
        14: "HOME — Bob Chen, 1810 N Sedgwick St, Unit 3, Chicago, IL 60614, 773-555-0137; SUMMER 900 Lake "
            "Shore Dr Chicago IL 60601 312-555-0199; SUMMER default; SUMMER remains",
        15: "ELONGATED SHOULDER BAG Two-tone ONE SIZE ONLY x1 USD 49.90; subtotal USD 49.90, shipping USD "
            "4.95, total USD 54.85; doubled USD 99.80 / USD 104.75; Your bag is empty; PLAID A-LINE DRESS "
            "x1 then x2 USD 91.80 / USD 96.75; RUFFLED ROMANTIC DRESS and CORDUROY LONG OVERALLS; 0 orders",
        16: "25 stores; 20 states; 21 options; FASHION SQUARE MALL SCOTTSDALE 10:00 - 21:00; ALA MOANA CENTER "
            "1450, ALA MOANA BOULEVARD; 2 New York stores; GARDEN ROOSEVELT FIELD MALL GARDEN CITY 11530; "
            "SOUTH COAST PLAZA MALL COSTA MESA",
        17: "331/10; SLIM FIT SHIRT USD 59.90; White, Sand, Light sky blue, Black, Dark brown; 4408/147; "
            "115/10; 38 filter leaves BASIC SLIM FIT JEANS and STRAIGHT-FIT JEANS; LOOSE FIT JEANS USD "
            "69.90 8 colors; Faded black 30 (US 30) x2 USD 139.80 / USD 144.75",
        18: "176/10; COCOA SUNSET EDP 100ML and COCOA BLISS EDP 100 ML at USD 35.90; ZARA ILLUSION RADIANCE "
            "USD 39.90 SKU 556189101; ZARAILLUSION SERENITY USD 39.90 SKU 545449880; 30/10; PINK RUSH LIP "
            "GLOSS PINK INFINITY USD 22.90; subtotal USD 119.70; 2 ILLUSION matches",
        19: "BURGUNDY 100% LEATHER PUFFED-BODY DRESS USD 459.00; Burgundy; XS low on stock, S/M/L coming "
            "soon; 5479/900; 406/10; 100% CASHMERE CROPPED FIT CARDIGAN USD 319.00 Turquoise XS; M doubled "
            "USD 638.00; 522/10; LEATHER WIDE HEEL BOOTS USD 179.00 Black 8 sizes; 7½ added; subtotal USD "
            "817.00; PUFFED: 1 match",
        20: "115/10; BLACK: PRINTED LOOSE FIT JEANS, BASIC SLIM FIT JEANS, LOOSE FIT JEANS; under 40 "
            "LIGHTWEIGHT REGULAR FIT JEANS USD 35.94; Light blue, Ecru, charcoal gray; ECRU 30 (US 30) x2 "
            "USD 71.88 / USD 76.83; DISTRESSED: 2 matches, the jeans is DISTRESSED FLARE FIT JEANS; final "
            "subtotal USD 151.78",
        21: "perfume x1, ELONGATED SHOULDER BAG Two-tone x1, polo Mid-gray M x1; subtotal USD 258.80, "
            "total USD 263.75; perfume to 2: USD 298.70; bag to 3: USD 398.50 / USD 403.45; removing the "
            "polo leaves USD 229.50 / USD 234.45; order "
            "8004384012 2026-09-12 Returned USD 339.00; card 5296; member since 2026-09-03; wishlist empty",
    }
    run = tmp_path / f"shortcut{n}"
    (run / "screenshots").mkdir(parents=True)
    (run / "initial.db").write_bytes(SEED_REF.read_bytes())
    (run / "after.db").write_bytes(SEED_REF.read_bytes())
    (run / "trajectory.json").write_text(json.dumps({
        "task_id": f"Zara--{n}", "start_url": "http://localhost:46114/",
        "steps": [], "terminated": True, "termination_reason": "agent_done",
        "final_answer": answers[n],
    }))
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False, "shortcut with no navigation must FAIL"


# ------------------------------------------------------------ D. wrong answers
@pytest.mark.parametrize("n", range(22))
def test_wrong_answer_fails(n, tmp_path):
    """Honest navigation cloned from the fixture, every anchored fact
    replaced by a plausible-but-wrong neighbor value."""
    run = clone(honest(n), tmp_path / f"wrong{n}")
    traj = json.loads((run / "trajectory.json").read_text())
    wrong = {
        0: "upstream 534, snapshot 11; BURGUNDY leaves the MIDI SCARF DRESS at USD 229.00; cheapest "
           "SATIN DRAPED DRESS USD 169.00; color Ecru; all sizes coming soon; ref 8100/038; subtotal "
           "USD 229.00, shipping USD 4.95, total USD 233.95; final x3 USD 209.70",
        1: "USD 229.01; 8100/039; MAN; TROUSERS; Black; all sizes low on stock; SKU 578162618; no tags; "
           "wishlist two items; final two: DRAPED SEQUIN MIDI DRESS and ELONGATED SHOULDER BAG",
        2: "USD 45.90; 2 colors Two-tone and Black; TWO SIZE; quantity 2; total USD 99.80; RED SKU "
           "552743196; BLACK SKU 552743197; OVAL USD 35.90; final subtotal USD 149.70",
        3: "55 upstream, 9 snapshot; Blue; USD 45.00; 9-10 years low on stock; RUFFLED ROMANTIC DRESS "
           "USD 45.90 all in stock; jacket USD 35.90 x2 total USD 75.80; PINAFORE: DENIM POCKET DRESS",
        4: "544 results; BLUE 321, WHITE 40; USD 24.90 - 350.00; LOOSE FIT JEANS first; USD 69.90; "
           "0774/334; 6 sizes; 34 (US 34) coming soon; 38 filter leaves LOOSE FIT JEANS; total USD 99.80 "
           "stays; under 50 nothing left",
        5: "48 results; Beige 10; USD 50.90 - 198.00; CONTRAST REVERSIBLE JACKET; XS in stock; subtotal "
           "USD 174.95; order 80030000006 total USD 225.80; card ending 1112; status Shipped",
        6: "ALA MOANA BEACH; 1400 ALA MOANA ROAD; 09:00 - 18:00; 8332472000; US/Alaska; 20260928; 4 "
           "California stores; CENTURY CITY Saturday 10:00 - 21:00; latest close FASHION SHOW MALL",
        7: "CENTURY CITY MALL; 10250 SANTA MONICA; 11:00 - 20:00 Saturday; MALL; CLOSED; 20260930; "
           "latest Monday open 250 POST ST SAN FRANCISCO",
        8: "4 California stores; 1250 POST ST; 12:00 - 21:00; DESERT RIDGE MALL; 09:00 - 18:00; Arizona "
           "US/Pacific; latest Saturday close ALA MOANA CENTER",
        9: "boots qty 3; subtotal USD 766.00; total USD 770.95; the dress remains; RED bag not added; "
           "orders 8004128041 and 8004277560; unit price USD 219.00",
        10: "order 80010000006; total USD 636.90; card ending 2424; HOME address chosen; 2 orders now",
        11: "3 orders; 8004128042; PLACED 2026-09-09; USD 79.90 total; card 4422; Chicago; member since "
            "2026-08-03; 4 saved items; subtotal USD 408.00 after doubling",
        12: "two items; 2026-09-01 dates; CONTRAST REVERSIBLE JACKET added; final three; highest card "
            "price ELONGATED SHOULDER BAG at USD 49.90; color Ecru; button ADD TO WISHLIST",
        13: "order 80050000006; total USD 229.00; LEATHER LOAFERS line",
        14: "WORK label; 425 W 14th St; New York; WINTER added; WORK default; WINTER remains",
        15: "Two-tone x2; USD 99.80 total; the bag holds the boots instead; carol's line stays x1; "
            "wishlist one item; 1 order; 2 saved addresses",
        16: "26 stores; 21 states; 22 options; 09:00 - 18:00; 1400 ALA MOANA ROAD; 1 New York store; "
            "GARDEN ROOSEVELT ZIP 11531; SOUTH COAST closed Sunday",
        17: "330/11; 114/9; LEATHER LOAFERS; USD 35.94; four colors; 0774/333; XL out of stock; LOOSE "
            "FIT JEANS USD 59.90 with 6 colors; Oyster-white 30 (US 30) x2",
        18: "175/11; USD 39.91; TWO SIZE; SKU 556189100; 0110/962; 3 gallery images; gloss USD 25.90 "
            "color RED INFINITY; subtotal USD 129.70; 3 ILLUSION matches",
        19: "Black; USD 458.00; all in stock; 5479/901; TRENCH RAINCOAT; Midi dress made of 90% wool; "
            "cardigan USD 329.00 in Blue; L size added; boots USD 159.00 6 sizes; subtotal USD 807.00; "
            "PUFFED: 2 matches",
        20: "USD 35.95; two colors; 34 (US 34) in stock; ECRU 32 in stock; DISTRESSED: 1 match, the "
            "boots; final subtotal USD 161.78; BLACK shows only PRINTED LOOSE FIT JEANS",
        21: "two lines; total USD 223.75; subtotal USD 44.90; 8004384013 2026-09-13 SHOULDER PAD ZIP "
            "JACKET; card 5286; member since 2026-09-04; wishlist holds one item",
    }
    traj["final_answer"] = wrong[n]
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False, "falsified facts must FAIL"


# ------------------------------------------------------------ E. stale/pre-mutated DB
def test_premutated_seed_fails(tmp_path):
    run = clone(honest(0), tmp_path / "stale0")
    db = sqlite3.connect(run / "initial.db")
    db.execute("UPDATE categories SET upstream_grid_count = 999 WHERE seo_id = 1066")
    db.commit()
    db.close()
    payload, _ = run_verifier(0, run)
    assert payload["pass"] is False, "pre-mutated initial DB must FAIL the seed gate"


def test_stale_after_db_fails(tmp_path):
    """T9 honest run graded against the untouched seed as its after DB
    (the stateful change never happened)."""
    run = clone(honest(9), tmp_path / "stale9")
    (run / "after.db").write_bytes(SEED_REF.read_bytes())
    payload, _ = run_verifier(9, run)
    assert payload["pass"] is False, "after DB missing the allowed delta must FAIL"


# ------------------------------------------------------------ F. injected writes
@pytest.mark.parametrize("n", [4, 6, 7, 8])
def test_readonly_violation_fails(n, tmp_path):
    run = clone(honest(n), tmp_path / f"rov{n}")
    inject_cart_row(run / "after.db")
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False, "unexpected DB write in a read-only task must FAIL"


@pytest.mark.parametrize("n", [0, 1, 2, 3, 5, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21])
def test_stateful_injected_row_fails(n, tmp_path):
    run = clone(honest(n), tmp_path / f"inj{n}")
    inject_cart_row(run / "after.db")
    payload, _ = run_verifier(n, run)
    assert payload["pass"] is False, "extra cart row beyond the allowed delta must FAIL"


# ------------------------------------------------------------ G. tampered packages
def test_wrong_task_id_fails(tmp_path):
    run = clone(honest(0), tmp_path / "tid0")
    traj = json.loads((run / "trajectory.json").read_text())
    traj["task_id"] = "Zara--1"
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(0, run)
    assert payload["pass"] is False


def test_offsite_url_fails(tmp_path):
    run = clone(honest(0), tmp_path / "off0")
    traj = json.loads((run / "trajectory.json").read_text())
    traj["steps"][1]["url"] = "https://www.zara.com/us/en/woman-dresses-l1066.html"
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(0, run)
    assert payload["pass"] is False


def test_cross_port_url_fails(tmp_path):
    run = clone(honest(0), tmp_path / "xport0")
    traj = json.loads((run / "trajectory.json").read_text())
    traj["steps"][1]["url"] = "http://localhost:48114/us/en/woman-dresses-l1066.html"
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(0, run)
    assert payload["pass"] is False


def test_unterminated_fails(tmp_path):
    run = clone(honest(0), tmp_path / "unterm0")
    traj = json.loads((run / "trajectory.json").read_text())
    traj["terminated"] = False
    traj["termination_reason"] = "max_steps"
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(0, run)
    assert payload["pass"] is False


def test_empty_answer_fails(tmp_path):
    run = clone(honest(0), tmp_path / "empty0")
    traj = json.loads((run / "trajectory.json").read_text())
    traj["final_answer"] = "   "
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(0, run)
    assert payload["pass"] is False


def test_bad_screenshot_fails(tmp_path):
    run = clone(honest(0), tmp_path / "badpng0")
    traj = json.loads((run / "trajectory.json").read_text())
    referenced = next(s["screenshot_before"] for s in traj["steps"] if s.get("screenshot_before"))
    (run / "screenshots" / referenced).write_bytes(b"NOT-A-PNG-AT-ALL")
    payload, _ = run_verifier(0, run)
    assert payload["pass"] is False


def test_missing_navigation_fails(tmp_path):
    """Honest T4 answer + DB but the search/PDP steps deleted from the
    trajectory (the navigation gates must trip)."""
    run = clone(honest(4), tmp_path / "navcut4")
    traj = json.loads((run / "trajectory.json").read_text())
    keep = [s for s in traj["steps"]
            if "search" not in str(s.get("url", "")) and "p00774333" not in str(s.get("url", ""))]
    traj["steps"] = keep
    (run / "trajectory.json").write_text(json.dumps(traj))
    payload, _ = run_verifier(4, run)
    assert payload["pass"] is False


# ------------------------------------------------------------ H. state under-reach
def test_t0_wrong_product_row_fails(tmp_path):
    """T0 honest run, but the guest bag row mutated to the second tied product."""
    run = clone(honest(0), tmp_path / "mut0")
    db = sqlite3.connect(run / "after.db")
    db.execute("UPDATE cart_items SET product_id = 575618025, color_id = 10, size_id = 45 "
               "WHERE user_id IS NULL")
    db.commit()
    db.close()
    payload, _ = run_verifier(0, run)
    assert payload["pass"] is False


def test_t2_wrong_state_row_fails(tmp_path):
    """T2 honest run, but the added bag row mutated to the wrong color."""
    run = clone(honest(2), tmp_path / "mut2")
    db = sqlite3.connect(run / "after.db")
    db.execute("UPDATE cart_items SET color_id = 48 WHERE user_id IS NULL")
    db.commit()
    db.close()
    payload, _ = run_verifier(2, run)
    assert payload["pass"] is False


def test_t5_order_row_missing_fails(tmp_path):
    """T5 honest run, but the placed order row deleted from the after DB."""
    run = clone(honest(5), tmp_path / "mut5")
    db = sqlite3.connect(run / "after.db")
    db.execute("DELETE FROM orders WHERE number = '80030000005'")
    db.commit()
    db.close()
    payload, _ = run_verifier(5, run)
    assert payload["pass"] is False


def test_t12_wishlist_row_missing_fails(tmp_path):
    """T12 honest run, but the added wishlist row deleted from the after DB."""
    run = clone(honest(12), tmp_path / "mut12")
    db = sqlite3.connect(run / "after.db")
    db.execute("DELETE FROM wishlist_items WHERE product_id = 545406123")
    db.commit()
    db.close()
    payload, _ = run_verifier(12, run)
    assert payload["pass"] is False


def test_t16_newsletter_row_missing_fails(tmp_path):
    """T16 honest run, but the newsletter row deleted from the after DB."""
    run = clone(honest(16), tmp_path / "mut16")
    db = sqlite3.connect(run / "after.db")
    db.execute("DELETE FROM newsletter_signups WHERE email = 'store-fan@zara.example'")
    db.commit()
    db.close()
    payload, _ = run_verifier(16, run)
    assert payload["pass"] is False


def test_t13_order_number_fails(tmp_path):
    """T13 honest run, but the placed order number mutated."""
    run = clone(honest(13), tmp_path / "mut13")
    db = sqlite3.connect(run / "after.db")
    db.execute("UPDATE orders SET number = '80050000006' WHERE id = 5")
    db.commit()
    db.close()
    payload, _ = run_verifier(13, run)
    assert payload["pass"] is False


def test_t14_missing_delete_fails(tmp_path):
    """T14 honest run, but the HOME address resurrected in the after DB."""
    run = clone(honest(14), tmp_path / "mut14")
    db = sqlite3.connect(run / "after.db")
    db.execute("INSERT INTO addresses (id, user_id, label, full_name, line1, line2, city, state, "
               "zip, phone, is_default) VALUES (3, 2, 'HOME', 'Bob Chen', "
               "'1810 N Sedgwick St, Unit 3', NULL, 'Chicago', 'IL', '60614', '773-555-0137', 0)")
    db.commit()
    db.close()
    payload, _ = run_verifier(14, run)
    assert payload["pass"] is False
