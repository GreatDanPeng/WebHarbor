# usps verifier suite (reviewer contract)

Deterministic, LLM-free verifiers for the 21 `USPS.com--*` benchmark tasks.
Written by the usps reviewer on `orch/review/usps`; ground truth is
**hardcoded** in `verify_<n>.py` — frozen from the reviewer's independent
Playwright walkthroughs of the review instance (seed md5
`af00d6d452e0fdddcf2197357ad9f3b2`), with every price anchor independently
verified against the live `pe.usps.com` Notice 123 / IML pages (22/22 exact),
the Postmaster Finder roster verified against the live `webpmt.usps.gov`
API, and news/store anchors verified against the live `about.usps.com` /
`store.usps.com`.

## Layout

- `verify_lib.py` — shared contract: package identity (task_id / agent_done /
  non-empty answer / same-origin same-port / decodable PNGs), seed identity
  gate (23-table counts + schema sha256 + rows sha256 pinning the
  independent in-image seed), navigation gates, STRICT two-decimal money
  checks plus attribution-aware money checks (anti price-swap),
  marker-scoped section checks (anti cross-item swap), and read-only /
  exact-delta DB after-state checks.
- `verify_0.py` … `verify_20.py` — one verifier per task; navigation gates +
  hardcoded ground truth + DB contract.
- `test_verifiers.py` — 109 pytest cases: 21 honest fixtures PASS; no-op,
  answer-only shortcut, wrong-answer, stale-DB, read-only-violation,
  tampered-package and task-specific-confusion negatives all FAIL
  (zero false positives).

## Ground-truth notes (per the reviewer's findings)

- **F-1 (blocking)**: the shipped site enables CSRFProtect but renders no
  `csrf_token` input in any of its 19 POST forms, so every form submission
  fails with "Bad Request — The CSRF token is missing" in a real browser.
  The honest live fixtures were therefore exercised through a CSRF-disabled
  review instance of the same tree/seed. After the contribution embeds the
  tokens (platform norm: allrecipes/github/bbc_news/wolfram_alpha), the
  same contract grades the shipped site unchanged.
- **F-2 (T5)**: the Click-N-Ship weight input `step="0.5"` rejects the
  task's 4.2 lb value in a real browser; the T5 fixture lifts only that
  constraint (sets step="0.1") and grades the task as written. Fixing the
  step attribute restores the unmodified browser walk.
- **F-7/F-8 (T5/T6)**: the shipped wizard blanks the step-1 address fields
  on later POSTs (rows carry empty sender/recipient fields) and never sets
  `signature_required`; the DB templates match the shipped behavior with
  wildcards so the contract stays valid before and after those fixes.
- **F-6 (T4)**: the seeded utility-bill mailpiece belongs to alice's feed;
  bob's feed has exactly one Bill/Statement piece today (Lakeshore
  Hardware). The T4 verifier grades the sender the environment actually
  shows and the report flags the premise defect for the contributor.
- Deterministic confirmation IDs (verified by recomputation):
  T7 `PKG-C0DAFAB`, T10 box `7792`, T13 `HLD-FD88495`, T17 `CLM-D7D8EDA`,
  T14 `COA-7837679` (Family/Regular choice; any honest forward-type choice
  still passes via the format + DB-row contract).

## Usage

```bash
python3 sites/usps/verify/verify_2.py --run_dir <trajectory_dir>
```

Each trajectory dir contains `trajectory.json` (task_id, start_url, steps
with url/url_after/screenshot refs, terminated/termination_reason,
final_answer), `screenshots/step_NNN.png`, `initial.db` (must be the frozen
seed) and `after.db`. Output: JSON verdict; exit 0 on PASS, 1 on FAIL.
