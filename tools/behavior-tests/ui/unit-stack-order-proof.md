# Existing unit graphics: minimal real frontend cache witness

This independent source-only probe targets the current application's cached unit
priority after a legitimate Hold order. It changes no C++, game priority policy,
Workshop production or original observations. No native/browser probe has run;
the predicted stale visible binding remains a hypothesis.

Source preparation passes Node syntax checks for the two modules and 13 synthetic
evaluator boundary checks, including a complete stale-ID mismatch, a fresh-ID
match, wrong transaction type/name, missing frontend refresh, unrelated native
mutation, inconsistent Widget binding and missing/duplicated action boundaries.
The source-only script/result are retained at
`/tmp/unit-stack-order-proof-check.mjs` and
`/tmp/unit-stack-order-source-check.json`. They execute no engine/browser and
add no passing game or original cases.

`tools/wasm-tests/unit-stack-order-browser-fixture.mjs` exports `stackOrderWorld`
and `stackOrderMain`. The world reuses the separately declared Workshop world
input, replacing its one local Former spawn with two ordinary Scouts at the
base-free (8,8) tile. All seven owners, seven cities and nine units remain live.
A has morale 2, B morale 1; both have full health/movement and no orders. The
current public source priority is A=272/B=270, then A=72/B=270 after A Holds.
These are application-policy inputs, not an original-game selection contract.

The self-running GSE fixture uses actual native public requests and read-only
payloads, with no replacement callbacks, Native wrapper arrays or fake frontend:

1. Reacquire scalar native A/B IDs. Wait for the existing native rendered-city
   focus capability, then `game.select_tile` queues the real FR_TILE_SELECT.
2. Require the resulting actual tile-select event, a subsequent actual map
   unit-preview(A), and the mounted Native Widget's `preview.data.unit.id == A`
   plus its real text binding. This warms the actual tile order caches.
3. Submit the legitimate authoritative `unit_hold` request with scalar A ID.
   Preserve its actual String transaction token, Int caller/entity IDs and Bool
   result. A backend ACK or the independent 100ms GSE label timer is insufficient.
4. Require a NEW actual map unit-preview after the Hold fence. Its source path is
   FR_UNIT_UPDATE → Unit::Refresh → UnitManager::RefreshUnit → RenderTile →
   UpdatePreviews. This is the frontend refresh barrier; capture the native world.
5. Queue another actual native tile-select and require the corresponding new
   tile-select followed by map unit-preview and matching mounted Widget/text IDs.
   Capture the complete result before normal native exit. No expected ID is
   substituted into the observation.

`unit-stack-order-proof.mjs` exports a strict evaluator and log parser. It checks
the exact event fences, identity types, actual Widget/event agreement, complete
all-seven/128tile coverage and all native fields. Only A's legitimate order may
change. It then compares the actual final Widget binding to current priority B.
The stale A observation, if reached, is retained as a complete strict mismatch.
Unsupported/setup failures never count as a visible cache defect or a pass.

Each complete world is serialized immediately into its own `UO_CHECKPOINT` log
record at warm/after-Hold/final boundaries. The fixture retains only plain scalar
UI/event metadata between actions. It does not retain native FloatPtr-backed
world values and reserialize them later, which could hide unrelated mutations.
The parser requires exactly those three independent immutable boundaries and
matches their metadata to the final result before evaluating any agreement.

For a future exclusive real run, mount the two exported fixture sources through
the reviewed candidate browser host with the current exact CDP print barrier,
cursor, immutable runtime and installed assets. Only the synthetic main/world
entrypoint changes; keep the product scripts/units and priority unchanged. The
existing Workshop browser host is still undergoing first-run repair/review, so
this probe deliberately does not copy its transport or pretend a second launcher
is verified. That mounting/launch adapter remains a preparation gap. Retain
runtime/default/observer/helper hashes, actual native exit zero and sealed raw
logs before invoking:

```sh
node tools/wasm-tests/unit-stack-order-proof.mjs \
  /tmp/unit-stack-order-attempt-1/application.log \
  /tmp/unit-stack-order-attempt-1/priority-result.json
```

This proof can establish the actual selected HUD's unit identity using the native
Widget payload; `widget/UnitPreview.cpp` binds that payload to the frontend unit
ID. It cannot establish the rendered map instance identity, original pixels,
facing, movement cadence, tool/limb animation or audio. Those remain explicit
graphics gaps. A later C++ cache-invalidation change requires actual failing
evidence first and must preserve the same witness and source priority policy.
