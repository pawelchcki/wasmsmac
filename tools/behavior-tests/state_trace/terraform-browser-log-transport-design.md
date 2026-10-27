# Bounded browser logger measurement and proposed harness changes

The original-root Terraform smoke on host `a457444e` timed out at the existing
180000 ms deadline after an accepted owned-base plan. Its final native graph,
pointer-dispatch completion and exit were not observed. It remains failed.
There is no established product click or shutdown defect from that run.

The NO-WASM Chromium replay uses the actual 11551539-byte captured input
(SHA256 `24fa026db81f4d4062af5b8f0bd9f11fc9cfd9f653181d619e4955fcfa95ad99`),
split into 883 LF-delimited messages. That split is an explicit replay model;
the failed game run did not measure its callback counts or logger timings.
Both original logger statements are retained, with clock reads around them:

```js
logElement.textContent += `${message}\n`;
logElement.scrollTop = logElement.scrollHeight;
```

The actual shell HTML/CSS is used with script tags removed, normal running
setup hidden, and log details separately closed/open. No Module, WASM resource,
network request or game input occurred. Node exited 0. Both 45-second scopes
stopped at their declared bounds, so neither claims a full 883-message replay.

| Scope | Completed messages | Exact retained prefix | Append time | Layout/scroll time | Largest callback |
| --- | ---: | ---: | ---: | ---: | ---: |
| Closed | 805/883 | 8561370 bytes | 0.2835 s | 44.7368 s | 2.2956 s |
| Open | 800/883 | 8559273 bytes | 0.2385 s | 36.5101 s | 0.9397 s |

The measured statement sums exclude per-row host reporting and the pre-read
of log length. Replay wall times include those costs and other browser work.
The results demonstrate expensive forced layout under this captured input;
they do not attribute every second of the failed game run to this function.
The adjacent JSON binds actual source, browser and prefix hashes. Full raw
inputs and per-call records remain in `/tmp/terraform-log-dom-benchmark`.

## Approved diagnostic print-hook source; runtime proof pending

Keep production web/default/native bytes unchanged. Pause only the main-frame
`GLSMAC.js` request through Playwright's existing routing boundary. At that
boundary, assert the existing bootstrap-created `Module.print`/`printErr`
configuration functions are present. Install harness callbacks before allowing
the unmodified runtime to execute. The pinned runtime captures those existing
configuration hooks at lines 11078–11079.

The harness callback executes the identical original append statement into
the same `#log`, retaining every message, newline, error and field. It omits
only the synchronous autoscroll statement. Bootstrap's own direct status/error
logger remains unchanged. Record exact hook source/hash, installation/runtime
ordering, callback sequence/counts, and initial/final DOM lengths. No alternate
buffer, truncation, trace cut, extra input or deadline increase is proposed.
Debug-log autoscroll becomes explicitly unsupported under this instrumentation;
native game windows and rendered canvas remain the subject of the proof.

The manager approved this source design. Before another candidate run, replay all 883 messages with exact full UTF-8
hash retention in NO-WASM Chromium for both detail states. Pure tests must
reject missing/repeated/late installation and preserve stdout/stderr order.
The next candidate browser requires manager approval and a fresh reviewed host.

## Approved collector finalization source; candidate proof pending

The failed run's `application.log` has 11551500 bytes. The continuously saved
JSONL chunks contain 11551539 bytes: an already pending read appended 39 bytes
after cleanup metadata was written, before browser close. The smaller file is
an exact prefix, not an equal artifact. Preserve both hashes and the separate
`application-reassembled.log`; do not relabel this partial failure a pass.

Add an explicit closing state to the cursor. Closing immediately rejects new
body/poll reads, but allows already accepted reads to settle and persist their
chunks. Queue one bounded final read internally, capture passive DOM receipts
and failure frame, then close the browser to settle any pending evaluations.
Await the cursor queue after browser closure. Only then freeze text, chunk
counts and read stats and write the final raw log/report once. The cursor must
reject every subsequent read and perform no append after freezing.

If a final evaluation fails or application exit is unproved, keep the failure
and unknown-unreceived-tail metadata. All received chunks must nevertheless
equal the frozen raw artifact exactly. A delayed-response pure regression
should reproduce the old 39-byte race, then prove final chunk equality, stable
metadata, rejected post-close reads and artifact I/O failure propagation.
No native collector, game timing, source fields or memory limit changes belong
to this harness correction.

Source implementation adds an explicit open/closing/sealing/sealed cursor.
An already accepted read remains eligible to append during closing; subsequent
body reads reject. After passive receipts/frame and browser closure, sealing
awaits the serialized queue and freezes the final text and read records.
Only then are joined chunks, raw text, hashes and report written. A close
failure stays an unsealed prefix with unknown tail; a timed-out final read
stays failed even if its response later arrives. Pure tests reproduce a
39-byte delayed response, cancelled final evaluation and immutable post-seal
artifact equality. The prior failed artifacts remain distinct and unchanged.

The separate `terraform-log-hook-replay.mjs` constructs an explicitly declared
configuration model from the actual source function and only the two capture
assignments. It does not load the runtime or instantiate WASM. It exercises
both output lanes in a declared alternating replay, since original channel
boundaries were not recorded. Actual runtime binding and first-callback proof
remain requirements of the next candidate browser.
