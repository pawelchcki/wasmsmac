# Capacity shutdown observation

The PR35 hot regression at `9f97267194ea898452a4da59865dd5b5cfb65e3d`
failed `terraforming-cooperation-capacity` at its unchanged 120-second deadline.
All five initial stage BEGIN/END pairs were present, including the second
production plan. Those END markers occur **inside** accumulation callbacks;
they do not prove the following commit, collection or normal Finish returned.
No PASS, summary or native success footer was present. This remains a genuine
failed CI gate.

A single approved 240-second **observational** run retained the original full
GSE snapshot and exact cloud engine. It changed no test statements, native code,
2 GiB WASM limit, GC cadence, field coverage or assertions. A parent process
sampled `/proc` once per second and retained unchanged worker stdout. It did not
load a Node preloader or access Module/WASM properties. WASM heap-capacity
observation is unsupported.

| Binding | SHA-256 |
| --- | --- |
| Full GSE snapshot (exact CI match) | `5a4528addb06c918a77d291d513e1096c7b780fd90bc4644c69f8232bffcbe6f` |
| Selected probe | `70056250da9314593e04fa2be65536eea60b76284b28bf1d14a8f59e96732b81` |
| Unchanged worker | `674a4a6f5fd4e5e176013b53b442037229aa02aef4c9c1bde5167c9147a76fc1` |
| Runtime JS | `acbc76fbc94b2306a01bce0fa2acf9c30f43f43addea915802f8d07142e5e3ec` |
| Runtime WASM | `83767fa8acce5c776be47f6298f0e24c5828f2e290722a4d341001f4ecb09a24` |

Native source tree is `115032ffc7f53ff7f0c3a9f997da12674e25e643`;
production default source tree is `25ef18d3222f553507291d412330262169b2e418`.
Historical CI full environment and host CPU/load were not captured. The
observation inherited its current environment (`NODE_OPTIONS` and
`WASM_HEADLESS_APP_DIR` absent), used a different ephemeral request prefix and
combined stdout/stderr acquisition. Entire launch/environment byte identity is
not claimed. CI ran two regression workers; this observation was exclusive.
Concurrency is a possible resource difference, not a demonstrated cause.

The unchanged observation completed normally in **80.574 seconds**, one scenario
and 11 assertions, raw exit zero, native success footer at 80.078 seconds. It
exited before the proposed 120-second checkpoint. The 240-second allowance was
not needed. This local observation is **not** a repaired or passing CI result.

The actual 4,096 patches / 4,096 full reads / 4,096 guard tuples produced the
same footprint JSON bytes as failed CI. Identity is 261,177 ASCII/UTF-8 bytes,
SHA-256 `ec74d2103109b1430b3d5ebb85710f95824930cd850454b5fa6fb9acbecd3b7a`.
The exact native 512 KiB readback, one-byte-over atomic rejection, unwrapped-plan
identity equality and complete native purity checks all completed. No fallback
or expected-state substitution was used.

| Observed boundary | Elapsed |
| --- | --- |
| Counted plan BEGIN / END | 3.542 / 29.707 s |
| Native byte-boundary BEGIN / END | 43.879 / 44.124 s |
| Second production plan BEGIN / END | 44.282 / 67.807 s |
| First after-Finish callback BEGIN | 79.302 s |
| Summary END | 79.511 s |
| Native success footer | 80.078 s |

The sample span consumed approximately 81.08 process CPU seconds. Sampled
process RSS peaked at 2,173,336 KiB; RSS includes host/runtime memory and is not
WASM heap capacity. It is not summed across threads. Markers are inside native
accumulations and timestamps include stdout transport. Inter-marker costs combine
execution, commit, collection and dispatch; these are not isolated GC timings.
Samples are non-atomic, and unavailable final `/proc` fields are retained as such.
No permanent stall, collector algorithm defect or production leak was proven.

Raw logs, `/proc` samples, source/runtime bindings, exact footprint comparison and
timing analysis are retained in `/tmp/terraform-pr35-capacity-observational240`.
The earlier CI timeout remains retained separately. Any resource scheduling or
producer change requires its own exact-head CI evidence; blindly enlarging the
global deadline or weakening shutdown checks is not justified by this result.
