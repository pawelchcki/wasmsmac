# Land height browser proof

Status: source prepared; **no native or browser execution claimed**.

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
asset override changes exactly the twenty installed TERRAIN duration fields to
one. Original/overridden file hashes, byte count, actual loader reads and both
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

Five fixed-viewport frames are retained before height work, at the quote,
after cancellation, at the payment draft and after completion. No camera input
is sent between them. Frames are candidate evidence, not original pixel matches
or typed mesh/actor-Z telemetry.

Success additionally requires final Q delivery, the native application's normal
zero-code exit state, Node process zero, no late browser/barrier/native errors,
actual main continuation ACK, at least one actual pthread continuation ACK,
first real callback out/err identity and complete sealed raw chunks. Raw GSE
snapshot text remains available because Node's JSON parser folds integral
native Float numbers; movement additionally carries actual native Float32 bits.

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
