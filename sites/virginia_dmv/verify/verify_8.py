#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--8 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the reviewer's independent
Playwright honest walks on the review container wh-vadm-review, seed md5
e20897642a951494ced5ad6393a78ad7) — never read from tasks.jsonl.
Usage: python3 verify_8.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_ordered,
    check_answer_phrase, check_answer_regex, check_read_only,
    check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Virginia DMV--8"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # manual Traffic Signals + graded section-2 practice exam
    check_visited_path(judge, traj, "nav_manual_signals", r"/drivers-manual/2/1")
    check_visited_path(judge, traj, "nav_exam_section", r"/licenses-ids/exams/practice-exam/2")
    check_visited_path(judge, traj, "nav_exam_result", r"/licenses-ids/exams/practice-exam/2/grade")
    check_answer_any(judge, answer, "steady_red_rule",
                     ["come to a complete stop", "complete stop at the stop line",
                      "stop at the stop line", "complete stop before"])
    check_answer_any(judge, answer, "flashing_yellow_rule",
                     ["slow down and proceed with caution", "proceed with caution"])
    check_answer_number(judge, answer, "num_questions", 10)
    # score/percentage/passed must be internally consistent (agent-dependent
    # score: two section-2 questions carry upstream-faithful broken
    # correctAnswer values, so an honest perfect-knowledge run scores 8/10).
    import re as _re
    m = _re.search(r"(\d{1,2})\s*/\s*10", answer)
    if not m:
        judge.fail("score_form", "answer lacks an N/10 score")
    else:
        score = int(m.group(1))
        if not (0 <= score <= 10):
            judge.fail("score_range", f"score {score} out of range")
        else:
            judge.ok("score_form", f"{score}/10")
        pct = _re.search(r"(\d{1,3})\s*(?:%|percent)", answer)
        if not pct:
            judge.fail("percentage_form", "answer lacks a percentage")
        elif int(pct.group(1)) != score * 10:
            judge.fail("percentage_consistent", f"percentage {pct.group(1)} != {score*10}")
        else:
            judge.ok("percentage_consistent", f"{score*10}%")
        passed = "pass" in answer.lower()
        if passed != (score * 10 >= 80):
            judge.fail("passed_consistent", f"passed={passed} but score {score}/10")
        else:
            judge.ok("passed_consistent", str(passed))
    check_answer_count_at_least(judge, answer, "feedback_text",
        ["must stop", "stop until the light turns green", "stop, then drive on carefully",
         "you may turn right", "proceed with caution", "stop until the light changes",
         "flashing red", "lane use", "look both ways", "yield the right-of-way",
         "come to a complete stop", "traffic signals apply"], 1)
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
