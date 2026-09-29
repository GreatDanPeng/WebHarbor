"""Shared test support for the ups verifier test suite."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY_DIR = HERE.parent
sys.path.insert(0, str(VERIFY_DIR))

import verify_lib  # noqa: E402

BASE = "http://localhost:40163"
CONTAINER = os.environ.get("WH_CONTAINER", "wh-ups-review")
PNG = (b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)

_seed_cache: Path | None = None


def acquire_seed() -> Path:
    """Seed DB from the pinned review container (cached for the session)."""
    global _seed_cache
    if _seed_cache and _seed_cache.is_file():
        return _seed_cache
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    inner = f"{CONTAINER}:/opt/WebSyn/ups/instance_seed/ups.db"
    r = subprocess.run(["docker", "cp", inner, path], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"docker cp {inner} failed: {r.stderr.strip()}")
    _seed_cache = Path(path)
    return _seed_cache


class RunBuilder:
    """Build an agent-style run dir: trajectory.json + screenshots/step_NNN.png."""

    def __init__(self, root: Path, task_id: str):
        self.root = Path(root)
        self.task_id = task_id
        (self.root / "screenshots").mkdir(parents=True, exist_ok=True)
        self.steps: list[dict] = []

    def add_step(self, action: str, url: str, shot: bool = True):
        n = len(self.steps) + 1
        name = f"step_{n:03d}.png"
        if shot:
            (self.root / "screenshots" / name).write_bytes(PNG)
        self.steps.append({
            "step": n, "url": url, "title": "", "thought": "",
            "action": action, "params": {}, "observed_text": "",
            "screenshot_before": None,
            "screenshot_after": name if shot else None,
            "url_after": url,
        })

    def write(self, answer: str, start_url: str = BASE + "/") -> Path:
        traj = {
            "task": self.task_id, "task_id": self.task_id,
            "start_url": start_url, "model": "test-fixture",
            "max_steps": len(self.steps), "steps": self.steps,
            "terminated": True, "termination_reason": "agent_done",
            "final_answer": answer,
            "final_url": self.steps[-1]["url"] if self.steps else start_url,
        }
        (self.root / "trajectory.json").write_text(json.dumps(traj, indent=1))
        return self.root


def run_verifier(task_no: int, run_dir: Path, initial_db: Path,
                 after_db: Path) -> dict:
    script = VERIFY_DIR / f"verify_{task_no}.py"
    r = subprocess.run(
        [sys.executable, str(script), "--run_dir", str(run_dir),
         "--initial_db", str(initial_db), "--after_db", str(after_db)],
        capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"task_id": f"UPS--{task_no}", "pass": False,
                "reason": f"verifier crashed: {r.stderr.strip()[-200:]}",
                "evidence": []}


def make_after_db(dest: Path, task_no: int, seed: Path) -> Path:
    """After-state DB for stateful tasks (exact expected writes), else a copy
    of the seed."""
    if task_no in (2, 17):
        shutil.copyfile(seed, dest)
        con = sqlite3.connect(dest)
        con.execute(
            "INSERT INTO tracking_events (shipment_id, seq, day, time, status, "
            "location, description, package_n) VALUES "
            "(1, 12, '2026-09-28', '—', 'Hold for Pickup Requested', 'New York, NY', "
            "'Delivery changed: the package will be held for pickup at The Ups Store, "
            "337 10Th Ave, New York, NY 10001. Bring a government-issued photo ID.', NULL)")
        con.execute(
            "INSERT INTO tracking_changes (shipment_id, change_type, detail, "
            "request_day) VALUES (1, 'hold', '255850', '2026-09-28')")
        con.execute(
            "UPDATE shipments SET hold_location_id='255850', hold_by='2026-10-05' "
            "WHERE tracking_number='1Z58F0E70312456012'")
        con.commit()
        con.close()
    elif task_no == 5:
        shutil.copyfile(seed, dest)
        con = sqlite3.connect(dest)
        con.execute(
            "INSERT INTO shipments (tracking_number, user_id, direction, service_code, "
            "shipper_name, from_city, from_state, to_name, to_city, to_state, to_zip, "
            "weight_lb, packages, signature, scheduled_delivery, status, declared_value, "
            "created_in_session) VALUES ('1Z5F71X90370000152', NULL, 'outbound', 'GND', "
            "'Alice Johnson', 'New York', 'NY', 'Bay Line Gifts', 'San Francisco', 'CA', "
            "'94105', 5.0, 1, 'Signature Required', '2026-10-01', 'Label Created', "
            "950.0, 1)")
        con.execute(
            "INSERT INTO tracking_events (shipment_id, seq, day, time, status, "
            "location, description, package_n) VALUES "
            "(15, 1, '2026-09-28', '—', 'Label Created', 'New York, NY', "
            "'Shipping information received by UPS. Drop off your package at a UPS "
            "location or hand it to a UPS driver to start its journey.', NULL)")
        con.commit()
        con.close()
    elif task_no == 6:
        shutil.copyfile(seed, dest)
        con = sqlite3.connect(dest)
        con.execute(
            "INSERT INTO pickup_requests (confirmation_number, user_id, contact_name, "
            "email, company, address_line1, city, state, zip, phone, pickup_date, "
            "earliest_time, latest_time, packages, weight_lb, service, saturday, "
            "fee_usd, payment, status) VALUES "
            "('PK1000001', 4, 'Dave Miller', 'dave.m@test.com', 'Dave Miller', "
            "'1701 South MoPac Expressway', 'Austin', 'TX', '78746', '5125550143', "
            "'2026-09-29', '9:00 AM', '5:00 PM', 1, 9.8, 'UPS Next Day Air Saver®', "
            "0, 9.65, 'Pay driver at pickup', 'Scheduled')")
        con.commit()
        con.close()
    elif task_no == 14:
        shutil.copyfile(seed, dest)
        con = sqlite3.connect(dest)
        con.execute(
            "INSERT INTO pickup_requests (confirmation_number, user_id, contact_name, "
            "email, company, address_line1, city, state, zip, phone, pickup_date, "
            "earliest_time, latest_time, packages, weight_lb, service, saturday, "
            "fee_usd, payment, status) VALUES "
            "('PK1000001', NULL, 'Alex Rivera', 'alex@example.com', 'Alex Rivera', "
            "'88 King Street', 'San Francisco', 'CA', '94107', '4155550117', "
            "'2026-10-03', '9:00 AM', '5:00 PM', 1, 5.0, 'UPS Ground', 1, 16.6, "
            "'Pay driver at pickup', 'Scheduled')")
        con.commit()
        con.close()
    elif task_no == 9:
        shutil.copyfile(seed, dest)
        con = sqlite3.connect(dest)
        con.execute(
            "INSERT INTO claims (claim_id, user_id, tracking_number, email, role, "
            "problem_type, merchandise, item_count, item_value, currency, status, "
            "events, filed_day, resolution_note) VALUES "
            "('CLM4000001', 1, '1Z58F0E70371234458', 'alice.j@test.com', 'receiver', "
            "'damaged', 'hand-thrown ceramic bowl set', 2, 180.0, 'USD', "
            "'Claim Review in Progress', '[]', '2026-09-28', "
            "'Unless additional investigation is required, you can typically expect "
            "a resolution to your claim in 8 to 10 business days.')")
        con.commit()
        con.close()
    else:
        shutil.copyfile(seed, dest)
    return dest


def make_dirty_seed(dest: Path, seed: Path) -> Path:
    """A pre-mutated 'initial' DB: not the frozen seed."""
    shutil.copyfile(seed, dest)
    con = sqlite3.connect(dest)
    con.execute("UPDATE shipments SET status='Delivered' "
                "WHERE tracking_number='1Z58F0E70312456012'")
    con.commit()
    con.close()
    return dest


def task_ques(task_no: int) -> str:
    rows = (VERIFY_DIR.parent / "tasks.jsonl").read_text().splitlines()
    return json.loads(rows[task_no])["ques"]
