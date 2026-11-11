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
  --jobs 1 --report build/ui-lifecycle-focused.json
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

## Limits

Explicit event delivery models child-modal consumption before root shortcuts;
it does not establish actual keyboard focus or rendered pointer routing. Timer
ticks exercise cancellation and completion ordering, not elapsed wall-clock
animation cadence. Sound assertions count production play/stop calls, not audio
waveforms, mixing or playback completion. These fixtures construct no native
world, so all-player simulation state is outside their scope. Existing original
observations, unsupported cases and other native-world coverage stay separate.
