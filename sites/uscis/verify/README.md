# uscis verifier suite (reviewer contract)

Deterministic, LLM-free verifiers for the 20 `USCIS.gov--*` benchmark tasks.
Written by the uscis reviewer on `orch/review/uscis`; ground truth is
**hardcoded** in `verify_<n>.py` — frozen from the reviewer's independent
Playwright walkthroughs of the review container `wh-uscis-review`
(seed md5 `e3b7b4f99717af8145217556ecf8fd44`), with the processing-times
values independently verified verbatim against the web.archive.org snapshots
of the real `egov.uscis.gov` API records and the news/glossary/fee anchors
verified against the live `www.uscis.gov` pages.

## Layout

- `verify_lib.py` — shared contract: package identity (task_id / agent_done /
  non-empty answer / same-origin same-port / decodable PNGs), seed identity
  gate (table counts + schema sha256 + rows sha256 pinning the independent
  in-image seed), navigation gates, answer token/phrase/number/money checks,
  office-range attribution coherence, and read-only / exact-delta DB
  after-state checks.
- `verify_0.py` … `verify_19.py` — one verifier per task; navigation gates +
  hardcoded ground truth + DB contract.
- `test_verifiers.py` — 98 pytest cases: 20 honest fixtures PASS; no-op,
  answer-only shortcut, wrong-answer, stale-DB, read-only-violation,
  tampered-package and task-specific-confusion negatives all FAIL
  (zero false positives).

## Usage

```bash
python3 sites/uscis/verify/verify_2.py --run_dir <trajectory_dir>
#   [--initial_db P] [--after_db P] [--container wh-uscis-review]
# prints {"task_id": ..., "pass": true/false, "reason": ..., "evidence": [...]}
```

`<trajectory_dir>` holds `trajectory.json` + `screenshots/step_NNN.png` +
`initial.db` + `after.db` (the agent_demo run shape).

## Seed reproducibility note

The seed is rebuilt deterministically inside the pinned image
(`PYTHONHASHSEED=0`); the reviewer's independent image build reproduces the
container seed byte-for-byte (md5 `e3b7b4f99717af8145217556ecf8fd44`, sha256
`ca96743e…`), identical to the contributor's dev container. All 20 per-task
reset snapshots were byte-identical. Note: a seed built **outside** the
pinned image (different SQLite build) is not byte-portable; the contract
freezes the logical digests and the in-image byte md5.
