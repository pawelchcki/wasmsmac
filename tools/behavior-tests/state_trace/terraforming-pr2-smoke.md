# Terraform controls and complete-action acceptance

Use a frozen full GSE host with a matching immutable native runtime. The current
verified staging baseline is source `ade25925`, native tree
`99976bc17b8218e7c1de18c57887df11ac097e9e`, runtime
`/tmp/wasmsmac-terraform-pr2-runtime-v4/GLSMAC.js`. JS SHA-256:
`48b70b1a4eb834687755850b3df54293701382dc81bfa6312e751200d401ec8c`;
WASM SHA-256:
`62406811649411ff044183fe0b7d491f489443557939ffffda97cf27c52dd775`.
The delivery checkpoint rooted in merged main has the same complete tree.
Record a new full-host digest for every later change; supporting older results
must retain their actual source and runtime identities.

The catalog already registers `terraforming-controls-all`, `terraforming-dialog`,
`former-controls` and `native-input-state` in active hot coverage. Mounted
handlers and input guards have supporting native passes; they do not establish
real browser rendering or input delivery. Run the applicable suites again after
controller, work or authority changes:

```sh
python3 tools/behavior-tests/fast.py \
  --runtime /path/to/immutable/GLSMAC.js --jobs 1 --timeout 120 \
  --suite terraforming-controls-all --suite terraforming-dialog \
  --suite former-controls --suite native-input-state \
  --report /tmp/terraform-pr2-ui-smoke.json
```

The staged native runner, live-world script and targeted terrain/automation/work
compatibility now pass. Matched height traces preserve all 138,158 typed fields
and exact Float bits while the staged worker exits cleanly with flat sampled
481 MB WASM capacity. The complete 36-action run remains independently gated by
its final manifest; do not infer it from the one-case memory result.

```sh
python3 tools/behavior-tests/state_trace/terraform_actions.py \
  --runtime /path/to/immutable/GLSMAC.js \
  --artifacts /tmp/terraform-pr2-all-actions
```

This executes 19 land variants, seven sea variants and ten commands in isolated
workers. Every selected case must report `passed`, native execution, complete
ordered observations, all seven owners and all 128 map tiles, actual effects or
steps, complete identities and raw exit zero. Preserve failed and unexecuted
rows separately. Height has seven observations, including pure quote, Cancel
and draft payment followed by real confirmation. Commands exercise real work
or movement and then cancel; the separate all-ten completion suite establishes
completion rather than map exhaustion in these bounded traces.

Run the actual pointer lifecycle browser smoke only with an exclusive browser
slot. `WASM_APP_DIR` identifies a complete web shell containing the pinned native
runtime; `WASM_SCRIPTS_ROOT` selects the frozen production host independently
from the browser harness checkout.

```sh
env FONTCONFIG_FILE=/tmp/glsmac-fonts.conf \
  PLAYWRIGHT_BROWSERS_PATH=/var/home/pawel/.cache/ms-playwright \
  SMAC_ASSETS_DIR=/var/home/pawel/reimplementation/smac-wasm/smac-assets \
  WASM_APP_DIR=/path/to/pinned/full-web-shell \
  WASM_SCRIPTS_ROOT=/path/to/frozen-pr2-checkout \
  TERRAFORM_CONTROLS_ARTIFACTS_DIR=/tmp/terraform-pr2-pointer-smoke \
  node --test tools/wasm-tests/terraform-controls.test.mjs
```

The smoke checks 29 distinct source rows, an actual non-base click, Escape and
Tab cancellation, and owned-base pointer dispatch while preserving all seven
owners and the map across pure controls. Rows are not domain variants or 36
completed actions. This browser proof remains pending on the complete current
host. Native traces cannot set `browser_verified`.

Separate functional acceptance still covers nonheight cooperation, two fresh
40×80 road and Tube worlds, actual source-produced SeaFormer production/port/home,
height payment and mesh refresh, progress presentation and keyboard context.
Real work-animation action binding, original fees/height/contour/climate,
original traversal timing and priorities, complete audio and typography remain
explicit fidelity gaps. Every action report retains zero original passing cases.

The producer requests the preregistered native initial RNG state
`1651011033:1377505029:3019448108:3247278135` through real quickstart seed flags.
A native pre-world probe confirms its first three draws. Input binding v2 keeps
the requested initial state separate from the actual post-startup native receipt.
The authored 16×16 map path uses LoadFromBuffer and RunNaturalStartup, bypassing
Map::Generate and the frontend; this is not procedural generation evidence.
The historical failed unseeded receipt remains post-startup data, not a known
initial seed. No seed search or selection by memory outcome is permitted.

Each observation immediately detaches the complete UI record once. Temporary
quote/draft state remains rooted only through the next real isolation assertion.
The staged runner uses explicit top-level accumulation boundaries without game,
RNG, timer or turn advancement. Cleanup precedes Finish and final native checks;
END and PASS are emitted only after those succeed. Full fields, stages and exact
native floats remain mandatory, and the 2 GB runtime limit is unchanged.
