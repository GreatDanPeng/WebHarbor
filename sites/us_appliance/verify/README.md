# us_appliance verifier contract

One deterministic verifier per task (`verify_0.py` … `verify_19.py`) plus the
shared `verify_lib.py`. Recorded in `tasks.jsonl` as `verifier_path` +
`judge_rubric` by the reviewer; ground truth is **hardcoded inside each
verifier** and never lives in `tasks.jsonl`.

## Signature

```
python3 verify_<n>.py --run_dir DIR [--initial_db P] [--after_db P]
```

- `--run_dir`: agent trajectory directory (`trajectory.json` +
  `screenshots/step_NNN.png` in the `agent_demo/agent.py` shape).
- `--initial_db` / `--after_db`: initial-state and after-state SQLite
  snapshots. Defaults: `<run_dir>/initial.db` / `<run_dir>/after.db`; when a
  file is missing the verifier `docker cp`s it from the review container
  (`$WH_CONTAINER`, default `wh-us-appliance-review`).
- Output: JSON `{task_id, pass, reason, evidence[]}`; exit 0 on PASS, 1 on
  FAIL. No LLM call is load-bearing.

## Gates (fail-closed, in order)

1. **Package identity** — `task_id` matches, trajectory terminated with
   `agent_done`, non-empty final answer, every recorded URL on the same
   loopback origin AND port as `start_url`, every referenced screenshot a
   decodable PNG.
2. **Seed identity** — the initial DB must BE the frozen seed:
   16 tables with exact row counts (12,778 products / 518 categories /
   101 brands / 8 orders / 300 reviews / 46 rebates / 9 guides / 12 FAQ
   items / 20 content blocks / 63,566 related-product rows …), schema
   digest `f445c6f2…`, canonical row digest `3bcea48f…`, file md5
   `d0c84438…`. A run graded against a pre-mutated database fails here.
3. **Navigation gates** — per task, the agent must have opened the
   on-site surfaces the task names (category grids, product pages, search
   results, cart/checkout, support pages). A correct answer with no
   matching navigation is a memory-recall shortcut = FAIL.
4. **Answer ground truth** — affirmative token/phrase/number/money checks
   against values frozen from the reviewer's independent walkthroughs of
   the review container. Where a task wording admits two defensible
   readings (e.g. "the cheapest one shown" before/after sorting), the
   verifier accepts each defensible name/price pair.
5. **DB after-state** — read-only tasks require every table row-identical
   to the seed; stateful tasks require the exact allowed row delta (and
   nothing else) in exactly the allowed tables:
   - T2/T15/T17: one `cart_items` row (the task's product at qty 1)
   - T3: `orders`+`order_items`+`order_events` each +1 (guest order 10009)
   - T12: `price_match_requests` +1
   - T16: `users`+`orders`+`order_items`+`order_events` each +1
   - T19: `newsletter_subscribers` +1

## Tests

`tests/` holds the adversarial matrix (`test_verifiers.py`, run with
`python3 -m pytest sites/us_appliance/verify/tests -q`): honest fixtures
transcribed from the reviewer's live runs must PASS 20/20, and no-op /
knowledge-shortcut / wrong-answer / stale-DB / wrong-mutation / extra-write /
tampered-package / pre-mutated-seed attacks must all FAIL. Seed DB for the
fixtures is fetched from the review container; `US_APPLIANCE_TEST_SEED_DB`
overrides the cache path.

## Provenance

Ground truth values were frozen from the reviewer's independent container
`wh-us-appliance-review` (image `webharbor:us-appliance-review`, built from
contribution `a9435607` through the real Dockerfile site block; seed sha256
`56e46fa0…`, reproduced across 20/20 task resets and two fresh in-image
`PYTHONHASHSEED=0` seed rebuilds).
