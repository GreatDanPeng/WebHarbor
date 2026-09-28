#!/usr/bin/env python3
"""Rubrics are maintained in ../tasks.jsonl.

This generator used to copy numeric ground truth into the agent-facing
task file. It now refuses to run.
"""
raise SystemExit(
    "refusing to rewrite tasks.jsonl; edit judge_rubric in that file directly"
)
