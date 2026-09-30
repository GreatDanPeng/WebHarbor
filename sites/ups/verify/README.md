# Reviewer grading contract for `ups`

One deterministic verifier per benchmark task (`verify_0.py` … `verify_19.py`),
plus the shared utilities in `verify_lib.py` and the adversarial test matrix in
`tests/test_verifiers.py` (94 cases: 20 honest-PASS fixtures + 74 attacks that
must all FAIL — zero false positives).

Deterministic-first contract, in evaluation order:

1. **Trajectory identity** (fail-closed): `task_id` matches, `terminated` with
   `agent_done`, non-empty final answer, every URL on the same loopback
   origin/port as `start_url`, every referenced screenshot a decodable PNG.
2. **Seed identity gate** (fail-closed): the initial DB snapshot must BE the
   frozen in-image seed — schema sha256 `72d2bbfc…`, rows sha256 `cecb4190…`,
   16-table counts, file md5 `44209820…`. A run graded against a pre-mutated
   database fails here.
3. **Navigation gates** (anti knowledge-shortcut): the on-site pages each task
   names MUST appear in the trajectory (track pages, wizards, locator, service/
   business/support/store pages). A correct answer with no matching navigation
   fails as a recall shortcut.
4. **Answer checks**: token / phrase / number / money / count matching against
   ground truth HARDCODED inside each verifier (never in `tasks.jsonl`).
5. **DB after-state**: read-only tasks require all 16 tables row-identical to
   the seed; stateful tasks (hold-for-pickup, guest shipment, pickups, claim)
   require the exact allowed row delta and nothing else (agent-chosen form
   fields like phone/email/contact name are wildcarded; task-specified facts
   are frozen).

Usage (same signature for every verifier):

```bash
python3 sites/ups/verify/verify_N.py --run_dir <trajectory-dir> \
    [--initial_db <seed.db>] [--after_db <live.db>] [--container wh-ups-review]
```

Emits `{"task_id", "pass", "reason", "evidence"}`; exit 0 on PASS, 1 on FAIL.

Frozen readings for the three double-readable task spots (documented in the
review report): the closest UPS Access Point to ZIP 10001 lists no phone
(report what the detail page shows); "second-to-last scan" is penultimate in
time; the Pack and Ship page itself makes no carrier-choice statement (carrier
acceptance is a Mailboxes-page perk). The cheapest weekly pickup for a
3-day-a-week shop is UPS Smart Pickup ($18.50 < Day-Specific 3-day $23.25).
