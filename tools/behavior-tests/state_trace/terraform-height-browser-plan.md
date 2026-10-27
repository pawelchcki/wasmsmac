# Land height browser proof

Status: the second actual browser attempt strictly passed the bounded land Raise
case below. The first failed observation remains preserved. **One candidate
browser case, zero original-agreement cases.**

The isolated case starts from PR35 `7ee4e80b1c1723f60c3349d2d0456aee70f54873`,
native tree `115032ffc7f53ff7f0c3a9f997da12674e25e643`, default source tree
`25ef18d3222f553507291d412330262169b2e418`. It does not change production,
the passing Terraform controls fixture, PR35/PR36 branches, catalogs, lanes or
workflow files.

The intended runtime is immutable local v6:

- JS `e71036c9365a3ac87bf818e7eb49fb2344077a15aa6836371a436572cedf7f82`.
- WASM `b2c7fa273042f2407335169eb4fca51f131f1f30656301d7b7573a201b28f5b7`.
- Initial requested seed `1651011033:1377505029:3019448108:3247278135` enters
  the existing `Game.Start` quickstart seed path. No browser live-RNG getter is
  claimed, and no favorable seed selection is permitted.

## Inputs and observation

`terraform-height-browser.test.mjs` reuses the source-backed seven-owner world
from `terraform-controls-world.gls.js`: seven cities, seven Scouts, one actual
local land Former, 16×16 imported map with 128 real tiles. Opening funding is
the actual source starting reserve plus the real faction bonus. A test-only
asset override changes exactly the twenty installed TERRAIN shared turns fields (index 4) to
one; the parser uses that one field for both land and sea metadata. Names and
prerequisites stay unchanged. Original/overridden file hashes, byte count, actual loader reads and both
manifest identities are separate report fields. This is not a stock-duration
claim.

`fixtures/terraform-height-main.gls.js` supplies only declared initial selection,
read observation and eventual test exit. All work, quote selection, cancellation
and payment use actual SDL keyboard/mouse delivery to mounted controls. The
production default source is loaded without a root-handler overlay.

The actual height popup uses ordinary Buttons and a Window. Modified query P
is not consumed by those Buttons; the Window's existing handler always returns
true. The fixture appends a handler returning the same true result, queues only
scalar owner/actor/turn/session/generation metadata and keeps its native frame
reference outside that metadata. An owned root timer validates the still-current
frame/session, then reads after dispatch returns. It never calls a work or popup
callback. Full quote objects are captured only by the six requested snapshots,
not copied by the lightweight UI-state poll.

The driver uses the proven CDP Fetch main/worker classifier, print-capture
identity barrier, UTF16 append cursor and sealed raw-log collector unchanged.
Every click requires actual semantic/native geometry, intended native hover,
left-down/up ingress and matching completed mouseup dispatch. Query keys require
raw SDL ingress linked to completed normalized dispatch and exactly one fresh
query response. The close boundary requires settled popup state **and** a native
node.hide after the cancellation pointer ingress. No fixed sleeps authorize
state assertions. The entire browser test retains the existing 180-second cap.

## One case and its gates

Six full checkpoints retain all seven players, eight units, seven cities and
every field of all 128 tiles:

1. `before-height`: actual selected land Former and normal opening funding.
2. `raise-quote`: pointer MENU → Terraform → Raise. The live quote is supported,
   source-rendered fee/reserves agree with it, and actual choice zero is Cancel.
   The entire native world equals checkpoint 1.
3. `raise-cancel`: activate the actual OK while Cancel is the default choice;
   wait for its native hide and settled callback. The entire native world still
   equals checkpoint 1.
4. `raise-reopened`: use the retained normal root menu and real Raise row again.
   Its live authoritative quote and complete native world remain unchanged.
5. `raise-payment-draft`: pointer-select the actual source-rendered Expend row.
   Choice one is only a draft; the entire native world remains unchanged.
6. `raise-paid-completion`: actual OK, scalar authoritative event receipt and
   settled pending/lock state. Fee is debited once from the real payer; opponents,
   all research and all cities retain their actual state. The actual quote's
   affected canonical elevations/classes and mutation epochs are checked. The
   worker spends its real movement budget, completes work, retains its native
   definition and logical tile, and every other unit remains intact.

