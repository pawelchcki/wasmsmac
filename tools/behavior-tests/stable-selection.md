# Preparatory Stable selection plan

`stable_selection.py` only prepares a coverage plan. It runs no candidate,
original, engine, browser or reference checks and cannot satisfy a CI gate.
No existing workflow or lane membership consumes this plan yet.

The v1 profile records the proposed partition, **45 Hot + 135 Stable = 180
regression suites**, including 31 proposed moves from today's 76 Hot suites.
All 11 current Hot UI references, eight recorded startup native projections,
complete seven-player terrain/traversal and identity observations, cooperative
owner packets, Float/JSON transport, minimum-size native generation and Base
Operations navigation remain required Hot coverage in the proposal. Six fixed
all-owner Terraform action representatives stay Hot; the complete 36 action
capture IDs remain required expanded Stable coverage. These capture invariants
are not original-game agreement cases.

**Version 1 always selects complete Stable coverage.** Its path-to-area patterns
are diagnostic starting points, not independently established transitive
dependencies. Mapped paths therefore carry `unreviewed-dependencies`; unknown
paths carry `unmapped-path`. Empty diffs also select complete Stable. No v1 flag
can enable narrower dependency selection. Before narrowing, independently review
the dependency map and introduce a reviewed schema/profile change with coverage
and adversarial tests. Until then, this preparatory step offers auditability,
not a CI latency reduction.

A request is strict JSON, using exact lowercase 40-character commit SHAs:

```json
{
  "version": 1,
  "base_sha": "1111111111111111111111111111111111111111",
  "head_sha": "2222222222222222222222222222222222222222",
  "inventory_sha256": "COPY_THE_CURRENT_REVIEWED_PROFILE_INVENTORY_HASH",
  "changes": [
    {"status": "M", "path": "src/gc/Space.cpp"},
    {"status": "R", "old_path": "src/old.cpp", "path": "src/new.cpp"}
  ]
}
```

Run from a clean committed source checkout:

```sh
python3 tools/behavior-tests/stable_selection.py \
  --request /tmp/stable-selection-request.json \
  --report /tmp/stable-selection-report.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tools/behavior-tests -p test_stable_selection.py -v
```

The CLI independently reads `git diff --name-status -z --find-renames`, checks
both rename/copy sides, requires the actual HEAD and a valid ancestor merge
base, rejects tracked uncommitted changes, and compares all declared changes
with the actual diff. A future workflow must supply the trusted current PR base
and final head; this tool cannot determine a remote PR's current base by itself.
The report must be outside the source checkout and cannot overwrite request or
profile inputs. An invalid invocation removes an earlier report at a valid
report destination and exits nonzero. Malformed paths, control characters,
absolute/traversal paths, unknown request/profile schemas, stale bindings,
unclassified catalog IDs and changed coverage unions fail closed.

The inventory fingerprint covers current lane/catalog metadata, synthetic case
inputs (including pending inputs, separately excluded from passing totals), the
source-declared Terraform action inventory and eight startup projection IDs.
It reads no recorded output observations. Adding/changing cases requires a
refreshed profile inventory hash and independent review. Reports include the
base/head, profile/inventory hashes, exact current suite/capture IDs, matched
areas and fallback reasons. `candidate_executed` and `gate_satisfied` are always
false; no runtime hash or executed/passing result is asserted.

Future integration must require successful exact-head Hot **and every selected
Stable execution before merge**, retain protected contexts and Main health,
reject missing/skipped/stale/unsupported required results, and preserve the full
Main/GSE/native/WASM/browser coverage union. Selection reports alone cannot do
this aggregation. Pending UI, unsupported gaps, static archives, private
reference captures and installed-asset checks stay outside public passing totals.
Repair the observed startup single-case stall before migrating any failure
checks. A separately reviewed CI change must integrate these prerequisites
before any suite/capture moves out of Hot.

The inventory binding includes every regression GSE script and included test
helper, not only catalog rows and JSON cases. Changing those inputs requires a
reviewed profile refresh even while v1 keeps its full Stable fallback. CLI copy
detection includes unchanged sources; both paths remain visible in diagnostic
area matching. Parse errors remove a prior report only when its destination can
be safely identified and validated. Final-component report symlinks are rejected
without unlinking them or their targets; all writes use the validated canonical
outside-checkout destination. No execution gate or lane migration is added.
