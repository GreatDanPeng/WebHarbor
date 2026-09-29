# virginia_dmv — deterministic verifier contract (reviewer-authored)

Written by the virginia_dmv reviewer (review track, 2026-09-29) on
`orch/review/virginia_dmv` @ the review commit, on top of the contribution
`orch/contribute/virginia_dmv` @ `5a65d2a9`. Every ground truth below was
frozen from the reviewer's independent Playwright honest walks on the
independently built review container (`wh-vadm-review`, image
`webharbor:vadm-review`), against the independently reproduced seed
(md5 `e20897642a951494ced5ad6393a78ad7`).

## Layout

- `verify_lib.py` — package identity gate (task_id / `agent_done` / non-empty
  answer / same-origin same-port URLs / decodable PNGs), frozen seed identity
  gate (16 table counts + schema sha256 `b13f284f…` + rows sha256
  `767062c3…`), navigation gates (anti knowledge-shortcut), answer
  token/phrase/number/money/label-anchored checks, and read-only /
  exact-increment DB after-state checks.
- `verify_0.py` … `verify_19.py` — one verifier per task; ground truth is
  HARDCODED, never read from `tasks.jsonl`.
- `test_verifiers.py` — 109 adversarial contract tests (pytest).
- `append_rubrics.py` — the one-off script that appended `verifier_path` +
  `judge_rubric` to `tasks.jsonl` (5-key prefix byte-identical, no answer
  key).

## Stateful tasks and their pinned DB deltas

| Task | Allowed delta |
|---|---|
| T0 carol.d license renewal | `transactions` +1 `LIC…` row ($42.00, "with REAL ID"); `user_licenses` D5540917 expires→2033-08-02, status Valid, real_id→1 |
| T1 alice.j 2-year registration renewal | `transactions` +1 `REG…` row ($56.50, 2-year); `vehicles` id 1 expires→2028-10-15, years→2 |
| T3 Go Hokies plate purchase | `transactions` +1 `PLT…` row ($35.00); `vehicles` id 2 plate_design→virginia-tech-go-hokies |
| T6 bob.c appointment reserve+cancel | `appointments` +1 `VADM…` row (Richmond Central, 2026-10-08, morning slot, status Canceled) |
| T12 bob.c address change | `users` id 2 address→4020 University Drive, Fairfax, VA 22030; `transactions` +1 `ADR…` row ($0.00) |
| T13 alice.j certified record | `record_requests` +1 `REC…` row (driver, certified, online, $13.00); `transactions` +1 `REC…` row |
| T14 carol.d license replacement | `transactions` +1 `REP…` row ($20.00, Lost or stolen) |

All other tasks are read-only: every table must be row-identical to the
frozen seed after the run.

## Known environment quirks the contract encodes

- Two section-2 exam questions carry upstream-faithful broken
  `correctAnswer` values (7 and 5 against four rendered options), so an
  honest perfect-knowledge exam scores 8/10 (80%, passed). The T8 verifier
  checks internal consistency (N/10, percentage = 10·N, passed ⇔ ≥80%)
  instead of a fixed score.
- The 173rd Airborne plate allows 6 characters; the 8-character message
  AIRBORNE is truncated by the browser to AIRBOR. The T4 verifier accepts
  the rendered outcome.
- No Spanish translator-certification form exists in the catalog (nor on
  the live upstream); T11 pins the real object (English CSMA 8).
- The buy-sell page states no number of days for the DMV sale notification;
  T16 never requires one.
- The DMV 201 edition date lives only inside the downloaded PDF
  (`as_attachment`), so T10 requires the form number but never the edition
  date.

## Running

```bash
# one task (against a run directory holding trajectory.json + screenshots/
# + initial.db + after.db):
python3 verify_0.py --run_dir <dir>

# adversarial battery:
python3 -m pytest test_verifiers.py -q     # 109 passed
```

The verifier defaults to the review container `wh-vadm-review`; override
with `WH_CONTAINER` / `--container` and `WH_MIRROR_PORT`.

## r3 sync (fix branch, 2026-09-29)

The fix branch adopted this contract (commit `86579549`) verbatim as the
base of its `verify/` copy, then re-anchored the six depth-failing tasks
(T5/T11/T14/T15/T16/T18) to deepened task texts (honest atomic depth >= 15
via real composite actions — finder-filter derivations, wizard bookings,
renewal preview, certified vehicle-record order, receipt reopens, news
pager navigation). r3 truth movements vs the r2 contract:

- T5: + Franconia office page (fax + one service Alexandria lacks);
  + DMV-Select count for an Alexandria search (1, AAA Alexandria) with its
  name/address; Fairfax-within-DMV-Select count kept (2), CSC total kept
  (76), DMV Select total kept (58).
- T11: CRD 01 number/title, catalog total (419), Spanish count (17), CSMA 8
  number, PPI three ways / 15-day wait / $12.00 fee kept; + Driver Record /
  Vehicle Record wizard booking at Alexandria on 2026-10-06 8:00 AM under
  Sam Taylor (appointments row, status Confirmed).