The paid checkpoint also runs a complete allowed-diff audit over the entire
native world. It starts with the full before-record and changes only payer
credits/revision, the actor's real movement/order flags and derived exhausted
movement eligibility, quoted canonical centers, and native shared geometry in
the actual patch/adjacent footprint. `TerrainMutation.cpp` preserves neighbor
canonical centers while refreshing shared corners and increments every recorded
affected tile epoch; `Tile::SetCanonicalElevation` clears imported source data
only for edited patch tiles. All unknown fields, payer identity/other energy
fields, actor health/morale/combat/work metadata, all resources in this empty
arid fixture and terrain outside that footprint must remain exact. Numeric
shared-corner values remain observed candidate geometry rather than an invented
original mesh oracle.

`Event.cpp` retains only scalar receipt fields. The driver binds actual
`name/event_id/caller/unit_id/action/confirmed_height` acceptance to the stored
live UI quote and resulting native fee/effect. The nested submitted quote is
not echoed by `event_result`; that payload-echo capability is explicitly
unsupported, never reconstructed from the UI observation.

Five fixed-viewport frames are retained before height work, at the quote,
after cancellation, at the payment draft and after completion. No camera input
is sent between them. Frames are candidate evidence, not original pixel matches
or typed mesh/actor-Z telemetry.

Success additionally requires final Q delivery, the native application's normal
zero-code exit state and actual `#status` text `GLSMAC exited (0).` (recorded as
`native_raw_exit_code: 0`), Node process zero, no late browser/barrier/native errors,
actual main continuation ACK, at least one actual pthread continuation ACK,
first real callback out/err identity and complete sealed raw chunks. Raw GSE
snapshot text remains available because Node's JSON parser folds integral
native Float numbers; movement additionally carries actual native Float32 bits.
The first callback must also prove `runtime_callMain_present === true`, and
every recorded worker request must have a successful continuation ACK.
Final verification scans the complete sealed raw suffix for native errors,
requires `sealed.failure === null` and exact raw/chunk equality. Any final
verification failure marks the artifact failed/partial with unknown-tail scope.
Node comparisons preserve parsed values, including signed zero where the JSON
token provides it. Native integral Float versus Int typing and exact numeric
wire spelling remain in the retained raw GSE JSON; Node does not claim to
distinguish those two native types after parsing.

## Known source lead and remaining scope

An initial pending-request concern was disproved by source inspection:
`menu.close(child)` invokes the shared on-close handlers for child menus too.
The height controller's `root.clear_active()` therefore clears that pending
request while closing the Terraform child. The case still checks the ordinary
cancel-and-reopen path. No production defect or fix is claimed.

Both height and fee are explicitly named functional approximations:
`application.band-slope-height.v1` and `application.band-fee.v1`. This case adds
no original agreement for contour, climate, dome/victim handling or fees. Coastal
and sea-domain transitions, Sea Former production, typed mesh vertices,
resident render-Z/facing, work/tool frames, animation parity, video, sound/music
and original graphics remain outside passing totals. A coastal/sea case needs a
separate plan and grant after this bounded land result.

Pure protocol tests are `terraform-height-observation.test.mjs`; their synthetic
packets validate harness rejection paths only and add zero native/browser passes.

## Preserved first attempt

Frozen height head `51563751fbfb276c83a1094a116299d85f225900` ran against the
pinned v6 engine. The single browser attempt stopped with Node exit 1 after
24.946 seconds: `#clone(preview.height_presentation)` received the initial Null
in the new observer. `src/gse/builtins/Common.cpp:91` allows clone only for
Object/Array. The bounded test-only correction retains actual Null directly and
clones only a present Object. No product change or outcome relaxation follows.

Artifacts remain at `/tmp/terraform-land-height-v6-first`: exact preflight with
all twenty row ID/name/field/old/new overrides, report, original fixture source,
failed frame, driver log and raw chunks. The actual rules hashes are original
`bb01e3ac23793da0a46713f4851d65e63b599c24aef8300ffe45e7e57b332c42`
and rate-one input
`7abf62aa4f4f562aaa86c785b67b7af2320e122cbda7901287ee3ed0ab4c5bd0`.
Raise source row 16 (`Raise Land`, line 127) changes shared turn field 4 from 12
to 1 for both domain variants; its `EnvEcon` prerequisite and other fields remain unchanged.

The real main continuation and all eight pthread continuations acknowledged;
the first actual callback proved out/err capture and callMain presence. Raw and
joined chunks are exactly 6,783,101 bytes, SHA256
`e8e6450375feaf09d17c00d2d624ece0ac6b3e7978f627d3a601a14903a1bb51`.
They are sealed but partial because the application failed. Native exit code
is unknown. Complete snapshots: 0; height actions: 0; passing cases: 0. Browser,
server and driver were reaped and the heavy lease released. The Null guard
requires a separately authorized actual verification; no retry is automatic.

