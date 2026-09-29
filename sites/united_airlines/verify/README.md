# Reviewer verifier contract for united_airlines (review track)

Deterministic per-task verifiers authored by the reviewer on
`orch/review/united_airlines`, per the hardened reviewer-suite contract
(`sites/us_appliance`, `sites/u_s_customs`). r1 (f1da62f4) authored the
contract against contribution `a5d947ff`; **r2 re-freezes it against the
fix-round contribution `93a2638f`** (seed md5
`3a04d306e9fcb436e598fa07e2740912`):

- `verify_lib.py` — shared gates: package identity (task_id / agent_done /
  non-empty answer / same-origin-same-port URLs / decodable PNGs), seed
  identity (schema sha256 `9f7ae6cf…` + rows sha256 `95d81cd7…` + counts,
  frozen from the reviewer's independent r2 image build, seed md5
  `3a04d306e9fcb436e598fa07e2740912`), anti-shortcut navigation gates,
  answer token checks, and SQLite after-state contracts (read-only or exact
  row deltas only).
- `verify_0.py … verify_20.py` — one verifier per task with the ground truth
  HARDCODED from the reviewer's honest live walkthroughs of the rereview
  container `wh-united-airlines-rereview` (never read from tasks.jsonl).
  r2 re-frozen answer points: T4's 787-8 total seat rows (32), T6's
  standard-Economy seat band (rows 15-32) and the $35 added-bag anchor,
  T8's before/after itinerary (original UA 2803 14:33), T12's 3-bag
  calculator run ($35/$45/$150 = $230), T14's both-page Silver thresholds
  (12 PQF / 4,000 PQP, they agree; 10 PQF / 3,360 PQP still needed), T16's
  fleet values (seat rows 37/46, cruise 560/557 mph, wingspan 197 ft 4 in,
  777-300ER thrust 115,300 lbf) and T17's four source-article titles.
- `tests/` — adversarial pytest matrix: honest 21/21 PASS, no-op 21/21 FAIL,
  shortcut/wrong-answer/stale-DB/read-only-violation/dirty-seed/package-tamper
  and task-specific negatives all FAIL (zero false positives); r2 adds seven
  new negatives attacking the re-frozen points (wrong original flight, wrong
  3-bag total, missing calculator run, wrong remaining PQF/PQP, false
  disagreement claim, stale pre-fix fleet values, missing article titles).
- `append_rubrics.py` — appends `verifier_path` + `judge_rubric` to
  tasks.jsonl asserting the original 5-key rows stay byte-identical to
  `93a2638f` and no answer key is added.

Run: `python3 -m pytest sites/united_airlines/verify/tests -q`
(103 passed; the seed resolves from the running rereview container or
`UNITED_AIRLINES_TEST_SEED_DB`).

Note on task 2: the award-redemption button was broken in the mirror UI at
r1 (hidden `method=card` input preceded the Redeem submit button — review
finding F-1). The fix at 93a2638f removes the hidden input and puts
`name="method"` on both submit buttons; the reviewer's r2 live walk of the
real Redeem click lands the award booking exactly as the contract freezes
it (42,595 miles redeemed, balance 25,855, total 0.0, single −42,595
activity, no award miles/PQP credited back to the traveler).

Audit-rail amendments (audit track, on top of the merge of contribution
93a2638f + contract 8f08d0d6):

- `verify_1.py` nav_return gate re-anchored to the real UI flow: the
  round-trip selection redirects to `/flights/select-return?origin=ORD&
  destination=CMX` (the return date lives in the session cart, never in
  the URL), so the old `depart=2026-10-21` URL requirement was
  unsatisfiable by any honest visible-element walk; the frozen fixture
  URL now matches the real browser flow.
- `verify_18.py` duration anchor re-anchored to the rendered value: the
  status page lists UA 1197's duration as 3h 01m (frozen great-circle
  block time), which the old anchor (2h 35m only — the naive schedule
  difference) never rendered; both the displayed reading and the honest
  arithmetic reading are now accepted, and the fixture answer quotes the
  displayed value.
- T6 frozen fixture seat updated from 15A (occupied on the live seat map
  and silently accepted by the old My-trips seat save) to 15D — a
  genuinely free standard aisle seat — matching the app-side fix that
  now enforces the seat map's occupancy exactly as the check-in flow
  does (`test_seat_selection_rejects_occupied_seat` guards it).
- All ground-truth values otherwise unchanged; pytest 103/103 green on
  the amended contract, 34/34 on the amended mirror suite.
