#!/usr/bin/env python3
"""u_s_customs fix-round walker — real-Chromium honest walkthroughs of all 21
tasks (contribute-side measured step counts).

Every task: control-plane reset -> fresh browser context (clean cookies) ->
drive the natural honest path through the real UI (clicks/fills/selects) ->
record per-step screenshots + initial/after DB snapshots -> honest step
counts (atomic + A-style). Step counting follows the frozen review
convention (matches wh-qatar / wh-trip_com / the u_s_customs review):

  atomic : each goto / click / fill / select / submit = 1 (strict lower bound)
  A      : atomic + each distinct required fact read-and-reported = 1
           (NAV+FILL+SELECT+SUBMIT+SCAN+READ; initial page load never counted)

Output: walk_summary_<N>.json per task under scripts_dev/walk_fix/ plus full
artifacts (screenshots / trajectories / DB snapshots) under
$US_CUSTOMS_FIX_EVIDENCE (outside the repo, like the review evidence).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:43105"
CTRL = "http://localhost:44105"
CONTAINER = "wh-us-customs-dev"
SITE_ROOT = Path(__file__).resolve().parents[2]
WALK_DIR = Path(__file__).resolve().parent
EV = Path(os.environ.get(
    "US_CUSTOMS_FIX_EVIDENCE",
    "/data/zhaoyang-user-projects/websyn/wh-us-customs-fix-evidence"))
RUNS = EV / "runs"
TOKEN = (EV / "control_token").read_text().strip()

TASKS = {json.loads(l)["id"]: json.loads(l)
         for l in (SITE_ROOT / "tasks.jsonl").read_text().strip().splitlines()}


class Walk:
    """One task walkthrough with trajectory recording."""

    def __init__(self, task_id, page):
        self.task_id = task_id
        self.page = page
        self.steps = []
        self.reads = []          # distinct facts read-and-reported (A-style)
        self.shot_idx = 0
        self.task = TASKS[task_id]

    # -- infrastructure -----------------------------------------------------
    def shot(self, label=""):
        name = f"step_{self.shot_idx:03d}.png"
        self.page.screenshot(path=str(self.run_dir / "screenshots" / name), full_page=False)
        self.shot_idx += 1
        return name

    def begin(self):
        self.run_dir = RUNS / self.task_id.replace("CBP.gov--", "")
        (self.run_dir / "screenshots").mkdir(parents=True, exist_ok=True)
        # capture initial DB (post-reset instance == seed)
        subprocess.run(["docker", "cp", f"{CONTAINER}:/opt/WebSyn/u_s_customs/instance/u_s_customs.db",
                        str(self.run_dir / "initial.db")], check=True)
        self.steps = []
        self.reads = []
        self.shot_idx = 0
        self.page.goto(BASE + "/", wait_until="domcontentloaded")
        self.page.wait_for_timeout(400)
        self.shot()  # step_000 = home (never counted)

    def end(self, answer):
        self.answer = answer
        subprocess.run(["docker", "cp", f"{CONTAINER}:/opt/WebSyn/u_s_customs/instance/u_s_customs.db",
                        str(self.run_dir / "after.db")], check=True)
        name = self.shot()
        traj = {
            "task": self.task["ques"],
            "task_id": self.task_id,
            "start_url": BASE + "/",
            "model": "contributor-walker",
            "max_steps": 100,
            "steps": self.steps,
            "terminated": True,
            "termination_reason": "agent_done",
            "final_answer": answer,
            "judge_rubric": "",
            "verifier_path": "",
        }
        (self.run_dir / "trajectory.json").write_text(json.dumps(traj, indent=2))
        summary = {
            "task_id": self.task_id,
            "atomic": len(self.steps),
            "A": len(self.steps) + len(self.reads),
            "reads": self.reads,
            "actions": [f"{s['action']}:{json.dumps(s['params'])[:60]}" for s in self.steps],
            "answer": answer,
        }
        (self.run_dir / "walk_summary.json").write_text(json.dumps(summary, indent=2))
        (WALK_DIR / f"walk_summary_{self.task_id.split('--')[1]}.json").write_text(
            json.dumps(summary, indent=2))
        print(f"[{self.task_id}] atomic={len(self.steps)} A={len(self.steps)+len(self.reads)} reads={len(self.reads)}")
        return summary

    # -- actions (each records one step) -----------------------------------
    def _rec(self, action, params, url_before):
        self.page.wait_for_timeout(250)
        url_after = self.page.url
        title = self.page.title()
        text = self.page.evaluate("() => document.body ? document.body.innerText.slice(0, 20000) : ''")
        name = self.shot()
        self.steps.append({
            "step": len(self.steps),
            "url": url_before,
            "url_after": url_after,
            "title": title,
            "action": action,
            "params": params,
            "observed_text": text,
            "observed_text_before": text,
            "observed_text_after": text,
            "screenshot_before": self.steps[-1]["screenshot_after"] if self.steps else "step_000.png",
            "screenshot_after": name,
        })
        if self.steps:
            self.steps[-1]["screenshot_before"] = self.steps[-2]["screenshot_after"] if len(self.steps) > 1 else "step_000.png"
        return url_after

    def _sel(self, selector):
        loc = self.page.locator(selector)
        return loc.first

    def click(self, selector, desc=""):
        url_before = self.page.url
        el = self._sel(selector)
        el.scroll_into_view_if_needed(timeout=8000)
        el.click(timeout=8000)
        return self._rec("click", {"selector": selector, "desc": desc}, url_before)

    def goto(self, path, desc=""):
        url_before = self.page.url
        self.page.goto(BASE + path if path.startswith("/") else path, wait_until="domcontentloaded")
        return self._rec("navigate", {"url": path, "desc": desc}, url_before)

    def fill(self, selector, text, desc=""):
        url_before = self.page.url
        el = self._sel(selector)
        el.scroll_into_view_if_needed(timeout=8000)
        el.fill(text, timeout=8000)
        return self._rec("input", {"selector": selector, "text": text, "desc": desc}, url_before)

    def select(self, selector, value, desc=""):
        url_before = self.page.url
        el = self._sel(selector)
        el.scroll_into_view_if_needed(timeout=8000)
        el.select_option(value, timeout=8000)
        return self._rec("select_dropdown", {"selector": selector, "text": value, "desc": desc}, url_before)

    def submit(self, selector, desc=""):
        url_before = self.page.url
        el = self._sel(selector)
        el.scroll_into_view_if_needed(timeout=8000)
        el.click(timeout=8000)
        return self._rec("click", {"selector": selector, "desc": desc or "submit"}, url_before)

    def read(self, fact, value):
        """Record a distinct required fact read from the current page."""
        self.reads.append({"fact": fact, "value": value})

    def body(self):
        return self.page.evaluate("() => document.body ? document.body.innerText : ''")

    def html(self):
        return self.page.content()


def reset_site():
    subprocess.run(["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {TOKEN}",
                    CTRL + "/reset/u_s_customs"], check=True, capture_output=True)
    time.sleep(6)
    # wait until alive
    for _ in range(20):
        r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", BASE + "/_health"],
                           capture_output=True, text=True)
        if r.stdout.strip() == "200":
            return
        time.sleep(1)
    raise RuntimeError("site did not come back after reset")
