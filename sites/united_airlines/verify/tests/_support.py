"""Shared fixtures for the united_airlines verifier tests.

The seed DB resolves from the rereview container
(wh-united-airlines-rereview); the UNITED_AIRLINES_TEST_SEED_DB env var
overrides the location. After-state DBs are copies of the seed with the
per-task stateful mutations applied through sqlite (the exact writes the
site itself performs), and trajectories are written in the agent_demo/agent.py
shape from the frozen SPECS (transcribed from the reviewer's honest live
runs). No LLM.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import zlib
from pathlib import Path

from fixtures_data import BASE, SPECS  # noqa: E402  (same directory)

VERIFY_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = VERIFY_DIR.parent
CONTAINER = os.environ.get("WH_CONTAINER", "wh-united-airlines-rereview")
CACHE = Path(os.environ.get("UNITED_AIRLINES_TEST_SEED_DB") or
             str(Path("/tmp") / "united_airlines_verify_tests_seed.db"))
TASKS_FILE = SITE_DIR / "tasks.jsonl"


def acquire_seed() -> Path:
    if CACHE.is_file():
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["docker", "cp",
                        f"{CONTAINER}:/opt/WebSyn/united_airlines/instance_seed/united_airlines.db",
                        str(CACHE)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cannot acquire the seed DB (docker cp failed): {r.stderr[:200]}")
    return CACHE


def task_ques(task_id: str) -> str:
    for line in TASKS_FILE.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["id"] == task_id:
            return row["ques"]
    raise KeyError(task_id)


# ------------------------------------------------------------------ tiny valid PNG
def tiny_png(width: int = 4, height: int = 4) -> bytes:
    raw = b"".join(b"\x00" + b"\x40\x90\xd0" * width for _ in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (len(data).to_bytes(4, "big") + tag + data
                + zlib.crc32(tag + data).to_bytes(4, "big"))

    ihdr = width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


PNG = tiny_png()


# ------------------------------------------------------------------ run-dir builder
class RunBuilder:
    """Writes an agent_demo-shaped run directory: trajectory.json + screenshots/."""

    def __init__(self, root: Path, task_id: str, start_path: str = "/"):
        self.root = root
        self.shots_dir = root / "screenshots"
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        self.task_id = task_id
        self.start_path = start_path
        self.steps = []

    def add_step(self, action: str, url_after: str, params: dict | None = None) -> None:
        name = f"step_{len(self.steps) + 1:03d}.png"
        (self.shots_dir / name).write_bytes(PNG)
        self.steps.append({
            "step": len(self.steps),
            "url": BASE + self.start_path if not self.steps else self.steps[-1]["url_after"],
            "title": "United Airlines",
            "thought": f"{action} {url_after}",
            "action": action,
            "params": params or {},
            "observed_text": f"page text for {url_after}",
            "screenshot_before": self.steps[-1]["screenshot_after"] if self.steps else name,
            "screenshot_after": name,
            "url_after": url_after,
        })

    def write(self, answer: str, terminated=True, reason="agent_done",
              task_id=None, start_url=None) -> Path:
        traj = {
            "task_id": task_id or self.task_id,
            "start_url": start_url or (BASE + self.start_path),
            "steps": self.steps,
            "final_answer": answer,
            "terminated": terminated,
            "termination_reason": reason if terminated else "error",
        }
        (self.root / "trajectory.json").write_text(
            json.dumps(traj, indent=1), encoding="utf-8")
        return self.root


# ------------------------------------------------------------------ after-state DB
def make_after_db(dest: Path, task_no: int) -> Path:
    shutil.copyfile(acquire_seed(), dest)
    db = sqlite3.connect(dest)
    try:
        for sql in SPECS[task_no]["sql"]:
            db.execute(sql)
        db.commit()
    finally:
        db.close()
    return dest


def make_dirty_seed(dest: Path) -> Path:
    """A pre-mutated 'initial' DB: one extra passenger row. The seed gate
    must reject any run graded against it."""
    shutil.copyfile(acquire_seed(), dest)
    db = sqlite3.connect(dest)
    try:
        db.execute("INSERT INTO passengers (id,booking_id,first_name,last_name,title,"
                   "date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
                   "VALUES (99,1,'Ghost','Rider','Mr','1990-01-01','Male','','',0,'')")
        db.commit()
    finally:
        db.close()
    return dest


def make_stale_after_db(dest: Path, task_no: int) -> Path:
    """After-DB missing the stateful write (stale DB attack)."""
    shutil.copyfile(acquire_seed(), dest)
    return dest


def _resolve(u):
    """Fixture URL resolution: @@OFFSITE@@ / @@CROSSPORT@@ build raw URLs."""
    if u == "@@OFFSITE@@":
        return "https://www.united.com/en/us"
    if u == "@@CROSSPORT@@":
        return "http://127.0.0.1:40098/"
    return BASE + u


# ------------------------------------------------------------------ runner
def run_verifier(task_no: int, run_dir: Path, initial_db: Path, after_db: Path) -> dict:
    import importlib
    import verify_lib
    mod = importlib.import_module(f"verify_{task_no}")
    argv_backup = importlib.sys.argv[:]
    importlib.sys.argv = [f"verify_{task_no}",
                          "--run_dir", str(run_dir),
                          "--initial_db", str(initial_db),
                          "--after_db", str(after_db)]
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            verify_lib.run_verifier(mod.TASK_ID, mod.run_checks)
    finally:
        importlib.sys.argv = argv_backup
    out = buf.getvalue().strip()
    verdict = json.loads(out) if out else {"pass": False, "reason": "no output"}
    return verdict
