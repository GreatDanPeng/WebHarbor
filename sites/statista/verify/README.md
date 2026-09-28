# Statista deterministic grading (review track)

All 23 tasks in `../tasks.jsonl` have a rubric and a deterministic verifier.
Ground truth lives only in `task_specs.py` (imported by `verify_0.py` …
`verify_22.py`). `tasks.jsonl` keeps the task wording and adds
`verifier_path` plus a rules-only `judge_rubric`. There is no answer key.
`append_rubrics.py` refuses to run so a generator cannot copy figures back
into the agent-facing file.

- `verify_lib.py` validates task id, completion, loopback origin and port,
  decodable screenshots, and the SQLite seed contract. Schema digest
  `e3571669…`, rows digest `aa83591b…`. A host md5 is not the contract.
  Numbers match as standalone tokens and must sit nearer their subject than
  a competing subject, so a swapped year, country, or market fails.
- Stateful tasks allow a new Basic account or, where the task names one, a
  specific seed account. Favorites, downloads, and the contact inquiry are
  exact row deltas. Read-only tasks require row-identical snapshots.
- `tests/` covers honest fixtures plus no-op, wrong-answer, swapped-subject,
  substring-number, homepage-only shortcut, state-mismatch, wrong-delta,
  alternate-account, and package-tampering cases.

The seed DB is `instance_seed/statista.db` when that file is present;
`STATISTA_TEST_SEED_DB` overrides it.

```bash
python3 -m pytest sites/statista/tests sites/statista/verify/tests -q
```

The deterministic grader is primary. The optional LLM judge was not run
for this review.

Task notes:
- Task 13's first table-of-contents entry is the heading "Description".
  The harvested in-depth report reproduces that upstream anonymous view.
- Task 12 asks how many audiences are above 60 million (six countries).
  Four of those are also above 100 million; the verifier grades the
  threshold the question asks for.
- Task 18 does not grade a "more than 15 percent" count. LinkedIn at 15.2
  would make that count four, and the question does not ask it.
- Task 21 persists the contact form. A thank-you sentence with no inquiry
  row fails.
- Statistic 256626's region chart is recovered from the harvested labels.
  Statistic 439576 stores the country conversion table rather than the
  dummy operating-system series on that page.
