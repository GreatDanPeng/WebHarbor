# verizon verifier suite (reviewer contract)

Deterministic, LLM-free verifiers for the 20 `Verizon--*` benchmark tasks.
Written by the verizon reviewer on `orch/review/verizon`; r2 contract
sync re-anchors the gates and ground truth to the depth-fix contribution
`99e1cb63`. Ground truth is **hardcoded** in `verify_<n>.py` — frozen from
the reviewer's two independent strict-caliber Playwright rounds on the
review container `wh-verizon-r2review` (seed md5
`f2d20153c24b6945fb5203b81d7f1fb6`, image `webharbor:verizon-r2review`,
an independent single-site build from contribution `99e1cb63` that re-runs
the exact real-Dockerfile verizon block: asset-inventory gate 281/281 +
`PYTHONHASHSEED=0` in-image seed build; in-image seed sha256
`eab88cb786ec880f8582a3e42e48295bb3ba4d2d886d4d71e1e71d4afb00b53c` —
byte-identical to the contributor's declared rebuild, with the schema
digest unchanged and the rows digest moved by the A17 5G upstream
storage/ship-window completion; `/reset/verizon` restores instance ==
instance_seed byte-identically after dirty-row injection). Both rounds
produced identical per-task measurements (20/20 error-free walks, counts
identical across rounds); every reported fact was asserted against the
frozen seed during the walks.

r2 sync caliber notes (virginia_dmv r2 precedent): navigation gates cover
ONLY the surfaces the task text requires — brand filters/sorts the text
does not ask for, bill-detail pages whose asked values are readable on
the already-required bills list, and store-detail pages whose asked
values are readable on the city page are NOT gated. Answer anchors are
page-verbatim with tolerance for equally-honest renderings (e.g. a
device-page rating may be quoted as `4.2 out of 5 rating (93 reviews)`
or `4.2 (93 reviews)`).

## Layout

- `verify_lib.py` — shared contract: package identity (task_id / agent_done /
  non-empty answer / same-origin same-port / decodable PNGs), seed identity
  gate (table counts + schema sha256 + rows sha256 pinning the independent
  in-image seed), navigation gates, answer token/phrase/number/money/ordered
  checks, confirmation cross-checks against DB rows, and read-only /
  exact-delta DB after-state checks.
- `verify_0.py` … `verify_19.py` — one verifier per task; navigation gates +
  hardcoded ground truth + DB contract.
- `test_verifiers.py` — 106 pytest cases: 20 honest fixtures PASS; no-op,
  answer-only shortcut (the fixture's own correct answer with zero
  navigation), wrong-answer, stale-DB, read-only-violation,
  tampered-package and mutated-state negatives all FAIL (zero false
  positives).

## Depth finding (2026-09-23 standard)

The same walks measured the honest atomic step count (navigation / fill /
select / submit after home load; perception reads NOT counted; +1 compose):
**min 2 / max 15 / total 140 — 19 of 20 tasks sit below the 15-step bar**
(only Verizon--5, the full purchase flow, reaches exactly 15). The
contribution receipt's "new atomic caliber (reads not counted), 20/20 >= 15"
claim is measured on the dual caliber `A = atomic + reads` (its own
`walk_results.json`: min 15 / max 19 / total 325, reproducible), not on the
reads-don't-count caliber. This is the same class as the zara / wanderlog /
tourradar depth blockers — see the review report.

## Premise notes pinned by the verifiers

