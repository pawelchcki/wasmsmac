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
