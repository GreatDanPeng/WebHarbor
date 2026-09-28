#!/usr/bin/env python3
"""Write the thin per-task verifiers.

Ground truth lives in task_specs.py. This script does not copy answer
values into tasks.jsonl.
"""
from pathlib import Path

TEMPLATE = '''#!/usr/bin/env python3
"""Verify Statista--{n}."""
from task_specs import SPECS
from verify_lib import apply_spec, run_verifier

TASK_ID = "Statista--{n}"


def run_checks(judge, traj, initial_db, after_db):
    apply_spec(judge, traj, initial_db, after_db, SPECS[{n}], TASK_ID)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
'''


def main():
    here = Path(__file__).resolve().parent
    for n in range(23):
        (here / f"verify_{n}.py").write_text(TEMPLATE.format(n=n), encoding="utf-8")


if __name__ == "__main__":
    main()
