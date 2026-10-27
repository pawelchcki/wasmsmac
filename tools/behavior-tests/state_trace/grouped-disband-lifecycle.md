# Grouped disband lifecycle checkpoint

The original published seven-case disband controls body and its 47 assertions
remain byte-for-byte unchanged in `_unit_disband_regression_cases.gls.js`.
Its single accumulation exhausted the unchanged 2 GiB WASM limit in CI after
body markers, before strict completion. The separate `6f6603a8` experiment
staged each unchanged case with separate empty BEGIN and deferred PASS callbacks.
It produced 22 stage callbacks. A read-only process diagnostic preserved its
120-second timeout. A separately authorized 240-second **observational** run
completed normally in 237.036 seconds with seven scenarios / 47 assertions and
`All tests passed`; this is not a passing 120-second CI check or a timeout fix.

That observation showed CPU-active finite progress. Even empty bookkeeping
callbacks were followed by multi-second boundaries; their timestamps include
commit, collection and dispatch, so they are not isolated GC timings. Historical
full environments and the ephemeral original fast-worker prefix were not saved.
The diagnostic pins the original worker and complete GSE snapshot hashes, records
known launch differences and marks WASM capacity unavailable. An earlier supplied
host hook accessed a non-exported Emscripten property and aborted; that invalid
attempt remains excluded from causal evidence.

`_behavior.group_staged` uses the existing public test-stage APIs. Every real
case runs in its own top-level callback: BEGIN, unchanged body, and a completion
flag bound to that case. One deferred callback verifies every completion before
emitting the seven PASS markers. The worker's existing final summary callback
remains separate. Cleanup and normal `GSE::Finish` must succeed before either
callback runs. This reduces this producer to nine callbacks while preserving
all seven genuine case collection boundaries, names, order, inputs, observations,
inline UI cleanup and strict native shutdown. No C++ collector algorithm,
production cadence, heap limit or global timeout changes.

The existing `script-stages` native fixture additionally exercises grouped FIFO,
real unit/UI/callback identity, exact movement bits, no implicit event/timer
progress, and cleanup-before-completion. Two underscore expected-negative probes
cover an actual grouped-body exception and a cleanup exception with real native
snapshots and owned repeating timers. Optional runtime-backed Python checks
require their exact intended failure, actual cleanup, normal failing-test return,
and the absence of PASS, summary and success markers; these are not passing game
cases. Native verification of this new source checkpoint is still pending.

## Bounded independent packets

The grouped nine-callback attempt also preserved all seven cases / 47 assertions
but timed out at the unchanged 120-second gate after its summary at 112.996
seconds. It remains a failed gate. Therefore the logical catalog suite must run
three independent packets selecting original indices `[0,3)`, `[3,5)`, `[5,7)`.
The complete canonical script remains available for direct native callers.
Packet scripts are underscore producers, not duplicate default-native tests.
Each uses the same helper and actual original case entries, with an explicit
indexed-value materialization required by GSE's ArrayRef semantics.

Every packet gets an unchanged 120-second isolated worker and 2 GiB limit. This
is explicitly up to three worker budgets / 360 seconds of serial worker time,
plus launch/report overhead, not a larger global timeout. The logical suite can
pass only after all three workers report their actual native success footer and
raw zero exits, with exactly the original seven names in source order and 47
assertions in aggregate. No joined output is reparsed as a fabricated single
native run, and no synthetic native footer is emitted. A packet never serializes
or recreates a live case halfway through: each original case already constructs
and removes its own fixture. Dynamic IDs remain obtained from that case's real
native entities. Cross-case chronology across different workers is not claimed
as gameplay timing; the ordered logical corpus and each case's action sequence
are preserved.
