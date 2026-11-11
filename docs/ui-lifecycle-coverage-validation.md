# UI lifecycle coverage

This batch adds nine application regression scenarios across three existing
suites. The production game UI, minimap turn control, popup manager and popup
definitions own the transitions. `_ui_mocks` supplies display objects, command
recording, event sources and controlled timer ticks. No original-game
observations or passing parity totals are added.

| Suite | Additional scenarios | Observed behavior |
| --- | --- | --- |
| `game-modal-input` | 4 | Status/year changes invalidate pending confirmations; fresh dialogs remain usable; modal keys retain dialog ownership; controls and callbacks saved before UI replacement cannot decide a successor. |
| `popup-resize-regression` | 3 | Both visible and hidden dialogs recenter without new decisions or audio; repeated show during exit retains the first callback/timer; a completion callback can open a different dialog safely. |
| `popup-sound-regression` | 2 | Speech is acquired/released once per visit; duplicate shows do not restart it; replacement during entry stops the old animation and blocks its hidden controls. |

Assertions inspect active dialog identity, visible/removed window state,
displayed prompt/year text, geometry, recorded commands/results, root and resize
listener counts, timer ownership, and transition/speech play/stop calls. The
status/year cases explicitly deliver synthetic events in the game's event
protocol to production UI handlers. They do not advance an authoritative native
world or establish any player-state transition.

## Verification

The focused command is:

```sh
python3 tools/behavior-tests/fast.py \
  --runtime /path/to/GLSMAC.js \
  --suite game-modal-input \
  --suite popup-resize-regression \
  --suite popup-sound-regression \
  --jobs 1 --default-timeout 120 --report build/ui-lifecycle-focused.json
```

The adjacent `ui-interactions` suite is also included in local verification.
The path-filtered `coverage-ui-lifecycle.yml` PR workflow replays all three
changed suites against the reusable exact-head engine and uploads its report.
This includes the Stable popup suites, which ordinary Hot replay would omit.

The initial immutable local engine comes from `pawelchcki/wasmsmac` PR #53 CI
run `43015901038`, source `c0160cea41c091d659ffe0248c0d532f36bc8a01`:

- Loader SHA-256: `469a240495f2945052b4fdb6eacc7d72c27231ac68bbf8f323e3d9dcce18750b`.
- WASM SHA-256: `c75880a5ad8baf7a6e2f8194fde8679cb150f83a45a93b8ca18d56bc073b1f35`.

The runner mounts current host scripts without modifying that runtime. Local
Node 24.10.0 execution on 2026-11-11 passed all four selected suites serially:

| Suite | Scenarios | Assertions |
| --- | --- | --- |
| `game-modal-input` | 15 | 68 |
| `popup-resize-regression` | 9 | 45 |
| `popup-sound-regression` | 5 | 28 |
| `ui-interactions` (unchanged adjacent coverage) | 64 | 423 |
| Total | 93 | 564 |

Elapsed runner time was 54.98 seconds, one worker. The initial attempt stopped
before executing scenarios because the fresh worktree had no staged TypeScript
manifest. Copying the matching CI package into that worktree's ignored build
directory resolved setup; neither the package nor shared runtime was modified.
The successful report is retained as
`/tmp/wasmsmac-coverage-ui-focused-2.json` during this delivery. Static diff
checks and workflow YAML structure validation also passed. These local results
are supplementary to exact-final-head PR CI and review.

### Initial PR CI failure and configuration repair

PR #57's first focused workflow used `fast.py` directly and inherited its
30-second development fallback. The established regression CI dispatcher
`tools/behavior-tests/lanes.py` explicitly supplies `--default-timeout 120` in
`command()`; the new focused workflow had omitted that argument. In
[run 43023624947](https://github.com/pawelchcki/wasmsmac/actions/runs/43023624947),
`game-modal-input` reached the first new scenario before timing out. Both popup
suites passed. The partial run is retained as a failure, not a passing total.

The focused workflow now uses the same 120-second fallback as established CI.
This is a fallback, rather than a `--timeout` override: any catalog-declared
deadline still takes precedence. No test inputs, assertions, fixture behavior,
catalog selections or production code changed in this repair.

The Hot harness independently rejected the preparatory Stable-selection profile
because its inventory fingerprint includes every GSE regression source. Updating
those sources requires regenerating that fingerprint. Only `inventory_sha256`
was refreshed from `stable_selection.inventory()['sha256']`; coverage unions,
selections and `dependencies_reviewed: false` remain unchanged. The 39 selector
and lane checks pass after the refresh; the stale-profile failure log is retained.

The CI-equivalent local replay used the exact failed job's engine, Node 22.16.0,
two workers and the established 120-second fallback. All four suites passed with
the same ordered scenario names, 93 scenarios and 564 assertions; the script
snapshot hash also matched the earlier passing replay. Runner time was 43.50
seconds, with `game-modal-input` taking 39.53 seconds. The failed engine's WASM
SHA-256 is
`fc72c9ecfe33c74cbd3b6be2324904dc77dc27bc3262edb256f2752c05ea9dc7`.
The CI-equivalent report remains at
`/tmp/wasmsmac-coverage-ui-ci-equivalent-120.json`; final-head CI still applies.

### Hosted platform dependency recovery

At head `b2a3c467`, the focused UI job and all other applicable contexts passed,
but the platform job initially stalled in the existing asset suite. Its cancelled
attempt and partial artifacts remain retained. Three subsequent attempts failed
before compilation or tests: `apt` could not resolve
`azure.archive.ubuntu.com` while installing the unchanged EGL/GLES packages.
These infrastructure failures are not counted as passing platform execution.

The failed jobs used Ubuntu image `20261101.360.1` in `eastus2` and `westus`.
The successful main platform job (`130549694359`, `southcentralus`) and PR #54's
platform job (`130551515298`, `westus3`) used that same image and provisioner
`20261028.624`. This comparison does not establish a regional root cause, but
rules out an image-version difference among those observed jobs.

The image's
[pinned source configuration](https://github.com/actions/runner-images/blob/ubuntu24/20261101.360/images/ubuntu/scripts/build/configure-apt-sources.sh)
replaces the Ubuntu source URI with `mirror+file:/etc/apt/apt-mirrors.txt` and
prioritizes Azure before the canonical Ubuntu archives. The platform job now
replaces only that URI in `/etc/apt/sources.list.d/ubuntu.sources` with
`https://archive.ubuntu.com/ubuntu/` before updating package indexes. Distribution
suites, components, signing-key configuration, EGL/GLES packages and every test
command remain unchanged. It does not bypass package signature verification or
turn a failed test into a skip. The retained failed-attempt logs are recorded in
the delivery ledger; the new head still requires fresh platform execution and
all applicable CI/review gates.

## Limits

Explicit event delivery models child-modal consumption before root shortcuts;
it does not establish actual keyboard focus or rendered pointer routing. Timer
ticks exercise cancellation and completion ordering, not elapsed wall-clock
animation cadence. Sound assertions count production play/stop calls, not audio
waveforms, mixing or playback completion. These fixtures construct no native
world, so all-player simulation state is outside their scope. Existing original
observations, unsupported cases and other native-world coverage stay separate.
