"""Adversarial test matrix for the ups reviewer verifier suite.

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

from _support import (BASE, RunBuilder, acquire_seed, make_after_db,  # noqa: E402
                      make_dirty_seed, run_verifier, task_ques)
from fixtures_data import SPECS  # noqa: E402


@pytest.fixture(scope="session")
def seed_db(tmp_path_factory):
    return Path(acquire_seed())


def build_honest_run(root: Path, task_no: int, answer=None, urls=None) -> Path:
    rb = RunBuilder(root, f"UPS--{task_no}")
    for u in (urls if urls is not None else SPECS[task_no]["urls"]):
        rb.add_step("navigate", BASE + u)
    return rb.write(answer if answer is not None else SPECS[task_no]["answer"])


# ---------------------------------------------------------------- honest PASS
@pytest.mark.parametrize("task_no", range(20))
def test_honest_walkthrough_passes(task_no, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"honest_{task_no}", task_no)
    after_db = make_after_db(tmp_path / f"after_{task_no}.db", task_no, seed_db)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert verdict["pass"], f"honest run must PASS: {verdict['reason']}"


# ---------------------------------------------------------------- no-op FAIL
@pytest.mark.parametrize("task_no", range(20))
def test_noop_fails(task_no, tmp_path, seed_db):
    """Agent opens the homepage, does nothing, empty answer: every verifier
    must FAIL (no false positives on a blank run)."""
    rb = RunBuilder(tmp_path / f"noop_{task_no}", f"UPS--{task_no}")
    rb.add_step("navigate", BASE + "/")
    run_dir = rb.write("")
    after_db = shutil.copyfile(seed_db, tmp_path / f"after_noop_{task_no}.db")
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "no-op run must FAIL"


# ------------------------------------------------- shortcut (answer, no navigation)
SHORTCUT_TASKS = [0, 3, 4, 7, 10, 11, 13, 15, 16, 19]


@pytest.mark.parametrize("task_no", SHORTCUT_TASKS)
def test_shortcut_answer_without_navigation_fails(task_no, tmp_path, seed_db):
    """Correct answer + correct DB but ZERO task-relevant navigation: the
    answer was recalled, not read off the site."""
    rb = RunBuilder(tmp_path / f"shortcut_{task_no}", f"UPS--{task_no}")
    rb.add_step("navigate", BASE + "/")  # stays on home, opens nothing
    run_dir = rb.write(SPECS[task_no]["answer"])
    after_db = make_after_db(tmp_path / f"after_shortcut_{task_no}.db", task_no, seed_db)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "knowledge-shortcut must FAIL"


# ---------------------------------------------------------------- wrong answers
WRONG_ANSWERS = {
    0: ("The latest scan is Delivered in Seattle on 2026-10-01 at noon; the "
        "shipment made 7 facility stops after leaving Seattle. The pickup "
        "location is Deepchhaya Deli & Grocery at 500 8th Ave, pick up by "
        "2026-11-01, ground drop-off 9:00am."),
    1: ("Status: Delivered. The exception reason is weather delay. Scheduled "
        "delivery 2026-12-25. The article says exceptions are caused by customs. "
        "The only change option is Hold for Pickup. Intercept fees are $15.00 web "
        "and $25.00 phone. Shipper: Cascade Coffee Co., Seattle, WA."),
    3: ("The residential estimate quoted 5 services; cheapest is UPS Ground at "
        "$19.99 and most expensive is UPS 3 Day Select at $99.99. Unchecking "
        "residential makes the cheapest $12.00 cheaper."),
    4: ("The guaranteed 10:30 a.m. services are UPS 2nd Day Air A.M. and UPS "
        "Ground. The cheapest is 2nd Day Air A.M. at $58.74, delivered by 10:30 "
        "A.M. Wednesday. Latest pickup 6:00 P.M., max weight 70 lbs."),
    7: ("There are 25 locations near 10001: 5 Access Points and 12 Drop Boxes. "
        "The nearest drop box is at 1 Times Square with ground drop-off 5:00pm. "
        "The closest UPS Store phone is 555-0123. The closest Access Point's phone "
        "is 2122442681."),
    8: ("The Seattle shipment has 2 packages, both delivered, signed by J. SMITH "
        "on 2026-09-30. Package 2's latest scan is Out for Delivery in Tukwila, "
        "WA. On the Track page the status is Delivered and the facility is "
        "Seattle, WA."),
    11: ("Carol has 6 shipments. Daily Pickup is $25.00, Smart Pickup $39.00, "
         "Day-Specific 3 days $50.00 — the cheapest is Daily Pickup. On-Call "
         "fees are $5.00 future-day and $10.00 same-day; Smart Pickup Saturday "
         "is $20.00."),
    13: ("Label Created means the package has shipped. Long-distance shipments "
         "are scanned every hour. The second-to-last scan was Origin Scan at "
         "Toronto, ON, CA on 2026-09-24; scheduled delivery 2026-09-30; service "
         "UPS 2nd Day Air. The nearest drop box is a Mobile Car with ground "
         "drop-off 7:00pm."),
    15: ("The closest UPS Store to 60601 is at 100 W Main St, phone 555-0100, "
         "open Monday 10-8 and Tuesday 10-8, air and ground drop-off 5:00pm. The "
         "nearest Access Point is Staples; the Store is closer. The packing "
         "experts sentence is not on the Pack and Ship page."),
    16: ("The Saturday-delivery air services are UPS Next Day Air Saver and UPS "
         "Ground Saver. UPS 2nd Day Air A.M. is not guaranteed, latest pickup "
         "6:00 P.M., and costs $50.00 for SF to Seattle, delivered Monday. UPS "
         "Ground max weight is 70 lbs, delivered within 3 to 10 days."),
    19: ("UPS Ground costs $45.00 delivered by Friday October 2; billable weight "
         "16.5 lbs. Next Day Air Early breakdown: Transportation $100.00, DAS "
         "$10.00, Fuel $20.00. Intercept web fee $25.00."),
}


@pytest.mark.parametrize("task_no, wrong", sorted(WRONG_ANSWERS.items()))
def test_wrong_answer_fails(task_no, wrong, tmp_path, seed_db):
    run_dir = build_honest_run(tmp_path / f"wrong_{task_no}", task_no, answer=wrong)
    after_db = make_after_db(tmp_path / f"after_wrong_{task_no}.db", task_no, seed_db)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong answer must FAIL"


# ------------------------------------------------- state-mismatch (self-reported success, DB clean)
STATEFUL = [2, 5, 6, 9, 14, 17]


@pytest.mark.parametrize("task_no", STATEFUL)
def test_state_mismatch_fails(task_no, tmp_path, seed_db):
    """Agent claims success in the final answer but the DB is untouched."""
    run_dir = build_honest_run(tmp_path / f"stale_{task_no}", task_no)
    after_db = shutil.copyfile(seed_db, tmp_path / f"after_stale_{task_no}.db")
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "state-mismatch (clean DB) must FAIL"


# ------------------------------------------------- read-only violation
@pytest.mark.parametrize("task_no", [0, 1, 3, 4, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19])
def test_readonly_violation_fails(task_no, tmp_path, seed_db):
    """Read-only task but the DB was mutated: must FAIL."""
    run_dir = build_honest_run(tmp_path / f"dirty_{task_no}", task_no)
    after_db = make_after_db(tmp_path / f"after_dirty_{task_no}.db", task_no, seed_db)
    con = sqlite3.connect(after_db)
    con.execute("INSERT INTO pickup_requests (confirmation_number, user_id, "
                "contact_name, email, company, address_line1, city, state, zip, "
                "phone, pickup_date, earliest_time, latest_time, packages, "
                "weight_lb, service, saturday, fee_usd, payment, status) VALUES "
                "('PK9999999', NULL, 'X', 'x@x.com', 'X', '1 Main St', 'NY', "
                "'NY', '10001', '5550000', '2026-09-29', '9:00 AM', '5:00 PM', "
                "1, 1.0, 'UPS Ground', 0, 9.65, 'cash', 'Scheduled')")
    con.commit()
    con.close()
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "read-only violation must FAIL"


# ------------------------------------------------- pre-mutated seed (tampered initial DB)
@pytest.mark.parametrize("task_no", [0, 5])
def test_tampered_seed_fails(task_no, tmp_path, seed_db):
    """Run graded against a pre-mutated initial DB: seed gate must FAIL."""
    dirty = make_dirty_seed(tmp_path / f"dirty_seed_{task_no}.db", seed_db)
    run_dir = build_honest_run(tmp_path / f"t_{task_no}", task_no)
    after_db = make_after_db(tmp_path / f"after_t_{task_no}.db", task_no, dirty)
    verdict = run_verifier(task_no, run_dir, dirty, after_db)
    assert not verdict["pass"], "tampered seed must FAIL"


# ------------------------------------------------- off-site / wrong-port navigation
@pytest.mark.parametrize("task_no", [1, 19])
def test_offsite_navigation_fails(task_no, tmp_path, seed_db):
    """Trajectory contains an off-site URL: must FAIL."""
    rb = RunBuilder(tmp_path / f"off_{task_no}", f"UPS--{task_no}")
    for u in SPECS[task_no]["urls"]:
        rb.add_step("navigate", BASE + u)
    rb.add_step("navigate", "https://example.com/ups")
    run_dir = rb.write(SPECS[task_no]["answer"])
    after_db = make_after_db(tmp_path / f"after_off_{task_no}.db", task_no, seed_db)
    verdict = run_verifier(task_no, run_dir, seed_db, after_db)
    assert not verdict["pass"], "off-site navigation must FAIL"


# ------------------------------------------------- missing screenshots
def test_missing_screenshots_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "noshots", "UPS--3")
    rb.add_step("navigate", BASE + "/ctc", shot=False)
    run_dir = rb.write(SPECS[3]["answer"])
    after_db = shutil.copyfile(seed_db, tmp_path / "after_noshots.db")
    verdict = run_verifier(3, run_dir, seed_db, after_db)
    assert not verdict["pass"], "missing screenshots must FAIL"


# ------------------------------------------------- wrong task id
def test_wrong_task_id_fails(tmp_path, seed_db):
    rb = RunBuilder(tmp_path / "badtid", "UPS--5")
    for u in SPECS[5]["urls"]:
        rb.add_step("navigate", BASE + u)
    traj = json.loads((rb.root / "trajectory.json").read_text()) \
        if (rb.root / "trajectory.json").exists() else None
    run_dir = rb.write(SPECS[5]["answer"])
    # rewrite with the wrong task id
    t = json.loads((run_dir / "trajectory.json").read_text())
    t["task_id"] = "UPS--9"
    (run_dir / "trajectory.json").write_text(json.dumps(t, indent=1))
    after_db = make_after_db(tmp_path / "after_tid.db", 5, seed_db)
    verdict = run_verifier(5, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong task_id must FAIL"


# ------------------------------------------------- task-specific attacks
def test_t2_wrong_hold_location_fails(tmp_path, seed_db):
    """Hold confirmed at the WRONG location (Deepchhaya, not the UPS Store):
    both the confirmation text and the DB contract must FAIL it."""
    answer = ("Held at Deepchhaya Deli & Grocery, 334 W 37th St, 0.3 miles. "
              "Confirmation: 'Delivery changed: the package will be held for "
              "pickup at Deepchhaya Deli & Grocery, 334 W 37Th St, New York, "
              "NY 10018.' The location's city is New York, NY and ground "
              "drop-off is Mon-Sat: 4:00pm.")
    rb = RunBuilder(tmp_path / "t2wrong", "UPS--2")
    for u in SPECS[2]["urls"]:
        rb.add_step("navigate", BASE + u)
    run_dir = rb.write(answer)
    after_db = make_after_db(tmp_path / "after_t2w.db", 2, seed_db)
    con = sqlite3.connect(after_db)
    con.execute("UPDATE tracking_changes SET detail='152025'")
    con.execute("UPDATE shipments SET hold_location_id='152025' "
                "WHERE tracking_number='1Z58F0E70312456012'")
    con.commit()
    con.close()
    verdict = run_verifier(2, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong hold location must FAIL"


def test_t5_foreign_tracking_number_fails(tmp_path, seed_db):
    """Answer reports a tracking number that is not the wizard's row."""
    answer = ("Tracking number 1Z9999999999999999, scheduled delivery 2026-10-01, "
              "declared value charge $17.00, resolves as Label Created.")
    rb = RunBuilder(tmp_path / "t5wrong", "UPS--5")
    for u in SPECS[5]["urls"]:
        rb.add_step("navigate", BASE + u)
    run_dir = rb.write(answer)
    after_db = make_after_db(tmp_path / "after_t5w.db", 5, seed_db)
    verdict = run_verifier(5, run_dir, seed_db, after_db)
    assert not verdict["pass"], "foreign tracking number must FAIL"


