# zara verifier suite (reviewer contract)

Deterministic, LLM-free verifiers for the 22 `Zara--*` benchmark tasks.
Written by the zara reviewer on `orch/review/zara`; ground truth is
**hardcoded** in `verify_<n>.py` — frozen from the reviewer's two independent
Playwright rounds on the review container `wh-zara-review` (seed md5
`9aafa4129f038e48bf85fb7ed1fbaa1e`, image `webharbor:zara-review`,
independent single-site build from contribution `8afac519` reproducing the
full Dockerfile zara block; in-image seed sha256
`efc75fbc95d650b015bacf2a0a1f122cded669534aaf8c3304d3291dd366d966` —
byte-identical to the contributor's declared build; `/reset/zara` restores
instance == instance_seed). Both rounds produced identical per-task
measurements; every reported fact was asserted against the frozen seed
during the walks.

## Layout

- `verify_lib.py` — shared contract: package identity (task_id / agent_done /
  non-empty answer / same-origin same-port / decodable PNGs), seed identity
  gate (table counts + schema sha256 + rows sha256 pinning the independent
  in-image seed), navigation gates, answer token/phrase/number/money/ordered
  checks, and read-only / exact-delta DB after-state checks.
- `verify_0.py` … `verify_21.py` — one verifier per task; navigation gates +
  hardcoded ground truth + DB contract.
- `test_verifiers.py` — 108 pytest cases: 22 honest fixtures PASS; no-op,
  answer-only shortcut, wrong-answer, stale-DB, read-only-violation,
  tampered-package and mutated-state negatives all FAIL (zero false
  positives).

## Usage

```bash
python3 sites/zara/verify/verify_2.py --run_dir <trajectory_dir>
#   [--initial_db P] [--after_db P] [--container wh-zara-review]
# prints {"task_id": ..., "pass": true/false, "reason": ..., "evidence": [...]}
```

`<trajectory_dir>` holds `trajectory.json` + `screenshots/step_NNN.png` +
`initial.db` + `after.db` (the agent_demo run shape). If the DB files are
absent they are `docker cp`-ed from the running review container
(`wh-zara-review`, mirror port 46114).

## Task / contract map

| Task | Verifier | Navigation gates | DB after-state |
|---|---|---|---|
| Zara--0 | verify_0.py | dresses grid + BURGUNDY filter + sort + cheapest PDP | read-only |
| Zara--1 | verify_1.py | dresses grid + PDP | read-only |
| Zara--2 | verify_2.py | bags grid + RED PDP + bag page | +1 guest bag row (Red/ONE SIZE) |
| Zara--3 | verify_3.py | kids grid + PDP | read-only |
| Zara--4 | verify_4.py | jeans search + first-result PDP | read-only |
| Zara--5 | verify_5.py | trench coat search + first-result PDP | read-only |
| Zara--6 | verify_6.py | locator + HAWAII + store page | read-only |
| Zara--7 | verify_7.py | locator + ZIP + store page | read-only |
| Zara--8 | verify_8.py | locator + CA + Santa Monica + AZ | read-only |
| Zara--9 | verify_9.py | logon + bag | −dress row, boots qty 2→1 |
| Zara--10 | verify_10.py | logon + bags + RED PDP + bag + checkout + confirm | −2 bag rows, +1 order, +3 order items |
| Zara--11 | verify_11.py | logon + orders + delivered detail | read-only |
| Zara--12 | verify_12.py | logon + wishlist + PDP toggle | read-only (net-zero toggle) |
| Zara--13 | verify_13.py | register + PDP + checkout + confirm | +1 user, +1 order, +1 order item |
| Zara--14 | verify_14.py | logon + addresses | +SUMMER row, −HOME row |
| Zara--15 | verify_15.py | bags + PDP + bag + logon + carol bag | +1 guest bag row (Two-tone) |
| Zara--16 | verify_16.py | locator + AZ + HI + home + newsletter | +1 newsletter row |
| Zara--17 | verify_17.py | shirts + jeans + BLACK filter + PDP | read-only |
| Zara--18 | verify_18.py | perfumes + PDP | read-only |
| Zara--19 | verify_19.py | dresses + PDP | read-only |
| Zara--20 | verify_20.py | jeans + PDP + ECRU variant | read-only |
| Zara--21 | verify_21.py | logon + bag + orders + returned detail | −polo row |

## Determinism notes

- The frozen seed digests are computed over the logical schema + every row
  (table-canonical order); they pin the independently rebuilt in-image seed.
- Benchmark accounts use a frozen bcrypt hash so the seed is byte-reproducible;
  the one registration task (Zara--13) matches its new user row with a bcrypt
  pattern instead of a literal hash (salted hash is legitimately random).
- Order numbers are seed-state-deterministic (`80<uid><seq>` over the frozen
  order count), so they are pinned literally after the seed gate.