- `Verizon--3`: the mirror's Samsung Galaxy A17 5G PDP lists **no storage
  options and no ship window** (upstream shows "Storage: 128 GB" and "Free
  shipping by Thursday" today), so the verifier pins the current on-page
  state ("not listed" / "none" answers accepted) and flags the task text's
  storage/ship-window asks as premise defects to fix.
- `Verizon--18`: both phones' base storage is 256 GB — the "which offers
  more base storage" ask is a tie; the verifier pins the tie answer.
- `Verizon--16`: the troubleshoot wizard POSTs its form (no query string),
  so the per-flow navigation gate keys on the wizard result text observed
  in the trajectory steps.

## Usage

```bash
python3 verify_<n>.py --run_dir <agent run dir> [--initial_db P] [--after_db P]
# exit 0 = PASS, 1 = FAIL; JSON verdict on stdout
pytest -q test_verifiers.py      # 106 adversarial contract cases
```

The seed-identity gate pins the frozen seed; if the contributor changes
seed content during a fix round, the pinned digests must be re-frozen from
a new independent build.

## r3 fix sync (orch/contribute/verizon, on top of the 77d56c1b contract)

The r2 re-review found the depth blocker unfixed (9/20 tasks under 15
honest atomic steps once task-text-unrequired padding is excluded) and
graded the fix branch's in-branch verify copy 0/20 against honest
strict-caliber fixtures (12 over-gated tasks, non-verbatim rating keys,
mis-anchored answer keys). The r3 fix adopts the reviewer's contract sync
`77d56c1b` wholesale — `verify_lib.py`, the eleven unchanged verifiers and
`README.md` are byte-identical to it — and re-anchors only the nine tasks
whose text was deepened. The stale `Verizon--3` premise note above predates
the r1 A17 fix; the current verifier (unchanged from 77d56c1b) correctly
requires the on-page "Storage options: 128 GB" and
"Free shipping by Thursday with new line".

Deepening (task text is the only spec; every added action is text-required):
- `Verizon--0` 17 atomic: + trade-in estimator leg for the family's Apple
  iPhone 17e in Mint condition.
- `Verizon--2` 17 atomic: + second estimate (Pixel 10a Good, after Cracked)
  and the return-policy leg (restocking fee + return window).
- `Verizon--7` 16 atomic: + Northgate appointment-topic page, Tacoma
  company-store detail page, Redmond store detail page, Everett city page.
- `Verizon--9` 16 atomic: + August/July bill detail pages, post-payment
  bills-list re-check, September detail payment echo, usage page, Auto Pay
  page.
- `Verizon--10` 18 atomic: + trade-in estimator leg for Grandma Lin's
  Motorola moto g - 2026 in Good condition.
- `Verizon--11` 17 atomic: + August bill detail page and a trade-in
  estimator leg for the Tablet line's Google Pixel 10a in Mint condition.
- `Verizon--12` 17 atomic: + Pixel 11 Pro PDP (battery/screen/rating) and
  iPhone 18 Pro PDP (24-month price, ship window).
- `Verizon--18` 19 atomic: + trade-in estimator leg for the iPhone 18 Pro
  Max in Good condition; the cart now renders each item's monthly line
  (r2 low-severity rendering fix), so the per-item anchors are page-verbatim.
- `Verizon--19` 22 atomic: + full checkout (Rosa Diaz order) and the razr+
  Cracked estimate; now stateful (orders row delta).

Truth moves (77d56c1b -> r3, for the r3 re-review diff):
- T0: added `nav_trade_in`, `nav_estimate`, `est_17e_mint` ($300.00).
- T2: added `est_10a_good` ($160.00), `nav_support`, `nav_return_policy`,
  `restocking_fee`/`restocking_amount` ($50.00), `return_window` (30 days).
  Deleted `simplicity_discounts` (task text no longer asks which discounts
  the single-line price is after).
- T7: added `nav_northgate_appt`, `nav_tacoma_detail`, `nav_redmond_detail`
  (either Redmond store), `nav_everett`, `appt_topics`,
  `tacoma_company_addr` (4009 Tacoma Mall Blvd), `tacoma_company_sunday`,
  `redmond_services`, `everett_count` (2), `everett_company`,
  `no_company_store` (Redmond). Deleted `seattle_non_company`,
  `company_monday`, `card_services`, `tacoma_appts` (the task text no
  longer asks for the Seattle non-company count, Monday hours, card
  services or the Tacoma appointment flag).
- T9: added `nav_aug_bill`, `nav_jul_bill`, `nav_sep_bill_echo`,
  `nav_usage`, `nav_autopay`, `aug_jul_protection`, `jul_protection`,
  `payment_echo`, `more_data` (Alice), `autopay_discount` ($10.00).
  Deleted `account_number`/`account_kind`/`line_count`/`bills_count` (the
  deepened text no longer asks for the overview identifiers or the bills
  count).
- T10: added `nav_trade_in`, `nav_estimate`, `est_motog_good` ($70.00).
  Deleted `bills_count`.
- T11: added `nav_aug_bill`, `nav_trade_in`, `nav_estimate`,
  `aug_protection`, `est_10a_mint` ($210.00). Deleted `line_count`.
- T12: added `nav_p11p_pdp`, `nav_18p_pdp`, `p11p_battery`
  ("Up to 34 hours"), `p11p_screen` (Super Actua), `p11p_rating`
  (3.8 / 71 reviews), `p18_24mo` ($49.99), `p18_ship` (Tue, Sep 29 - Fri,
  Oct 9). Deleted `plan_hotspot_allowance` (the plan-page selector leg now
  carries the 2-line total only).
- T18: added `nav_trade_in`, `nav_estimate`, `est_18pm_good` ($730.00);
  `storage_tie` relaxed to `storage_verdict` (tie/neither/equal/same) since
  the text now asks "whether either offers more base storage".
- T19: added `nav_checkout`, `nav_order_conf`, `est_razr_cracked` ($100.00),
  `order_confirmation` (DB-matched VZW token), `delivery_window`
  ("Ships between Wed, Sep 30 - Fri, Oct 9"); read-only -> stateful with the
  exact `orders` row delta (Rosa Diaz, $70.41/mo). Deleted `nav_plans`,
  `simplicity_1line`, `simplicity_discounts` (the task text no longer asks
  for the Simplicity single-line price).

`test_verifiers.py`: 146 cases — every fixture is the r3 re-reviewer's
own honest walk (two independently executed rounds with identical
counts, on an independent container in the 46099 port block); the
adversarial negatives cover no-op x20, answer-only shortcut x20,
wrong answers x20, stale/dirty DB x7, read-only violations x12,
tampered packages x40 (wrong task_id / off-site / cross-port /
unterminated / empty answer / corrupt screenshot / deleted
navigation / cross-fixture) and state under-reach x7 (including the
T19 checkout's missing / wrong-address order row). The stateful set is
{5, 8, 9, 10, 11, 13, 14, 19}.

Known low-severity limitations (pre-existing in the frozen 77d56c1b
contract, byte-identical here, NOT introduced by the r3 fix):

1. `verify_lib.check_screenshots` validates only the 8-byte PNG magic,
   not a full decode, so a truncated screenshot that preserves the
   magic passes that auxiliary gate.
2. `verify_lib.check_answer_money`'s comma-grouped fallback pattern
   (`pat3`) uses a `(?![\d,])` lookahead that omits the decimal point,
   so a cents-only off value (e.g. "$160.63" against the $160.62
   truth) passes the money gate; dollar-part deviations are caught.
   Honest agents quoting the rendered page are unaffected.

The substantive grading (answers, navigation, DB after-state) is
unaffected by either; hardening the shared lib is deferred to the
unified integration pass so the fix branch's byte-identical adoption
of the frozen contract stays aligned.

## Audit-rail hardening (2026-09-30 audit, position 61)

The 2026-09-30 audit hardened the three low-severity items above in place
(shared-lib + verifier changes, audit rail `orch/audit/verizon`):

1. `_png_ok` now validates a complete, decodable PNG: 8-byte magic, an
   IHDR chunk up front with nonzero dimensions, and the IEND trailer at the
   very end. Truncated screenshots (magic preserved, payload dropped) and
   magic-only stubs FAIL the screenshot gate; real Playwright screenshots
   pass. Pinned by `test_truncated_screenshot_fails` and
   `test_magic_only_png_stub_fails`.
2. `check_answer_money` closes the cent-drift hole while keeping every
   honest form: numerically equal spellings pass ("31.4" == 31.40,
   "$300.00." with a sentence period, "Good $330.00," with a list comma),
   significant drift fails ("$160.63" / "$160.00" / "$160.6" for
   $160.62; "$1,199.98" for $1,199.99), and boundary guards reject
   partial-token matches ("$1,300" / "$1300" / "300,000" for $300).
   Pinned by `test_money_gate_forms`, `test_t9_cent_drift_answer_fails`,
   `test_t10_cent_drift_answer_fails`.
3. `verify_9`'s `jul_protection` anchor now requires the protection charge
   to be tied to July (was: any "Jul(y)" mention).

Two further audit corrections: the `nav_plans` gates in verify_0/2/12/14
accepted only `/plans/`, but the site links the Simplicity Plan page solely
as `/plans/unlimited/` (the `/plans/` alias of the same route is never
linked), so every honest click-only run failed the gate — the gate now
accepts either form of the same page (`check_visited_any`; answer and DB
anchors unchanged), and verify_14's row template is a raw string (was a
SyntaxWarning under Python 3.12).

Site-side audit fixes (same commit): all 885 store-detail pages emitted
breadcrumb links under state-abbreviation slugs (`/stores/wa/...`) that
404 — the breadcrumb now emits the canonical full-state-name slugs
(97 unique dead targets -> 0 across the full 2800+-page link graph);
narrow-viewport overflow on seven template surfaces (plan compare table,
account overview, usage, cart, bills, store lists/cards) fixed via a
<=760px block (tables scroll internally, grid children min-width:0,
two-column lists, stacked store cards, wrapping action buttons) — 0
overflow at 1440/390/320 on every template; the city store card's
scrape-note label "Hours today-style (Mon)" is now "Hours (Mon)".

Remaining pre-existing, non-blocking, documented (written response):
support content bodies carry upstream page-chrome scrape residue ahead of
the substantive text (seed-bound content; a cleanup requires a content
reseed and a seed re-anchor across both rails — all task-anchored content
is present and readable at the same URLs), and support page slugs use
underscores (verifier-anchored URLs, resolve fine).
