"""Adversarial test matrix for the us_appliance reviewer verifier suite.

Every honest fixture is the reviewer's real live walkthrough (SPECS); every
negative case is an attack on one gate. Zero false positives required: a
verifier may only PASS its honest fixture and must FAIL every attack.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import (PNG, RunBuilder, acquire_seed, make_after_db,  # noqa: E402
                      make_dirty_seed, run_verifier, task_ques)
from fixtures_data import BASE, SPECS  # noqa: E402


@pytest.fixture(scope="session")
def seed_db(tmp_path_factory):
    return acquire_seed()


@pytest.fixture()
def dirs(tmp_path):
    return tmp_path


def build_honest_run(root: Path, task_no: int, answer=None, urls=None) -> Path:
    rb = RunBuilder(root, f"USAppliance--{task_no}")
    for u in (urls if urls is not None else SPECS[task_no]["urls"]):
        rb.add_step("navigate", BASE + u)
    return rb.write(answer if answer is not None else SPECS[task_no]["answer"])


# ---------------------------------------------------------------- honest PASS
@pytest.mark.parametrize("task_no", range(20))
def test_honest_walkthrough_passes(task_no, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"honest_{task_no}", task_no)
    after_db = make_after_db(tmp_path / f"after_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert verdict["pass"], f"honest run must PASS: {verdict['reason']}"


# ---------------------------------------------------------------- no-op FAIL
@pytest.mark.parametrize("task_no", range(20))
def test_noop_fails(task_no, tmp_path, seed_db):
    """Agent opens the homepage, does nothing, empty answer: every verifier
    must FAIL (no false positives on a blank run)."""
    rb = RunBuilder(tmp_path / f"noop_{task_no}", f"USAppliance--{task_no}")
    rb.add_step("navigate", BASE + "/")
    run_dir = rb.write("")
    after_db = shutil.copyfile(seed_db, tmp_path / f"after_noop_{task_no}.db")
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "no-op run must FAIL"


# ------------------------------------------------- shortcut (answer, no navigation)
@pytest.mark.parametrize("task_no", [0, 3, 5, 9, 10, 14])
def test_shortcut_answer_without_navigation_fails(task_no, tmp_path, seed_db):
    """Correct answer + correct DB but ZERO task-relevant navigation: the
    answer was recalled, not read off the site."""
    rb = RunBuilder(tmp_path / f"shortcut_{task_no}", f"USAppliance--{task_no}")
    rb.add_step("navigate", BASE + "/")  # stays on home, opens nothing
    run_dir = rb.write(SPECS[task_no]["answer"])
    after_db = make_after_db(tmp_path / f"after_shortcut_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "knowledge-shortcut must FAIL"


# ---------------------------------------------------------------- wrong answers
WRONG_ANSWERS = {
    0: ("There are 250 gas ranges; the cheapest is a Bosch at $499.00. The GE "
         "JGBS66REKSS costs $999.00 with promo note 'Holiday Sale'. ZIP 48083 is "
         "unavailable; ZIP 96762 ships everywhere in the USA."),
    2: ("Subtotal $3,500.00, shipping $250. After changes: subtotal $1,000.00, "
        "shipping $50.00. The In-Home Delivery upgrade is $89 per order."),
    4: ("Alice has 5 orders; the delivered order used Curbside delivery via FedEx, "
        "tracking 999XYZ, 2 events, total $500.00, 5 line items."),
    6: ("The sale headline is Fall Blowout; the biggest cut is a Samsung fridge at "
        "$5,000 off; 10 products are on sale; French Door 50, Dishwashers 12."),
    8: ("Financing offers 24 months interest-free with no minimum and 20 brands; "
        "the card is called Appliance Pay; call 555-0100."),
    12: ("The range costs $700.00; the promise is to match 50% of the difference; "
         "the confirmation heading is Thank You; product line 'Dishwasher'."),
    16: ("Order 20001 placed for a total of $2,500.00 with free delivery."),
    19: ("Newsletter confirmed 'Welcome aboard'; hours are 9-5 weekends only; the "
         "address is 1 Main St, Detroit MI 48000; fax 555-1234; 3 sections; Track an "
         "Order is in Returns; 60-day window; 25% restocking fee."),
}


@pytest.mark.parametrize("task_no, wrong", sorted(WRONG_ANSWERS.items()))
def test_wrong_answer_fails(task_no, wrong, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"wrong_{task_no}", task_no, answer=wrong)
    after_db = make_after_db(tmp_path / f"after_wrong_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong answer must FAIL"


# ---------------------------------------------------- stale DB (missing mutation)
@pytest.mark.parametrize("task_no", [2, 3, 12, 15, 16, 17, 19])
def test_stateful_without_mutation_fails(task_no, tmp_path, seed_db):
    """Agent self-reports success but the DB shows no change -> FAIL."""
    run_dir = build_honest_run(tmp_path / f"stale_{task_no}", task_no)
    after_db = shutil.copyfile(seed_db, tmp_path / f"after_stale_{task_no}.db")
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "stateful task with unmutated DB must FAIL"


# ---------------------------------------------------- read-only violation
@pytest.mark.parametrize("task_no", [0, 4, 6, 9, 10, 18])
def test_readonly_violation_fails(task_no, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"dirty_{task_no}", task_no)
    after_db = shutil.copyfile(seed_db, tmp_path / f"after_dirty_{task_no}.db")
    db = sqlite3.connect(after_db)
    db.execute("INSERT INTO newsletter_subscribers (id, email, created_on) "
               "VALUES (99, 'sneaky@example.com', '2026-09-29')")
    db.commit()
    db.close()
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "read-only task with injected row must FAIL"


def test_extra_table_write_on_stateful_fails(tmp_path, seed_db):
    """T3 honest order + a sneaky extra write elsewhere -> FAIL."""
    run_dir = build_honest_run(tmp_path / "sneaky_3", 3)
    after_db = make_after_db(tmp_path / "after_sneaky_3.db", 3)
    db = sqlite3.connect(after_db)
    db.execute("INSERT INTO newsletter_subscribers (id, email, created_on) "
               "VALUES (98, 'sneaky@example.com', '2026-09-29')")
    db.commit()
    db.close()
    verdict = run_verifier(3, run_dir, seed_db, after_db)
    assert not verdict["pass"], "unexpected extra table write must FAIL"


def test_wrong_mutation_on_stateful_fails(tmp_path, seed_db):
    """T3 with a wrong-shape order row (self-report + wrong state) -> FAIL."""
    run_dir = build_honest_run(tmp_path / "wrongstate_3", 3)
    after_db = make_after_db(tmp_path / "after_wrongstate_3.db", 3)
    db = sqlite3.connect(after_db)
    db.execute("UPDATE orders SET total = 999.99 WHERE id = 9")
    db.commit()
    db.close()
    verdict = run_verifier(3, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong-shaped stateful mutation must FAIL"


# ---------------------------------------------------------------- package tampering
def test_wrong_task_id_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "tamper_id", "USAppliance--0")
    for u in SPECS[0]["urls"]:
        rb.add_step("navigate", BASE + u)
    run_dir = rb.write(SPECS[0]["answer"], task_id="USAppliance--19")
    after_db = make_after_db(tmp_path / "after_tamper_id.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_offsite_url_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "tamper_offsite", "USAppliance--0")
    rb.add_step("navigate", BASE + "/ranges.html")
    rb.add_step("navigate", "https://www.us-appliance.com/gas-ranges.html")
    rb.add_step("navigate", BASE + "/gas-ranges.html")
    rb.add_step("navigate", BASE + "/jgbs66rekss.html")
    run_dir = rb.write(SPECS[0]["answer"])
    after_db = make_after_db(tmp_path / "after_tamper_off.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_other_port_url_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "tamper_port", "USAppliance--0")
    rb.add_step("navigate", BASE + "/ranges.html")
    rb.add_step("navigate", "http://localhost:47108/gas-ranges.html")
    rb.add_step("navigate", "http://127.0.0.1:40108/gas-ranges.html")  # other port
    rb.add_step("navigate", BASE + "/jgbs66rekss.html")
    run_dir = rb.write(SPECS[0]["answer"])
    after_db = make_after_db(tmp_path / "after_tamper_port.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_not_terminated_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "tamper_term", "USAppliance--0")
    for u in SPECS[0]["urls"]:
        rb.add_step("navigate", BASE + u)
    run_dir = rb.write(SPECS[0]["answer"], terminated=False, reason="max_steps")
    after_db = make_after_db(tmp_path / "after_tamper_term.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_empty_answer_fails(tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / "tamper_empty", 0, answer="   ")
    after_db = make_after_db(tmp_path / "after_tamper_empty.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


def test_corrupt_screenshot_fails(tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / "tamper_shot", 0)
    shots = sorted((run_dir / "screenshots").glob("step_*.png"))
    shots[-1].write_bytes(b"not a png at all")  # last one is referenced
    after_db = make_after_db(tmp_path / "after_tamper_shot.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"]


# ---------------------------------------------------------------- seed gate
def test_pre_mutated_seed_fails(tmp_path, seed_db):
    """A run graded against a pre-mutated initial DB (not the frozen seed)."""
    run_dir = build_honest_run(tmp_path / "dirtyseed_19", 19)
    dirty = make_dirty_seed(
        tmp_path / "dirty_seed_19.db",
        "INSERT INTO newsletter_subscribers (id, email, created_on) "
        "VALUES (1, 'pre@dirty.com', '2026-01-01')")
    after_db = make_after_db(tmp_path / "after_dirtyseed_19.db", 19)
    verdict = run_verifier(19, run_dir, dirty, after_db)
    assert not verdict["pass"], "pre-mutated initial DB must FAIL the seed gate"


# ---------------------------------------------------------------- task-specific
def test_t6_dead_onsale_link_count_fails(tmp_path, seed_db):
    """T6 answered with the unfiltered category totals (318 / 336) instead of
    the on-sale counts -> FAIL (the facet must have been applied and read)."""
    run_dir = build_honest_run(
        tmp_path / "t6_unfiltered", 6,
        answer=("Biggest cut: Best HBC163ESS, Now $2,095.00, Was $3,299.00, "
                "You save $1,204.00. 24 products shown on sale today. French Door "
                "Refrigerators: 318 products. Dishwashers: 336 products."))
    after_db = make_after_db(tmp_path / "after_t6_unfiltered.db", 6)
    verdict = run_verifier(6, run_dir, seed_db, after_db)
    assert not verdict["pass"], "category-total answers must FAIL the on-sale count gates"


def test_t4_borderline_status_mixup_fails(tmp_path, seed_db):
    run_dir = build_honest_run(
        tmp_path / "t4_mixup", 4,
        answer=("Alice has 2 orders. The delivered order used Standard Delivery via "
                "Maersk with tracking MN-88231340, 3 events, total $2,011.88, 1 line "
                "item. Statuses: Delivered and Cancelled."))
    after_db = make_after_db(tmp_path / "after_t4_mixup.db", 4)
    verdict = run_verifier(4, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong order facts must FAIL"


def test_t1_hood_as_dishwasher_answer_counts(tmp_path, seed_db):
    """The hood price is a defensible 'cheapest result' reading only when named
    as the hood; answering the hood as a dishwasher with a wrong price fails."""
    run_dir = build_honest_run(
        tmp_path / "t1_hood_wrong_price", 1,
        answer=("384 dishwashers found; 36 Bosch results in $500-$1,500. The cheapest "
                "is the Bosch DUH30253UC dishwasher at $599.00 with model code "
                "DUH30253UC and the 15 Months Special Finance Offer."))
    after_db = make_after_db(tmp_path / "after_t1_hood.db", 1)
    verdict = run_verifier(1, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong cheapest price must FAIL"


# ------------------------------------------------------------ r2 deepening negatives
@pytest.mark.parametrize("task_no, wrong", [
    (4, ("Alice has 2 orders: Delivered and Shipped. The delivered order used "
         "In-Home Delivery via R+L Carriers, Pro #RL774912, 6 events, total "
         "$2,289.32, 2 line items. The shipped order ships via FedEx with tracking "
         "999ABC, estimated delivery Dec 25, 2026, and shows 5 timeline events.")),
    (7, ("21 brands have rebate offers, expires Dec 31. Asko: Save $300 washer "
         "and dryer + extended 5 Year Warranty. KitchenAid: Save up to $3000. Viking: "
         "Buy One Get One. Miele lists 3 rebate offers and Samsung lists 2 offers. "
         "Shop By Brand shows a Rebate Offers flag.")),
    (9, ("Free delivery over $999, $99 under it, In-Home $199. P.O. Boxes not "
         "served; stairs cost extra. FAQ: no delivery to Alaska; sales tax applies. "
         "The return policy: orders can be canceled within 72 hours. Smaller items "
         "are shipped via DHL.")),
    (10, ("20,841 reviews, 4.9 average, 97% 4-5 stars, founded 1963, online since "
          "1999. John: 5 stars, 09-20-26, Verified. Another page-1 review: Ernie, 5 "
          "stars. Page 2 starts with Calvin D., 5 stars, dated 07-07-26 — John's "
          "review is more recent than it.")),
    (11, ("Shipping is free over $999, cancellable within 48 hours, price match "
          "110%. No delivery to Alaska/Hawaii. The warranty answer: the retailer "
          "will repair or replace a covered appliance. Installation is part of our "
          "delivery. In-Home upgrade $199; 2 delivery options compared.")),
    (12, ("The GE JGBS66REKSS is $823.00. The cart shows a subtotal of $900.00 "
         "with FREE shipping — the order qualifies for free delivery. We'll match "
         "110% of the difference; confirmation heading Request Received; product "
         "line GE JGBS66REKSS 30\" Gas Range.")),
    (18, ("4 content results; Range Buying Guide; first section 1. Fuel Types "
          "covering Electric and Induction only. 1428 product results; the cheapest "
          "listed is the Gas Range Installation Kit at $29.95 — an actual range "
          "that serves Electric.")),
    (19, ("Newsletter confirmed. Sales 8am-6pm EST; service 10am-7pm EST — the "
          "same hours. 877-628-9913 both lines. 111 Corporate Drive, Auburn Hills, "
          "MI 48326, fax (248) 364-0701. Seven help sections; Track an Order in "
          "Delivery. 30-day returns, 10% restocking; damage must be reported within "
          "72 hours; all sales final on overstock and clearance items.")),
])
def test_r2_deepening_wrong_answers_fail(task_no, wrong, tmp_path, seed_db):
    """Attacks on the r2-deepened answer keys: every wrong value on a NEW
    question point must FAIL the extended verifier."""
    run_dir = build_honest_run(tmp_path / f"r2_wrong_{task_no}", task_no, answer=wrong)
    after_db = make_after_db(tmp_path / f"after_r2_wrong_{task_no}.db", task_no)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], f"r2 deepening wrong answer must FAIL (T{task_no})"


def test_t12_missing_cart_mutation_fails(tmp_path, seed_db):
    """r2 contract: T12's honest walk leaves BOTH a cart row and the price
    match request. A DB with only the price-match row (the old r1 shape) is a
    stale state and must FAIL."""
    run_dir = build_honest_run(tmp_path / "t12_no_cart", 12)
    after_db = make_after_db(tmp_path / "after_t12_no_cart.db", 12)
    db = sqlite3.connect(after_db)
    db.execute("DELETE FROM cart_items")
    db.commit()
    db.close()
    verdict = run_verifier(12, run_dir, seed_db, after_db)
    assert not verdict["pass"], "T12 without the cart row must FAIL"


def test_t12_without_cart_navigation_fails(tmp_path, seed_db):
    """T12 answered without ever opening the cart page -> the r2 cart-gate
    navigation check must FAIL."""
    rb = RunBuilder(tmp_path / "t12_no_cartnav", "USAppliance--12")
    rb.add_step("navigate", BASE + "/jgbs66rekss.html")
    rb.add_step("navigate", BASE + "/price-match-request.html")
    run_dir = rb.write(SPECS[12]["answer"])
    after_db = make_after_db(tmp_path / "after_t12_no_cartnav.db", 12)
    verdict = run_verifier(12, run_dir, seed_db, after_db)
    assert not verdict["pass"], "T12 without cart navigation must FAIL"


def test_t4_without_shipped_order_navigation_fails(tmp_path, seed_db):
    """T4 answered without opening the shipped order detail -> the r2 shipped
    order navigation gate must FAIL."""
    rb = RunBuilder(tmp_path / "t4_no_shipped", "USAppliance--4")
    rb.add_step("navigate", BASE + "/login.php")
    rb.add_step("navigate", BASE + "/account.php")
    rb.add_step("navigate", BASE + "/account.php/orders/1")
    run_dir = rb.write(SPECS[4]["answer"])
    after_db = make_after_db(tmp_path / "after_t4_no_shipped.db", 4)
    verdict = run_verifier(4, run_dir, seed_db, after_db)
    assert not verdict["pass"], "T4 without shipped-order navigation must FAIL"


def test_t0_without_sort_navigation_fails(tmp_path, seed_db):
    """T0 answered with the featured-page cheapest (the old ambiguous reading)
    and no sort URL in the trajectory -> the r2 single-reading + sort gate
    must FAIL."""
    rb = RunBuilder(tmp_path / "t0_no_sort", "USAppliance--0")
    rb.add_step("navigate", BASE + "/ranges.html")
    rb.add_step("navigate", BASE + "/gas-ranges.html")
    rb.add_step("navigate", BASE + "/jgbs66rekss.html")
    run_dir = rb.write(
        "The Gas Ranges category lists 297 products. The cheapest one shown is the "
        "Electrolux ECFG3068AS at $2,979.00. The GE JGBS66REKSS is $823.00 with "
        "promo note 'Sale ends Sept 30'. Features: steam clean, edge-to-edge cooktop. "
        "ZIP 48083: available for delivery to your area. ZIP 96762: continental "
        "United States only.")
    after_db = make_after_db(tmp_path / "after_t0_no_sort.db", 0)
    verdict = run_verifier(0, run_dir, seed_db, after_db)
    assert not verdict["pass"], "featured-page reading without sort must FAIL"
