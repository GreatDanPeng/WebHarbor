"""Shared fixtures for the u_s_customs verifier tests.

Snapshots are copies of the real seed (instance_seed/u_s_customs.db from the
review container wh-us-customs-review) with the per-task stateful mutations
applied through sqlite, and trajectories are written in the agent_demo/agent.py
shape from the frozen SPECS (transcribed from the reviewer's honest live
runs). No LLM.

The seed DB resolves from the review container (wh-us-customs-r2review); the
US_CUSTOMS_TEST_SEED_DB env var overrides the location. Run with plain
python3 + pytest:

    python3 -m pytest sites/u_s_customs/verify/tests -q
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
CONTAINER = os.environ.get("WH_CONTAINER", "wh-us-customs-r2review")
CACHE = Path(os.environ.get("US_CUSTOMS_TEST_SEED_DB") or
             str(Path("/tmp") / "us_customs_verify_tests_seed.db"))
TASKS_FILE = SITE_DIR / "tasks.jsonl"


def acquire_seed() -> Path:
    if CACHE.is_file():
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["docker", "cp",
                        f"{CONTAINER}:/opt/WebSyn/u_s_customs/instance_seed/u_s_customs.db",
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
            "title": "U.S. Customs and Border Protection",
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
        (self.shots_dir / "step_000.png").write_bytes(PNG)
        traj = {
            "task": task_ques(self.task_id),
            "task_id": task_id or self.task_id,
            "start_url": start_url or (BASE + self.start_path),
            "model": "test-fixture",
            "max_steps": 100,
            "steps": self.steps,
            "terminated": terminated,
            "termination_reason": reason if terminated else None,
            "final_answer": answer,
            "judge_rubric": "",
            "verifier_path": "",
        }
        (self.root / "trajectory.json").write_text(json.dumps(traj, indent=2))
        return self.root


# ------------------------------------------------------------------ db snapshots
def make_after_db(dest: Path, task_no: int) -> Path:
    """Copy the seed and apply the honest per-task mutation."""
    seed = acquire_seed()
    shutil.copyfile(seed, dest)
    if not SPECS[task_no]["mutations"]:
        return dest
    db = sqlite3.connect(dest)
    try:
        for _table, sql in SPECS[task_no]["mutations"]:
            db.execute(sql)
        db.commit()
    finally:
        db.close()
    return dest


def run_verifier(task_no: int, run_dir: Path, initial_db: Path, after_db: Path):
    """Run verify_<task_no>.py as a subprocess; return the verdict dict."""
    script = VERIFY_DIR / f"verify_{task_no}.py"
    r = subprocess.run(
        [sys_python(), str(script), "--run_dir", str(run_dir),
         "--initial_db", str(initial_db), "--after_db", str(after_db)],
        capture_output=True, text=True)
    try:
        verdict = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise AssertionError(f"verifier crashed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return verdict


def sys_python() -> str:
    import sys
    return sys.executable
