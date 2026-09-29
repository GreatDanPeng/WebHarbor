#!/usr/bin/env python3
"""Deterministic verifier for Virginia DMV--9 (virginia_dmv).

Ground truth below is HARDCODED (frozen from the fix-branch honest Playwright
walks on the fix container wh-vadm-fix, seed md5 e20897642a951494ced5ad6393a78ad7,
task text as deepened in the r1-fix commit) — never read from tasks.jsonl.
Usage: python3 verify_9.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_ordered,
    check_answer_money_after, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Virginia DMV--9"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    # knowledge exam retake rules + vision/permit facts + Safe Driving exam
    check_visited_path(judge, traj, "nav_exams", r"/licenses-ids/exams")
    check_visited_path(judge, traj, "nav_manual_exam", r"/drivers-manual/1/1")
    check_visited_path(judge, traj, "nav_road_skills", r"/drivers-manual/1/2")
    check_visited_path(judge, traj, "nav_vision", r"/drivers-manual/1/3")
    check_visited_path(judge, traj, "nav_license_types", r"/drivers-manual/6/1")
    check_visited_path(judge, traj, "nav_permit_apply", r"/licenses-ids/learners/apply")
    check_visited_path(judge, traj, "nav_practice_landing", r"/licenses-ids/exams/practice-exam")
    check_visited_path(judge, traj, "nav_practice_section", r"/licenses-ids/exams/practice-exam/3")
    check_visited_path(judge, traj, "nav_practice_grade", r"/licenses-ids/exams/practice-exam/3/grade")
    check_answer_number(judge, answer, "retake_wait_days", 15)
    check_answer_any(judge, answer, "worked_example", ["january 17", "jan. 17", "jan 17"])
    check_answer_any(judge, answer, "exam_frequency", ["once per business day", "only once per business day", "one time per business day"])
    check_answer_any(judge, answer, "sign_rule", ["all ten sign questions", "all ten traffic sign questions", "all ten questions", "all 10 sign questions"])
    check_answer_any(judge, answer, "part_two_rule", ["24 correct answers", "24 questions", "80 percent", "80%"])
    check_answer_any(judge, answer, "audio_version", ["audio version of the exam is available", "an audio version", "audio version"])
    check_answer_count_at_least(judge, answer, "exempt_licenses", ["canada", "germany", "france", "republic of korea", "south korea", "u.s. state"], 4)
    check_answer_any(judge, answer, "road_skills_extra", ["taiwan"])
    check_answer_any(judge, answer, "vision_standard", ["20/40"])
    check_answer_any(judge, answer, "restriction_code", ["restriction code c", "display a c", "code c", "a c for this restriction", "c for this restriction"])
    check_answer_any(judge, answer, "holding_period", ["minimum of 60 days", "60 days", "sixty days"])
    check_answer_any(judge, answer, "permit_companion", ["at least 21", "21 years of age", "21 or older"])
    # agent-dependent exam score: internal consistency for the 8-question exam
    import re as _re
    m = _re.search(r"(\d{1,2})\s*/\s*8", answer)
    if not m:
        judge.fail("score_form", "answer lacks an N/8 score")
    else:
        score = int(m.group(1))
        if not (0 <= score <= 8):
            judge.fail("score_range", f"score {score} out of range")
        else:
            judge.ok("score_form", f"{score}/8")
        pct = _re.search(r"(\d{1,3})\s*(?:%|percent)", answer[m.end():m.end()+80])
        expect_pct = {0: 0, 1: 12, 2: 25, 3: 38, 4: 50, 5: 62, 6: 75, 7: 88, 8: 100}[score]
        if not pct:
            judge.fail("percentage_form", "answer lacks a percentage")
        elif int(pct.group(1)) != expect_pct:
            judge.fail("percentage_consistent", f"percentage {pct.group(1)} != {expect_pct}")
        else:
            judge.ok("percentage_consistent", f"{expect_pct}%")
        passed = ("passed" in answer.lower()
                  and "not passed" not in answer.lower())
        if passed != (score * 12.5 >= 80):
            judge.fail("passed_consistent", f"passed={passed} but score {score}/8")
        else:
            judge.ok("passed_consistent", str(passed))
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
