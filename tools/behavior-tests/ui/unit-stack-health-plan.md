# Candidate unit health ranking and movement observations

This is a source-only follow-up to the verified Hold cache repair at
`b6a80a056cee421e7c6a1bb727664939052c7c2f`. It adds four new files on a separate
branch. It changes no production Default, C++, existing witness, expected
selection policy, shared browser helper or current PR delivery head. No engine,
browser, build or original game has executed this new health case.

## Health fixture and acceptance

`unit-stack-health-browser-fixture.mjs` exports `stackHealthWorld` (the exact
existing seven-owner, seven-base, nine-unit, 128-tile stack world) and a new
`stackHealthMain`. The initial two Scouts remain healthy, active and without
orders at the base-free (8,8) tile. A has morale 2; B has morale 1.

The fixture registers the isolated event `fixture_stack_health_half_v1` through
the native `game.register_event` API. Its validator requires the live scalar
actor ID, native caller/current owner, unfinished current turn, declared nonce,
full prior Float bits, exact new Float half-health, unchanged source definition,
morale, moves, orders, position and unlocked tile. Apply revalidates, writes only
the backend native `unit.health` setter, reacquires the actor and verifies the
new bits. Scalar apply and rollback counts independently require one application
and zero rollbacks in the successful case. Rollback validates the native live
identity and exact half-health before restoring the prior health; it is not a
passing or exercised rollback case.

`Game::ProcessEvents` validates and applies registered events inside its normal
native write boundary. `NotifyEventResult` emits the actual String transaction
token, String command, Int caller and copied scalar inputs with Bool success.
The fixture records those actual types and the exact input nonce, actor, owner,
turn and health bits. A timer submits the event and waits for observations; it
never writes frontend fields or backend health itself. This is a declared
synthetic test control, not a simulated combat outcome or an original damage
contract.

The native update source path is:

1. `backend/unit/Unit.cpp`: dynamic Float `health` setter → `OnWrapSet`.
2. `backend/unit/UnitManager.cpp`: `RefreshUnit` queues `UUO_REFRESH`;
   `PushUpdates` sends the actual health in `FR_UNIT_UPDATE`.
3. `frontend/Game.cpp`: `SetHealth` then `Unit::Refresh`.
4. `frontend/unit/Unit.cpp`: changed health sets `m_need_refresh`; the existing
   three-file repair invalidates both ordering caches before
   `UnitManager::RefreshUnit` renders and updates previews.

No further C++ change is proposed. Current source weights are A=272/B=270 with
full health and A=268/B=270 after A's health becomes 0.5. Both remain active. The
known `UnitDef::IsArtillery` policy and all tie/explicit-selection behavior stay
unchanged. These numbers describe current application source, not original-game
unit selection.

The first warm barrier requires an actual native tile-select, newer native map
unit-preview(A), matching mounted Widget ID/text ID and null explicit selection.
After the fixture event, both its actual matching receipt and a NEW native map
preview are required. The callback's relation to `FR_UNIT_UPDATE` is source-backed;
a direct native frontend-request cause ID remains unsupported. Native tile
reselection then requires another fresh tile-select/preview and matching actual
mounted Widget. No expected ID is inserted into an observation. Stale A remains
a complete mismatch only if every other guard succeeds.

Each of `warm`, `after_health` and `final` immediately serializes a separate
complete all-owner world using `#json_text_exact`. Native wrappers and FloatPtr
observations are not retained across actions. A separate scalar row for every
unit records actual native ID/owner types, health/movement Float types and exact
`#float_bits` values. Full health bits are `0x3f800000` (1065353216); half-health
bits are `0x3f000000` (1056964608). The evaluator requires all nine rows to agree
with their world values and native owners. Only A's world health and matching
health bits may change; terrain, locks, treasury, all opponents, quotes, activity,
orders, moves and every other recorded field remain guarded. Any additional
mirror/derived difference is an invariant failure to investigate, not permission
to broaden the allowed diff.