The original first-attempt preflight called field 4 `land_turns`. That label
was incorrect: `terraforming_rules.gls.js` parses row[4] once and passes the
same turns value to both land and sea variants. The original preflight remains
untouched; its adjacent label-clarification sidecar records this correction.
Neither the executed bytes nor any observed outcome changes.

## Verified second attempt

Executed source `bc8a3e4a113456cce2ada80e7a56d0872911d8a0` retains the same
native/default trees, v6 engine, rules bytes and 180-second budget. The actual
case passed in 84.769 seconds; the outer Node process returned 0. The tool's
actual session 40314 completion, chunk `0ae251`, records that raw return code
independently of TAP. The application also exposed body state `exited` and
actual `#status` text `GLSMAC exited (0).`.

Artifacts are `/tmp/terraform-land-height-v6-second`; the immutable repository
summary is `terraform-height-browser-v6-proof.json`. All six raw snapshots have
seven players, eight units, seven bases and 128 full tiles. The five prepayment
worlds are identical under recursive exact JSON type/value/Float64-bit comparison.
All 96 unit movement/health Float tokens across the snapshots round-trip exactly
to Float32; the actor's movement bits are `1065353216` before payment and `0`
after completion. `terraform_height_browser_audit.py --artifacts PATH` reproduces
the read-only typed audit without launching an engine.

The actual quote names the two approximation policies, charges 4 of the real
10 credits and raises target canonical elevation 240 → 1500 while retaining land
domain. Nine quoted canonical tiles and the 25-tile shared-geometry footprint
account for the complete native difference. The read-only audit classified all
229 changed native fields; no other field changed. Payer revision advances 1 → 2
and its balance 10 → 6. Quote, Cancel, ordinary reopen and Expend draft preserve
the entire observed world. The accepted receipt contains the actual scalar
`unit_id/action/confirmed_height` fields and opaque String event ID, not a
fabricated nested quote echo.

The real main continuation and all eight worker continuations acknowledged.
The first actual callback proved configured out/err and callMain presence.
All raw chunks join exactly to 14,465,994 bytes, SHA256
`7877baed15b88c2700f3042fe5c31f64c6ee66517dcef04541c1ced832bad473`.
The sealed failure is Null, partial is false and late errors are empty.
Delivery independently audited the raw typed worlds, bits, inputs, frames,
receipt, runtime barrier and sealed bytes. Browser, server and driver are reaped.

Five frames are retained with an unchanged viewport, **not a proved fixed camera**.
Completion auto-selects Scout 1 instead of worker 8, and the final frame shows
changed focus/position. Native actor map coordinates stay fixed; resident render-Z,
camera pose, facing and numeric mesh/corner fidelity are not established. No
pixel comparison or unchanged-camera assertion is inferred from the screenshots.

## Next source-only coastal/sea plan

No additional live case is authorized by this document. The next coherent scope
needs a separately reviewed fixture and resource grant:

1. Prepare a declared coastal world with all seven real players and registered
   source recipes. A Sea Former must come through its actual source-composed
   Foil/terraforming-capability recipe and normal production pathway in a
   separate acceptance step. Do not replace production with a fake availability
   answer or treat a disabled original template as enabled. Any bounded input
   for production stock/rate needs its own explicit source hash and scope.
2. On a genuine sea worker's shelf square away from protected cities, preserve
   quote/Cancel/draft purity, then confirm the live approximate Raise plan and
   fee. Capture every affected neighbor, land/sea class and epoch, all players,
   the unit definition and actual naval-recovery state. Its renderer remains the
   real currently supported resource; no invented Sea Former art is introduced.
3. Observe legal reversal through the same initiating worker's actual recovery
   context after a real turn boundary. Retain all seven players' genuine income,
   research and movement differences at that boundary. Separately reject illegal
   docked-port/foreign-resident stranding cases without charging or mutating work.
   Technology bypass must not waive those domain/treasury/geometry restrictions.
4. Resolve camera/resident/mesh observation capability before any numeric visual
   claim. Existing native refresh logs and screenshots are observations only;
   a new read-only renderer getter would need a separate proven need and C++
   lease. Coast/climate/Pressure Dome/victim algorithms, original graphics,
   animations and audio stay outside passing totals until independently observed.