- T14: replacement chain kept (credential/class, status, reasons, $20,
  REP receipt, card arrival, receipt copy, renew-or-replace rule, online
  blockers, DL 1P); + standard-term renewal preview total ($32.00) before
  the order.
- T15: new-resident steps/deadlines, safety inspection, emissions
  localities, insurance rule, decal note, CDL rule, voter note, exam
  exemption kept; + Richmond search count (6) and its customer-service-
  center count (5); + Vehicle Registration / Title wizard booking at
  Richmond Central on 2026-10-05 8:00 AM under Alex Morgan.
- T16: now stateful under alice.j — certified copy of the Camry's vehicle
  record online (title T8842-1195, VIN 1HGCF1A23XA448119, $13.00, REC
  receipt + copy lines); seller steps / plate rule + FMS-210 / SUT-3 /
  notify phone / buyer VSA 17A / PPI report contents / four fee cross-
  checks (registration transfer $2.00, replacement registration card
  $2.00, vehicle record online $8.00, original title $15.00) kept.
- T18: REAL ID fee/looks/steps/boarding rule, DMV 141/299 form numbers,
  fee-chart minimum $20, Apple Wallet release date, newest title kept;
  + oldest news item's title and release date on the pager's last page
  (2024 Local Heroes Series Features Statewide First Responders,
  2024-07-29); + REAL ID wizard booking at Arlington on 2026-10-06 8:00 AM
  under Jordan Lee. Dropped (no longer asked by the deepened texts): T18
  new-state rule, secure-facilities rule, Apple Wallet feature wording,
  news pager page count, id-apple-wallet how-to-add page.

`test_verifiers.py` runs 121 adversarial tests against the position-60
audit fixtures (`wh-virginia-dmv-audit-evidence/runs`: the auditor's own
independent honest walks for all twenty tasks on the audit container,
re-run clean on the final rebuilt image) — 20 honest PASS, 101 negatives
all FAIL. The stateful set grew to
`{0,1,3,6,11,12,13,14,15,16,18}` (new bookings + record order), so the
stale-DB and wrong-state batteries grew accordingly.

## r2 sync (re-review, 2026-09-29)

Re-anchored to the deepened task texts of the fix commit `243ceb9a`
(`orch/contribute/virginia_dmv`), per the r2 truth-movement audit:

- `tasks.jsonl` byte-copied from the fix branch: 20 rows, 7-key contract
  (5-key prefix = deepened texts; T3/T6/T8 prefix byte-identical to the
  frozen rows), no answer keys. `judge_rubric` per task matches the new
  texts (pure rules, no truth leakage).
- 17 verifiers (`verify_{0,1,2,4,5,7,9..19}.py`) re-anchored with new
  navigation gates and frozen ground truths; `verify_3/6/8.py` kept
  BYTE-IDENTICAL to the frozen contract; `verify_lib.py` seed identity
  digests unchanged (schema `b13f284f…`, rows `767062c3…`, file md5
  `e2089764…`) and the defaults still point at the review container
  (`wh-vadm-review`, port 46112).
- r2 adversarial correction applied: the fix branch's contract copy was
  over-asking (facts no task text requests: T0 real_id_minimum, T11
  ppi_report_includes, T14 renewal_preview/renewing_note, T15
  plate_designs/within_va strict phrasing, T18 mobile_id_cost, T19
  eligibility) and over-gating (surfaces not required for the asked
  facts: T5/T7 office-detail pages, T9 know-exam/manual-landing, T11
  filter pills, T14 renewing/renew-check, T15
  eligibility/title/registration/emissions/plates pages, T16
  dmv-select/title/registration pages, T17 reinstate/fees/roanoke
  detail, T18 mobile-id/newest/last-page, T19 eligibility). All removed:
  the reviewer's own honest task-text-only walks (two identical rounds)
  must pass 20/20 — verified — while 95 adversarial negatives all fail
  (`test_verifiers.py`: no-op, pure-answer shortcut, wrong answers,
  stale DB, read-only violations, tampered packages, task confusions,
  wrong state rows).
- `test_verifiers.py` fixtures switched to the reviewer's honest
  fixtures (`wh-virginia-dmv-rereview-evidence/my_fixtures`, ports
  46112/48112).
- `scripts_dev/validate_tasks.py` (7-key shape + leakage + premise +
  depth replay) switched to the reviewer's honest fixtures; it now
  reports the honest measured depths (min 7 / max 21 / total 304,
  six tasks below the >=15 bar: T5 13, T11 11, T14 14, T15 9, T16 7,
  T18 10) — AUDIT FAILED until those task texts are deepened further.

r3 re-review sync (reviewer track): the re-anchored verify_5/11/14/15/16/18
were accepted only after the r3 reviewer's independently built fixtures
(own container, own walks, own answers from page originals) passed them
20/20; verify_lib.py and every non-reanchored verifier stay byte-identical
to the r2 contract (seed digests re-verified unchanged: SCHEMA b13f284f...,
ROWS 767062c3..., FILE md5 e20897642a951494ced5ad6393a78ad7).