def test_t7_wrong_ap_phone_fails(tmp_path, seed_db):
    """Reporting the SECOND-closest Access Point's phone as the closest AP's
    phone: the closest AP lists no phone, so this must FAIL."""
    answer = ("20 locations, 2 Access Points, 8 Drop Boxes. Nearest drop box "
              "Tishman Speyer, 66 Hudson Blvd E, ground drop-off Mon-Fri: "
              "1:30pm. Closest UPS Store phone 2124577300. Closest UPS Access "
              "Point: Deepchhaya Deli & Grocery, 334 W 37th St, phone "
              "2122442681.")
    rb = RunBuilder(tmp_path / "t7wrong", "UPS--7")
    for u in SPECS[7]["urls"]:
        rb.add_step("navigate", BASE + u)
    run_dir = rb.write(answer)
    after_db = shutil.copyfile(seed_db, tmp_path / "after_t7w.db")
    verdict = run_verifier(7, run_dir, seed_db, after_db)
    assert not verdict["pass"], "misattributed AP phone must FAIL"


def test_t11_wrong_cheapest_fails(tmp_path, seed_db):
    """Claims Day-Specific Pickup is cheapest (it is $23.25; Smart Pickup at
    $18.50 is the cheapest): must FAIL."""
    answer = ("Carol Diaz lists 3 shipments. Daily Pickup $39.00, Smart Pickup "
              "$18.50, Day-Specific 3 days $23.25 — the cheapest for a 3-day "
              "shop is Day-Specific Pickup at $23.25/week. On-Call: $9.65 "
              "future-day, $15.75 same-day. Smart Pickup Saturday $8.00.")
    rb = RunBuilder(tmp_path / "t11wrong", "UPS--11")
    for u in SPECS[11]["urls"]:
        rb.add_step("navigate", BASE + u)
    run_dir = rb.write(answer)
    after_db = shutil.copyfile(seed_db, tmp_path / "after_t11w.db")
    verdict = run_verifier(11, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong cheapest-pickup conclusion must FAIL"


def test_t13_second_oldest_reading_fails(tmp_path, seed_db):
    """The double-reading trap: reporting the second-OLDEST scan (Origin Scan,
    Toronto) instead of the second-to-LAST scan (Departed, Louisville): must
    FAIL — the frozen reading is penultimate-in-time."""
    answer = ("Label Created means we've received the shipment details and "
              "billing information from the sender. Long-distance shipments "
              "likely won't be scanned again until they reach their destination "
              "hub. Second-to-last scan: Origin Scan at Toronto, ON, CA on "
              "2026-09-24; scheduled delivery 2026-10-02; service UPS Ground. "
              "Nearest drop box Tishman Speyer, ground drop-off Mon-Fri: "
              "1:30pm.")
    rb = RunBuilder(tmp_path / "t13wrong", "UPS--13")
    for u in SPECS[13]["urls"]:
        rb.add_step("navigate", BASE + u)
    run_dir = rb.write(answer)
    after_db = shutil.copyfile(seed_db, tmp_path / "after_t13w.db")
    verdict = run_verifier(13, run_dir, seed_db, after_db)
    assert not verdict["pass"], "second-oldest misreading must FAIL"


def test_t18_carrier_on_packship_fails(tmp_path, seed_db):
    """Claims the Pack and Ship page says customers can choose their carrier:
    that statement is not on the page; must FAIL."""
    answer = ("In-store services: Notary, Passport Photos, Shredding. Mailbox "
              "customers get: We Sign for Packages, We Accept All Carriers, "
              "Receive Delivery Text Alerts, Prevent Porch Pirates, 24-hour "
              "access. The Pack and Ship page says you can choose your carrier "
              "of choice for every shipment. 5 UPS Stores within 15 miles of "
              "10001; closest The UPS Store, 337 10th Ave.")
    rb = RunBuilder(tmp_path / "t18wrong", "UPS--18")
    for u in SPECS[18]["urls"]:
        rb.add_step("navigate", BASE + u)
    run_dir = rb.write(answer)
    after_db = shutil.copyfile(seed_db, tmp_path / "after_t18w.db")
    verdict = run_verifier(18, run_dir, seed_db, after_db)
    assert not verdict["pass"], "fabricated carrier-choice claim must FAIL"


def test_t8_wrong_counts_fails(tmp_path, seed_db):
    """Wrong multi-package counts (2 packages / 2 delivered): must FAIL."""
    answer = ("The Seattle shipment contains 2 packages, both delivered, signed "
              "for by T. OLSEN on 2026-09-26. Package 2's latest scan: Out for "
              "Delivery at Tukwila, WA. Track page status Delivered, facility "
              "Seattle, WA.")
    rb = RunBuilder(tmp_path / "t8wrong", "UPS--8")
    for u in SPECS[8]["urls"]:
        rb.add_step("navigate", BASE + u)
    run_dir = rb.write(answer)
    after_db = shutil.copyfile(seed_db, tmp_path / "after_t8w.db")
    verdict = run_verifier(8, run_dir, seed_db, after_db)
    assert not verdict["pass"], "wrong package counts must FAIL"
