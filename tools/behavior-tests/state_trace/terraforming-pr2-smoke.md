# Terraform controls bring-up

These commands are staged, not passing evidence. Run them from the assembled
PR2 checkout after its source and runtime identities are frozen and the heavy
resource slot is granted. Native runtime v1 is
`/tmp/wasmsmac-terraform-pr2-runtime-v1/GLSMAC.js`, built from `5fae2f90`;
its provenance file must accompany each result. The production GSE host must
include the height, automation, shared movement and controller checkpoints.
An older native runtime cannot establish the optional paid-work, terrain-epoch
and pending-action capabilities.

First register the existing staged script
`GLSMAC_data/tests/terraforming_controls_all.gls.js` under the exact catalog ID
`terraforming-controls-all` with domains `gameplay,ui,ux` and evidence
`glsmac-regression`. Final lane membership is an integration decision. Do not
rename an existing suite or substitute a mock native implementation.

```sh
python3 tools/behavior-tests/fast.py \
  --runtime /tmp/wasmsmac-terraform-pr2-runtime-v1/GLSMAC.js \
  --jobs 1 --timeout 120 \
  --suite terraforming-controls-all --suite terraforming-dialog \
  --suite former-controls --suite native-input-state \
  --report /tmp/terraform-pr2-ui-smoke.json

python3 tools/behavior-tests/state_trace/terraform_actions.py \
  --runtime /tmp/wasmsmac-terraform-pr2-runtime-v1/GLSMAC.js \
  --case land:farm --artifacts /tmp/terraform-pr2-action-smoke
```

The first command exercises mounted control handlers with real native effects;
it does not establish browser input or rendering. The second must emit the
ordered before/queued/acknowledged/after manifests, all seven owners, complete
native inventories and every tile. Its JSON must say `status: passed` and
`candidate_executed: true`, retain exact host/runtime/fixture identities, and
retain zero original passing cases. Missing chunks, stale API errors and no-op
acknowledgements are failures. Preserve their logs before any correction.

Once these pass, run the existing actual pointer lifecycle browser smoke in an
exclusive browser window. `WASM_APP_DIR` must identify a complete web shell
containing the pinned native runtime; `WASM_SCRIPTS_ROOT` selects the assembled
production host independently from this harness checkout.

```sh
env FONTCONFIG_FILE=/tmp/glsmac-fonts.conf \
  PLAYWRIGHT_BROWSERS_PATH=/var/home/pawel/.cache/ms-playwright \
  SMAC_ASSETS_DIR=/var/home/pawel/reimplementation/smac-wasm/smac-assets \
  WASM_APP_DIR=/path/to/pinned/full-web-shell \
  WASM_SCRIPTS_ROOT=/path/to/assembled-pr2-checkout \
  TERRAFORM_CONTROLS_ARTIFACTS_DIR=/tmp/terraform-pr2-pointer-smoke \
  node --test tools/wasm-tests/terraform-controls.test.mjs
```

That smoke has 29 distinct source menu rows, an actual non-base click, Escape
and Tab cancellation, and an actual owned-base pointer dispatch. It preserves
all-seven-owner/full-map state across pure controls. It does not count 29 rows
as 36 executed cases, prove height payment, or prove a complete autonomous plan.

After the smoke, execute all 36 native action captures with fresh workers:
19 land variants, seven sea variants and ten commands. Start with `sea:farm`,
`land:raise` and `command:road_to`; omit `--case` only after these first domain
and API checks pass. Commands exercise real work/movement followed by explicit
cancellation; link the separate completion suites rather than reporting this
bounded trace as map exhaustion. Height captures must include pure quote,
Cancel and draft choice, followed by actual confirmed payment and completion.

The wider browser matrix remains pending: all domain/action routes, source
SeaFormer production, height quote/payment and mesh/class-change refresh,
work/progress presentation and keyboard context. Mock handler coverage and
native capture cannot set `browser_verified`. Original effect/fee/animation,
audio and naval model composition gaps remain outside passing totals.


### Reproducible action trace inputs and snapshot lifetime

The all-action producer requests native initial RNG state
`1651011033:1377505029:3019448108:3247278135`, the existing Config example,
chosen before its first seeded replay. The worker passes the real
`--quickstart --quickstart-seed` flags. `Game::Start` applies that state before
fixture map creation; `Map::GetRandom` and gameplay use the same native RNG.
This fixture supplies an authored 16×16 flat-arid map with `LoadFromBuffer` and
runs `RunNaturalStartup`; it never calls `Map::Generate` or mounts the frontend.
Thus quickstart's generated-map/environment overrides and frontend branches are
outside this declared path. This is not proof of procedural map generation.

The input binding v2 records both the requested initial state and the actual
post-startup, before-action native RNG receipt. They are separate fields; the
latter must equal the `before` native inventory. Legacy input binding v1 logs
remain readable with their original unseeded scope. In particular, the failing
v6 receipt `826145919:3571325180:111502455:207424645` is post-startup, not a known
initial seed. Its full original map and output remain preserved outside pass
counts.

The UI reader lends references only until `observer.read` immediately deep
clones the complete UI record. Each resulting checkpoint owns detached values.
The emitter serializes those already-detached fields directly instead of
cloning them again. Actual Cancel/confirm transitions assert that earlier UI
checkpoints retain their prior stage; after work, the initial native Float
movement bits must still match the captured pre-command value. No native field,
checkpoint, participant, map tile, or read-purity assertion is removed.

Memory savings and strict shutdown require a fixed-input before/after native
measurement. Source inspection and pure transport tests alone are not a native
memory pass, and the existing 2 GB runtime limit is unchanged.
