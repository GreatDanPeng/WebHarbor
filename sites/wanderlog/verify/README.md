# wanderlog verifier suite (reviewer contract, depth-fix sync)

Deterministic, LLM-free verifiers for the 21 `Wanderlog--*` benchmark tasks.
Written by the wanderlog reviewer on `orch/review/wanderlog`
(frozen at `885defcf`, re-synced at r2 for the depth fix,
r3-synced for the T2 deepening): the 17 shallow
tasks were deepened to the audit
caliber (atomic UI actions, reads excluded, ≥15), so every changed question
point got matching navigation gates, answer anchors and DB contracts. The 4
already-passing tasks (T4/T8/T10/T18) keep their original task text and their
frozen verifiers byte-identical. Ground truth is **hardcoded** in
`verify_<n>.py` — re-frozen at r2 from the reviewer's two independent
Playwright rounds on the r2 review container `wh-wanderlog-r2` (seed md5
`b32e9905a17605ce9c983780764c9ee4`, image `webharbor:wanderlog-r2`, built
independently from the fixed tree; seed byte-identical to the frozen r1
review contract and the contributor's dev container). Both rounds produced
identical per-task measurements; every reported fact was additionally
cross-checked against the frozen seed database (394 facts, zero mismatch).
The r2 sync corrected two transcription errors present in the fix branch's
proposed copy (verify_12 first_coords -> 48.8639, 2.2934; verify_16
pantheon_coords -> 41.8986, 12.4769) and four judge-rubric drifts against
the task texts (T11/T12/T13/T16).

**r3 sync** (fix commit `6dcf9cf9` on `orch/contribute/wanderlog`): T2
gains a cross-page question point (the free-attractions list's top two
places and both of their descriptions), so `verify_2.py` adds the
`/place/details/1534` navigation gate (`nav_sacre`) and the
`free_second`/`sacre_desc` anchors; the honest walk must now return from
the Père-Lachaise page to the free-attractions list and open the
second-ranked place, taking T2 from 14 to **16** atomic steps (verified by
the reviewer's two independent r3 rounds on the r3 review container
`wh-wanderlog-r3rv`, image `webharbor:wanderlog-r3`, built independently
from the fix tree; 21/21 ≥ 15, min 15 / max 19 / total 338, per-task
counts identical across rounds). The T2 anchors were asserted live during
those walks and match the frozen seed rows exactly. The fix branch adopted
the r2 truth corrections (verify_12/verify_16 coordinates) and the
T11/T12/T13/T16 rubric corrections verbatim from `1adce592`, so those
verifiers and rubrics stay byte-identical here. Honest fixtures re-frozen
from the reviewer's r3 round 2 in
`/data/zhaoyang-user-projects/websyn/wh-wanderlog-rereview-evidence/r3/runs_round2`.

## Layout

- `verify_lib.py` — shared contract: package identity (task_id / agent_done /
  non-empty answer / same-origin same-port / decodable PNGs), seed identity
  gate (table counts + schema sha256 + rows sha256 + file md5 pinning the
  in-image seed), navigation gates, answer token/phrase/number/money/ordered
  checks, and read-only / exact-delta DB after-state checks.
- `verify_0.py` … `verify_20.py` — one verifier per task; navigation gates +
  hardcoded ground truth + DB contract.
- `test_verifiers.py` — 113 pytest cases: 21 honest fixtures PASS; no-op,
  answer-only shortcut, wrong-answer, stale-DB, read-only-violation,
  tampered-package and task-confusion negatives all FAIL (zero false
  positives). With the site's own suite: 155 passed.

## Usage

```bash
python3 sites/wanderlog/verify/verify_2.py --run_dir <trajectory_dir>
#   [--initial_db P] [--after_db P] [--container wh-wanderlog-r3rv]
# prints {"task_id": ..., "pass": true/false, "reason": ..., "evidence": [...]}
```

`<trajectory_dir>` holds `trajectory.json` + `screenshots/step_NNN.png` +
`initial.db` + `after.db` (the agent_demo run shape). If the DB files are
absent they are `docker cp`-ed from the running r3 review container
(`wh-wanderlog-r3rv`, mirror port 46113). The honest fixtures live in
`/data/zhaoyang-user-projects/websyn/wh-wanderlog-rereview-evidence/r3/runs_round2`.

## Task / contract map

| # | domain | state | required surfaces | DB contract |
|---|---|---|---|---|
| 0 | guides sort + guide + profile + Iceland search + recent sort | read-only | /guides?sort=places, /view/nlcviusycz, /u/pham2ez, /guides?q=Iceland, /view/znordifcrv, /u/achillesvig, /guides?sort=recent, /view/vayytsqzpq | row-identical |
| 1 | Tokyo rankings cross (attractions 6-7, cafes top-2, restaurants 7) | read-only | /explore/1, /list/104388, /place/956, /place/36514, /list/14, /place/27207, /place/376399, /list/1, /place/379633 | row-identical |
| 2 | Louvre chain + free-attractions top-2 + restaurants 6-7 | read-only | /search, /place/1529, /list/104643, /place/1532, /list/129829, /place/24882, /place/1534, /list/74215, /place/115485, /place/369538 | row-identical |
| 3 | trip overview + Septime/Sacré-Cœur places + budget/checklist/settings/shared view | read-only | /login, /plan/parisinspring, /place/114863, /list/74215, /place/1534, …/budget, …/checklist, …/settings, /trip/parisinspringv, /u/bob.c | row-identical |
| 4 | add Shinjuku Gyoen to Tokyo Weekend (kept) | +1 entry | /login, /plan/tokyowkend, /plan/tokyowkend/add | trip_entries +1 (Day 1, 09:00, 90, note), trips touched |
| 5 | reorder + remove + add Arc de Triomphe on Day 1 | -1 entry, ~1, +1 | /login, /plan/parisinspring, /plan/parisinspring/add | Sainte-Chapelle removed, Eiffel renumbered, Arc added (11:00, 60, note), trips touched |
| 6 | checklist two adds + two toggles | +2 items, ~1 | /login, /plan/icelandring, …/checklist | checklist_items +2 (todo checked, packing unchecked), Car insurance toggled |
| 7 | budget two Transport expenses + settlement | +2 expenses | /login, /plan/icelandring, …/budget | expenses +2 (Fuel $87.30 Dana, Airport parking $12.50 Bob, both 2026-11-07 both-split), trips touched |
| 8 | invite + accept cross-account (kept) | +1 collab | /login, /plan/parisinspring, /plans | trip_collaborators +1 (carol, accepted) |
| 9 | privacy flip + extend trip + share link | ~1 trip, +1 section | /login, /plan/nycfoodcrawl/settings, /trip/nycfoodcrawlv, /place/115803, /list/74988 | trips private→link + end 2026-12-07, trip_sections +1 (Day 4 · Dec 7) |
| 10 | new Kyoto trip + section (kept) | +1 trip, +3 sections | /login, /plan/new?…geo_id=2 | trips +1 (deterministic keys), trip_sections +3 |
| 11 | trip map + budget + Orsay/Clamato + shared view | read-only | /login, /plan/parisinspring/map, …/budget, /place/1522, /place/24178, /list/74215, /trip/parisinspringv, /u/bob.c | row-identical |
| 12 | hotel search + Paris 1/3/5 + Rome top-2 hotels | read-only | /hotels, /hotels/9614, /place/24349, /place/531760, /place/757903, /hotels/9616, /place/390732, /place/392578 | row-identical |
| 13 | lilies profile + guide + commenters + rachel search chain | read-only | /search?q=lilies, /u/alilies, /view/uzyvvtuwtc, /u/alice.j, /u/carol.d, /search?q=rachel, /u/rachelirl_, /u/peachy2391, /view/nwhizniizm, /u/dana.k | row-identical |
| 14 | leaderboard + LizzyS guide + Empire State + maru chain | read-only | /leaderboard, /search?q=LizzyS, /u/LizzyS, /view/tbgojyfsfr, /place/2352, /list/105416, /search?q=maru, /u/Marutravelsjapan, /view/vayytsqzpq, /view/okgarduipy | row-identical |
| 15 | like + comment on Rome guide + author/commenter profiles | +1 like, +1 comment, ~1 guide | /login, /guides, /view/zlcocpeivp, /u/delicious_dogfish, /u/dana.k | likes/comments +1, like_count 226→227 |
| 16 | Rome restaurants + attractions + hotels deep chain | read-only | /explore/9616, /list/74217, /place/370765, /place/370316, /list/104645, /place/1583, /list/137027, /place/390732 | row-identical |
| 17 | Dana Kim search + Rome trip + Pantheon/Trevi + member chain | read-only | /search?q=Dana+Kim, /u/dana.k, /trip/romeessentv, /place/1583, /list/104645, /place/1589, /u/alice.j, /trip/tokyowkendv, /place/965 | row-identical |
| 18 | collaborator adds Breizh Café (kept) | +1 entry | /login, /plan/parisinspring, …/add | trip_entries +1 (Day 3, 09:00, 60, note, bob) |
| 19 | London guides + Tate Modern + both authors | read-only | /guides?q=London, /view/dxpkirpjls, /place/28109, /list/104642, /u/taraabraham, /view/wnglqezund, /u/LizzyS | row-identical |
| 20 | Tokyo explore deep + attractions/cafes/hotels/restaurants cross | read-only | /explore/1, /list/104388, /place/31866, /list/14, /place/119197, /list/136770, /place/79682, /list/1 | row-identical |

## Honest-walk measurement (audit caliber)

Real-Chromium honest walks, fresh reset + fresh context per task, js_errors 0,
two independent rounds with identical per-task counts. Caliber: **atomic UI
actions only (click/fill/select/submit/check/back), reads excluded, +1 for
composing the answer; the initial home load is never counted.**

| T | atomic | ≥15 | T | atomic | ≥15 |
|---|---|---|---|---|---|
| 0 | 15 | ✓ | 11 | 17 | ✓ |
| 1 | 16 | ✓ | 12 | 15 | ✓ |
| 2 | 16 | ✓ | 13 | 17 | ✓ |
| 3 | 18 | ✓ | 14 | 17 | ✓ |
| 4 | 16 | ✓ | 15 | 15 | ✓ |
| 5 | 18 | ✓ | 16 | 15 | ✓ |
| 6 | 15 | ✓ | 17 | 17 | ✓ |
| 7 | 19 | ✓ | 18 | 16 | ✓ |
| 8 | 15 | ✓ | 19 | 15 | ✓ |
| 9 | 15 | ✓ | 20 | 15 | ✓ |
| 10 | 16 | ✓ | | |

Total atomic = 338 (min 15, max 19); **21/21 meet the ≥15 bar** in both
independent r3 rounds (the reviewer's walks on `wh-wanderlog-r3rv`). The
measured in-repo audit
(`scripts_dev/validate_tasks.py`, same caliber driven through the Flask test
client with CSRF on) reproduces min 15 / max 19 / total 338 with T2 = 16
(the mandatory return to the free-attractions list and the
second-place open are part of the driven path).

## Seed reproducibility note

The seed is rebuilt deterministically inside the pinned image
(`PYTHONHASHSEED=0`); the r3 review image build reproduces the container seed
byte-for-byte (md5 `b32e9905a17605ce9c983780764c9ee4`, identical to the
frozen review contract, the contributor's dev container and the staged
`wanderlog.tar.gz` asset flow). All 21 per-task reset snapshots were
byte-identical; the r3 re-freeze re-verified the counts / schema sha256 /
rows sha256 / file md5 against the independently built r3 image seed and
re-proved reset byte-identity (UI dirty write -> control-plane reset ->
cmp BYTE-IDENTICAL). A seed built **outside** the pinned image is not
byte-portable; the contract freezes the logical digests and the in-image
byte md5.
