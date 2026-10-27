# Aquifer plan reuse checkpoint

The real 4,096-tile cooperation capacity attempt exhausted the unchanged 2 GiB
WASM limit before guard encoding. A counter-only replay completed the first
16,544 geometry reads, 4,096 feature-patch reads, and native terrain validation.
It then repeated the geometry search (33,088 cumulative reads) and reached
7,680 cumulative feature reads before aborting. Full terrain-state reads remained
at one. This evidence supports removing duplicate per-call route construction;
it does not establish a problem in the later identity guard allocation.

`terraforming_effects.plan` now asks its private validation implementation to
retain the exact route array after successful native validation. Assignment into
a fresh local result object preserves the array reference in GSE. Planning
returns that same array. Standalone public validation retains its four-argument
signature and existing undefined/reason results. There is no global cache,
changed route search, tie breaking, ordering, patch fields, validation bypass,
transaction capacity increase, or original-game fidelity claim.

The `aquifer-plan-reuse` regression uses two declared small native water-outlet
inputs. A forwarding TileManager records the actual array submitted to native
validation. The plan must match those complete ordered patch bytes, validate
once, and perform the same geometry/feature reads as standalone validation.
It prints exact patch JSON and the real cooperative identity for independent
old/new byte comparison, preserves native world/terrain/inventory state, and
checks that an already existing river still produces the same rejection.

At this source checkpoint only the eighteen pure lane checks have run. Native
old/new parity and the unchanged 4,096-tile capacity and 512 KiB boundary tests
remain pending; the previous failure is preserved separately.
