"""Deterministic verifier contract tests for the 21 tumblr tasks.

Covers, per task: the honest trajectory (from the reviewer's live runs,
frozen in _support.honest_steps) MUST PASS; a no-op run (homepage only,
empty answer, clean DB) MUST FAIL; a knowledge-shortcut (correct answer +
honest delta, homepage-only navigation) MUST FAIL; a wrong answer MUST
FAIL; a state-mismatch (honest claim, un-mutated DB) MUST FAIL for stateful
tasks. Read-only tasks MUST FAIL on a mutated after-DB. Package tampering
(task_id mismatch, non-done trajectory) MUST fail closed.

No LLM: snapshots are seed copies mutated through sqlite, trajectories are
written in the agent_demo/agent.py shape.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import (honest_run, mutated_readonly_run,  # noqa: E402
                      noop_run, run_verifier, shortcut_run, state_mismatch_run,
                      wrong_answer_run, RunBuilder, BASE)

READ_ONLY = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
STATEFUL = set(range(10, 21))
ALL = sorted(READ_ONLY | STATEFUL)

# plausible-but-wrong answers per task (contradict the frozen ground truth)
WRONG_ANSWERS = {
    0: "The top tag is #art with 39M followers and 9.1K new posts today. "
       "The related tag is #painting with 40 new. The newest post is by "
       "meolog with 12 notes, first tag #art; the blog has 40 posts.",
    1: "The first trending post is by sparth with 2.9K notes; opened it "
       "shows 1,000 likes and 500 reblogs. Page 2's first post is by meolog "
       "with 3.4K notes, opening 'hello world', tags #art and #space.",
    2: "The Top tab shows 25 results; the matching blogs are waneella and "
       "graylure. The newest Recent post is by 8pxl with 100 notes; its "
       "tags are #pixel and #art and it has 50 likes.",
    3: "NASA's blog is titled NASA Space with 2,000 posts, updated 30 days "
       "ago. March 2026 has the most posts with 20. The opened post has "
       "999,999 notes and summary 'Mars landing'.",
    4: "The staff post shows 300,000 notes, 90,000 likes and 150,000 "
       "reblogs; it opens 'Welcome to Tumblr'. The likers are alice and "
       "bob; the first reblog is nasa. The staff blog has 1,000 posts, "
       "updated 2 days ago, and its newest post's first tag is #staff.",
    5: "The ask was from art-lover-99 asking 'how do you draw'; the answer "
       "starts 'Thanks a lot'. It has 999 notes and tags #art #drawing. "
       "The blog has 500 posts; the newest archive month is August 2026 "
       "with 9 posts.",
    6: "The provider is YouTube; the tags are #rocket and #launch; the post "
       "titled 'Flight Test Like a NASA Engineer!' has 1,881 notes with 999 "
       "likes and 111 reblogs. NASA's blog has 1,758 posts, updated "
       "yesterday; the newest archive month is October 2026 with 10 posts.",
    7: "The trail is alice → bob → carol; the summary is 'cats are great'; "
       "it has 1,000 notes with 5 likes and 9 reblogs and opens 'Once upon a "
       "time'. The original blog is 'Yellow Submarine' with 10 posts, "
       "updated 2 years ago.",
    8: "The dashboard shows 5 posts from alice and bob; the newest post is "
       "'hello tumblr' with 10 notes, 1 like, 1 reblog and 2 notes total.",
    9: "Alice has liked 30 posts. The most recent is by waneella, 'pixel "
       "city', with 5K notes; its first tag is #pixelart, with 100 likes, "
       "20 reblogs and 5,000 total notes.",
    10: "Alice follows 4 blogs: cabinporn, nasa, staff, meolog. After "
        "unfollowing she has 3; after refollowing the page shows 4 blogs.",
    11: "The first trending post is by nasa with 100 notes; after liking it "
        "shows 101. The Likes page top is NASA's rabbit-holes post.",
    12: "The pixel-art blog is puffychi; the reblog comment was 'maybe "
        "later' and it carried the tags #pixel and #art over.",
    13: "The last suggested blog is 'Neon Dreams' with no description, about "
        "cyberpunk cities. After following, the dashboard's newest post is "
        "a NASA moon post.",
    14: "The last staff message was 'Welcome to Tumblr!'. The reply "
        "confirmation said 'Message deleted' and my message never appeared.",
    15: "The ask confirmation said 'Ask failed'. Alice's inbox was empty.",
    16: "The Activity badge showed 9. The notifications were: nasa liked "
        "your post, staff reblogged it, bob-c followed you. The newest was "
        "5 minutes ago. The Inbox badge showed 7 and the Activity badge "
        "still shows 9 afterwards.",
    17: "Published 'Cabin Dreams' about a fireplace with tag #cozy; the "
        "tag page showed 0 posts.",
    18: "The quote post published 'Art is life' by Anonymous with the tag "
        "#art.",
    19: "The blog title now reads 'bob's art gallery'; the username is "
        "robert, it shows 10 posts, newest summary 'sketch dump', and the "
        "archive's newest month is January 2026.",
    20: "Registered harbor-tester but landed on Explore. After following "
        "NASA the dashboard showed the 'Kodak Ektar 100' post with 556 "
        "notes.",
}


# ---------------------------------------------------------------- honest PASS
@pytest.mark.parametrize("task_no", ALL)
def test_honest_pass(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    verdict = run_verifier(task_no, run, expect_pass=True)
    assert verdict["reason"] == "all checks passed"


# ---------------------------------------------------------------- no-op FAIL
@pytest.mark.parametrize("task_no", ALL)
def test_noop_fails(tmp_path, task_no):
    run = noop_run(tmp_path, task_no)
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- shortcut FAIL
@pytest.mark.parametrize("task_no", ALL)
def test_shortcut_fails(tmp_path, task_no):
    run = shortcut_run(tmp_path, task_no)
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- wrong answer FAIL
@pytest.mark.parametrize("task_no", ALL)
def test_wrong_answer_fails(tmp_path, task_no):
    run = wrong_answer_run(tmp_path, task_no, WRONG_ANSWERS[task_no])
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- state mismatch FAIL
@pytest.mark.parametrize("task_no", sorted(STATEFUL))
def test_state_mismatch_fails(tmp_path, task_no):
    run = state_mismatch_run(tmp_path, task_no)
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- read-only mutation FAIL
@pytest.mark.parametrize("task_no", sorted(READ_ONLY))
def test_readonly_mutation_fails(tmp_path, task_no):
    run = mutated_readonly_run(tmp_path, task_no)
    run_verifier(task_no, run, expect_pass=False)


# ---------------------------------------------------------------- tamper fail-closed
@pytest.mark.parametrize("task_no", ALL[:3])
def test_task_id_mismatch_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    traj = json.loads((run / "trajectory.json").read_text())
    traj["task_id"] = "Tumblr--99"
    (run / "trajectory.json").write_text(json.dumps(traj))
    run_verifier(task_no, run, expect_pass=False)


@pytest.mark.parametrize("task_no", ALL[:3])
def test_not_done_fails(tmp_path, task_no):
    run = honest_run(tmp_path, task_no)
    traj = json.loads((run / "trajectory.json").read_text())
    traj["terminated"] = "error"
    (run / "trajectory.json").write_text(json.dumps(traj))
    run_verifier(task_no, run, expect_pass=False)


def test_offsite_url_fails(tmp_path):
    run = honest_run(tmp_path, 1)
    traj = json.loads((run / "trajectory.json").read_text())
    traj["steps"].append({"n": 99, "action": "navigate", "target": "evil",
                          "url": "http://93.184.216.34/exploit", "params": {}})
    traj["final_url"] = "http://93.184.216.34/exploit"
    (run / "trajectory.json").write_text(json.dumps(traj))
    run_verifier(1, run, expect_pass=False)


def test_missing_screenshots_fail(tmp_path):
    run = honest_run(tmp_path, 2)
    shutil.rmtree(run / "screenshots")
    run_verifier(2, run, expect_pass=False)


def test_honest_answer_zero_false_positive_check(tmp_path):
    """An honest run for task 11 must NOT pass the task-12 verifier and vice
    versa (cross-task answer leakage guard)."""
    run = honest_run(tmp_path, 11)
    verdict = run_verifier(12, run, expect_pass=False)
    assert verdict["pass"] is False
