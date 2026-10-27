# Terraform action capture

`terraform_actions.py` executes 36 isolated candidate-only cases: the 19 playable
land actions, seven enabled sea variants and ten compound commands. Monolith is
structurally disabled. The 29 visible source menu rows are not a count of domain
variants or completed actions.

One bounded case:

```sh
python3 tools/behavior-tests/state_trace/terraform_actions.py \
  --runtime /path/to/immutable/GLSMAC.js --case land:farm \
  --artifacts /tmp/terraform-actions
```

Omit `--case` to execute all 36 sequentially. Each worker gets a fresh native
seven-player 16×16 world, declared source rates of one turn, the real persisted
technology-waiver policy, an authored treasury budget and a capable land or sea
worker. Input setup finishes before the baseline. Mounted production menu rows
produce scalar event requests; the explicit display-free transport then runs the
actual event validator/apply path. Native display geometry, hit testing and SDL
delivery are separate browser checks.

Every case captures all seven owners, registered units/cities, identities,
research, balances, full-map height/corners/canonical state, terrain classes,
flags and construction owners, per-owner resources, work/automation, current
movement quotes and mounted selection/modal state. Begin/end manifests and
unique domain/row IDs make missing chunks an error. Native snapshots and queue
inventories fence read purity. Quotes remain distinct from actual command debit
and movement. Animation duration, audio and original height bytes stay explicitly
unsupported.

Primitive checkpoints (four observations) are `before`, `queued`,
`acknowledged`, and `after`.
Height adds pure `quote`, `cancelled-quote`, and `draft-payment` checkpoints
(seven observations total) before
authoritative confirmation. It records the actual height/fee policy identifiers,
full consent envelope and paid native work state. Same-order price/terrain/owner
changes invalidate consent; no process-local UI session identifier enters the
peer-compared event.

Compound commands add `exercised` (five observations total), then explicitly
cancel through the normal
authoritative plan event. Their completion binding says
`bounded-exercise-and-cancel`; it never claims map exhaustion. The separate native
automation suite must prove completion and effects for all ten commands. General
damaged/cooperative work, partial movement/rates, save/load, payment undo, sea
production, neighboring effects and representative traversal remain separate
completion gates in the master ledger.

Each `<case>.json` retains the exact runtime JS/WASM, worker, host snapshot and
generated fixture digests, complete stages/inventories and exhaustive observed
deltas. `<case>.log` preserves both passing and failing native output. The final
`manifest.json` uses `game.terraform_action_capture.v1`; it distinguishes selected
cases, successful application checks and the full inventory. Every report has
zero original passing cases. Source-guided functional height and automation
policies do not establish original agreement; immutable original observations
must be compared separately without tolerances or edited expectations.

The producer requires native script staging API v1. It registers stable outer
phase callbacks around one live fixture, native unit and mounted scene. Each
observation returns through an ordinary top-level accumulation boundary before
the next explicit action. Those boundaries collect finished invocation locals;
they never process game events, timers, turns or RNG. Full quote/draft captures
stay rooted only until the next real Cancel/confirm detachment check, and are
cleared before the next observation. The initial detached actor movement stays
as an exact Float scalar rather than retaining the entire first snapshot.

Owned-view cleanup is registered before setup and runs on failure as well as
success. The staged scenario cannot print its passing footer until all phases,
cleanup and normal Finish succeed. Cleanup/Finish must preserve the final native
graph, RNG and event inventory. An old runtime fails the explicit capability
check; it cannot silently fall back to one accumulation or omit trace fields.
The packet schema, order, case-specific observation counts, requested initial
seed and actual startup receipt remain unchanged.

This staged producer source still requires the combined runner/height/automation
runtime proof. Previous single-accumulation height captures reached all seven
observations but exhausted the heap during shutdown; they remain strict failures.
Parser tests validate corrupt transport rejection and must not be reported as
native execution. Actual execution and memory improvement require a new pinned
runtime, exact fixed-input field/Float parity, complete packets and raw exit zero.