`unit-stack-health-proof.mjs` checks exact raw event rows against the final event
prefix, serial ordering, checkpoint action order, immediate event-prefix
boundaries, metadata equality and exactly one of each independent world. It
rejects missing/duplicate results, native failures and unsupported prefixes.
`evaluateUnitStackHealthLog` additionally requires actual native exit zero,
sealed nonpartial raw bytes, matching SHA-256 for retained raw/joined chunks,
one main/eight worker hook acknowledgements and canonical out/err/callMain flags
before evaluating the HUD. The future launcher must derive those prerequisites
from actual execution and canonical helper receipts; supplied synthetic test
metadata is not evidence of a game run. Evaluation always reports zero executed
candidate/original cases of its own.

Fifteen committed asset-free synthetic checks cover complete match versus
complete guarded mismatch, receipt types and identity, actual callback barriers,
Widget agreement, full inventory, unrelated mutations, Float bits, one-shot
application, raw boundary order, checkpoint drift, exit/seal and native failure
classification. They execute no game or native engine. Node syntax checks do not
parse the GSE string.

Before a live case: independent source review, native fixture scalar/event sanity
where supported, exact source/Default/runtime/asset/helper pins and an exclusive
Root grant are required. A future new launcher should reuse canonical transport
without editing the verified Hold or Workshop launchers. On each runtime use the
same inputs and expectation, strict actual application exit zero, producer close,
drain/seal and owned worker reaping. Preserve a complete old-runtime mismatch;
classify setup, type, state or shutdown failures separately. An unchanged new
runtime pass would add bounded health-path coverage, not another cache fix or
proof of original map rendering.

## Movement: source audit and proposed read-only observations

Current source evidence (unexecuted in this follow-up):

| Source boundary | What it establishes | What it does not establish |
| --- | --- | --- |
| Backend `MoveUnitToTile` | Source/destination tile locks, actual `FR_UNIT_MOVE`, native animation ID and a guarded completion callback | Intermediate map-body pose or original timing |
| Frontend `UnitManager::MoveUnit` | Moving-unit record, old tile removal, destination selection and `Unit::MoveToTile` | Which actual drawn unit instance appears in a frame |
| `Unit::MoveToTile` | Existing sprite is shown; translation starts between actual tile render coordinates, using `GetCloserCoords` for wrapping | Facing changes, stepping/tool clips or model assembly |
| `Unit::MOVE_DURATION_MS` / `util::Scroller` | Requested 125ms duration, 10ms steps and integer division to 12 steps | Measured wall duration, cadence or original-game parity |
| `Unit::Iterate` / `SetRenderCoords` | Scroller ticks update actual unit, badge and health-bar actor instance positions | Exposed read-only observation of those instance positions |
| Frontend moving completion | Actual `SetTile`, selected-tile refresh and `SendAnimationFinished` | Whether the renderer displayed the final frame before completion |
| Backend completion callback | Clears animation, unlocks tiles, updates canonical tile and runs continuation before pending-action completion | Visual settle time or independent body identity |
| `UnitDef::GetSprite` | Static sprite/optional morale atlas offset selection | Direction-dependent frame, facing, pose, clip or Former action mapping |

The first useful observation addition would be a read-only packet at actual
frontend movement start, coordinate update and completion. Proposed minimum
fields are native unit/owner ID, source/destination logical tiles, native
animation ID, frontend action sequence, exact actor-instance ID, source resource
identity, visible flag, actual render coordinates, camera/world-wrap context and
monotonic observation timestamp. A completion packet should distinguish final
coordinate update, frontend tile membership update, animation-finished send and
backend acknowledgement. Do not read the world while mutation/dispatch is in
progress; keep complete native state checkpoints independent of render packets.

This is a telemetry proposal only. Its instrumentation seam, overhead, lifetime,
native source compatibility and exact event causality still require separate
review. No fields are added to C++ here. Frame/facing/clip/pose fields must be
explicitly absent when unsupported; zero values would falsely imply capability.
In-flight sentinel coordinates are not valid world positions. Requested 125ms
and 12 Scroller steps are source facts, not an executed timing contract or a
demonstrated timing bug.

A later bounded movement case should use one normal declared land move, actual
native command receipt and completion, all-owner before/during/after guards,
actual map-body ID/trajectory evidence and normal exit/seal. Original-only work
may supply clean observable expectations through Root without candidate
implementation details. Rendered map identity, original orientation/frame cadence,
Former full assembly/tools/limbs, action clips and audio timing remain unsupported
by the present HUD and Workshop proofs.
