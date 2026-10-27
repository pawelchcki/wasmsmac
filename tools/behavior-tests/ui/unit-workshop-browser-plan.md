# Unit graphics and Workshop: separate candidate proof tracks

## Existing-design Workshop browser entrypoint

`tools/wasm-tests/unit-workshop-browser.test.mjs` is an optional installed-data
candidate application test. It is prepared in a separate follow-up branch; the
verified Workshop production freeze at `87d22ffe` remains unchanged. It requires
that freeze plus the shared cursor and native print-hook APIs accepted through
delivery source `256bff5c` (or their independently reviewed successors). The
follow-up source does not edit or copy those shared helpers.

After source review and an exclusive browser grant, the smallest real execution
is one serial test with an immutable compatible native/WASM runtime and matching
web shell, source root and installed assets:

```sh
SMAC_ASSETS_DIR=/path/to/installed/game \
WASM_APP_DIR=/path/to/immutable/web-shell \
WASM_SCRIPTS_ROOT=/path/to/combined-reviewed-source \
WORKSHOP_BROWSER_ARTIFACTS_DIR=/tmp/unit-workshop-browser-attempt-1 \
node --test tools/wasm-tests/unit-workshop-browser.test.mjs
```

This is one launch with the existing 180-second test limit. Missing source,
runtime API, resource fingerprint, geometry, input receipt, state or rendered
evidence fails closed. A retry must use a new artifact directory and source
freeze. Source syntax/adapter checks are not a browser pass; neither the new
GSE fixture nor this complete flow has executed yet.

Source preparation replayed 79,810 retained actual native presentation events
from the earlier Terraform capture through the adapter, checking eight live-node,
label, bounds, visibility and sequence boundaries. Ten additional synthetic
protocol-boundary checks cover scoped dialog/list membership, selected/modal/
focus fields, ambiguous text, missing keys, destroyed rows, hidden ancestors and
dropped events. These are parser/adapter checks with zero engine/browser runs;
they do not turn the earlier incomplete Terraform attempt into a Workshop pass.
The reproducible local source check and exact hashes are retained at
`/tmp/unit-workshop-adapter-check.mjs` and
`/tmp/unit-workshop-adapter-source-check.json`.

The synthetic 16×16 world retains all seven native owners, seven cities, eight
units and all 128 tiles. Its production inventory registers actual installed
basic/optional naval recipes, prices and population requirements. This is an
explicit input inventory, not an inferred technology result. Source rules,
technology/research/energy, city production/citizens and every unit/tile remain
observed by the existing complete native observer.

The fixture focuses its owned city through the existing native projection API,
then the browser physically clicks that reported map point. It opens production
and WORKSHOP through real mounted native controls. Every later button comes from
one visible native dialog, its actual `$button`, mounted text and effective
bounds. A chooser row additionally requires native `semantic.choice` membership
with its stable key, label and node. No source ordinal, invented coordinates,
guessed viewport or direct controller call authorizes input. Shared
`nativeToCanvas`, `nativeHover` and `completedNativeClick` connect actual geometry
to SDL ingress and completed application dispatch. Focus/modal state is retained
as observation, independently of inferred visibility or selection.

The flow checks the full inventory, source name/cost/stats, stock Former preview,
pointer Cancel, physical Escape, draft-only SELECT, normal production OK, stale
base refresh and base hide/reopen cleanup. UI-only stages compare complete native
snapshots unchanged and forbid production receipts. Normal OK requires exactly
one accepted production event and the chosen native project; only that city's
project/minerals/processed-turn fields may differ, with switch loss read from the
actual existing native query. Other native fields remain exact. Stale-context
setup arms a declared native `game.select_base` refresh after a live Workshop has
been observed. It never calls `screen.set`, `hide`, `choose` or any production
handler. The selected base's normal reconciliation still runs and is observed.

A separate declared black-backed pixel control loads authentic `VT.cvr` through
the normal installed asset bridge/loader. Its accepted source SHA is checked in
the actual remote manifest. Dynamic native geometry and the actual canvas box
identify both pixel regions; the Workshop must contain the component's observed
physical palette. Full screenshots, acquisition times and native region metadata
are retained. This is a candidate resource/preview relation, not original camera,
composition, color/shading or pixel agreement.

## Observation and input handling audit

Modal Windows consume root query keys. The observer therefore attaches one
read-only query listener to each actual base/Workshop Window, retained until its
normal native destruction. `popup.gls.js`'s created Window key handler and
`base_screen/workshop.gls.js`'s Window key handler already return `true` for every
key path. `src/gse/Wrappable.cpp::Trigger` copies the ordered callback map and
runs every callback; the final return wins. The observer also returns `true`
for every key, preserving the existing result and every existing callback.
It does not add a root listener that returns `false` after handled Escape.

Reserved Ctrl+Alt+P increments a query and queues observation. The actual native
keydown ingress/begin/end must complete. The owned timer reads fresh native
state after the callback returns; it never snapshots during input dispatch or
uses a world snapshot taken before mouseup. `Input::ProcessEvent` emits dispatch
end after the UI callback stack returns; GSE timers run from the later
`GLSMAC::Iterate`/GSE async iteration. The timer then prints the observation and
drains actual presentation packets. Browser acceptance retains both the native
query receipt and the uniquely advancing query number. Ctrl+Alt+J arms only the
declared native context invalidation; Ctrl+Alt+Q queues native exit for teardown,
which is explicitly not an original quit-dialog comparison.

Window attach/remove records, native show/hide/destroy, modal/focus/selection,
actual effective geometry and input events are distinct observables. Production
default, observer fixture, world input, observer helpers, shared helper files,
runtime JS/WASM and web shell have separate hashes. The existing test-only print
hook installs before the unmodified native runtime captures its configuration.
The cursor retains every UTF-16 suffix and raw chunk, closes the producer before
sealing, and marks incomplete capture honestly. Raw exit zero, normal bootstrap
`exited` status, complete fresh snapshots, no dropped native events and retained
logs are required for a real pass.

## Existing unit graphics: reachable ordering witness

Source-only audit identifies an application inconsistency, not yet an executed
visible failure or original comparison:

1. On a base-free tile, create two owned healthy Scouts A/B with movement and
   NO_ORDERS, morale 2/1. `Unit::GetSelectionWeight` gives A weight 272 and B 270
   (active 200, the current Scout category term 60, morale 4/2, health 8).
2. Select/preview that populated tile through the ordinary frontend path. A call
   to `Tile::GetMostImportantObject` or `GetMostImportantUnit` warms
   `GetOrderedUnits` and `GetOrderedObjects`, storing A first.
3. Issue a legitimate Hold or Sentry to A and wait for actual native ACK plus
   `FR_UNIT_UPDATE`. `Unit::SetOrder` flags refresh; `Unit::Refresh` recomputes
   A's active state. A now weighs 72; B remains 270. Tile membership, morale,
   health and positions are unchanged.
4. `UnitManager::RefreshUnit` calls `Game::RenderTile`, which calls
   `Tile::Render` and computes a fresh local `GetUnitsOrder`. It does not
   invalidate the two cached order flags. Those flags are only changed by
   AddUnit/RemoveUnit and base membership paths, not this weight change.
5. `Game::SelectTileOrUnit` fallback, `Game::UpdatePreviews`,
   `Game::GetSelectedTileMostImportantUnit` and `UnitManager::DeselectUnit` then
   consume the stale cached first unit A. Re-selecting the tile can fall into
   tile selection/preview A even while active B has greater current weight.

The smallest meaningful executed probe must use real frontend units and this
actual caller sequence, pin A/B native IDs, warm the cache before the order
change, retain the native order receipt, then capture actual unit-select versus
tile-select events and the mounted preview's unit ID/order after re-selection.
It must check all seven owners' native state and allow only A's legitimate
order/readiness change. A complementary health-only case can change weight
without membership or turn advancement. A later cache-invalidation fix must
make the same pre-recorded probe agree with fresh current priority, without
changing the source weight policy, original observations or UI expectations.

There is currently no public frontend telemetry for the rendered map instance's
unit identity, cached order vector, facing or animation frame. Pixel/body identity
and cache introspection are explicit gaps; a read-only seam would need a separate
file lease, review and fresh native build. This follow-up changes no C++ and
claims no executed cache defect yet.

The earlier `ShowFakeBadge(!instance_id)` lead is latent under current callers.
`Tile::Render` is the only production caller of `ShowFakeBadge`; before rebuilding
it hides and clears every retained fake badge. Move/despawn/tile-transfer paths
also clear them. Thus the replacement-ID branch has no demonstrated reachable
production path. It remains unchanged instead of being counted as a visible fix.

## Concrete graphics and Workshop gaps

| Area | Current bounded support | Unsupported |
| --- | --- | --- |
| Existing bodies | Authentic stock Former VT chassis; existing other-role fallbacks | Complete Scout/Pod/SeaFormer assemblies and tools |
| Movement | Existing body interpolation and badge blink | Original facing, trajectory/cadence and intermediate-frame agreement |
| Work/animation | Existing PSI attack/death clips; resource metadata only for Former tools | Farm/Raise/etc. clip binding, limbs, transforms, visibility and timing |
| Workshop | Existing source designs, stats, guarded preview, production draft handoff | Authoring/customization, save/obsolete/upgrade, rotation and original UI layout |
| Browser proof | Source-prepared native Window/SDL/state/pixel acceptance | Actual execution until an exclusive slot is granted; original passing cases remain zero |
