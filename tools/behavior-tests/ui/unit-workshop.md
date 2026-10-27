# Existing-design Workshop application contract

The base production pane's WORKSHOP button opens a modal browser of its currently
available unit production choices. Facilities and unsupported project kinds are
excluded. It starts on the production draft's unit when possible, otherwise the
first available unit. Arrow keys preview a bounded adjacent choice; pointer
SELECT or Enter transfers its stable production ID to the existing draft. The
normal production OK, switch-loss preview, availability and ownership validation
still submit the eventual production event. Browsing and SELECT issue no game
event. Escape or CANCEL discards the Workshop selection and preserves the draft.

The browser displays each live production descriptor's name and mineral price.
Existing installed rule definitions supply combat, reactor, movement and worker
module details. `default/units/render.gls.js` is the same render-policy helper
used by the real unit definitions: the guarded stock land Former uses the
independently bound `VT.cvr` chassis component; other designs retain the existing
portrait fallback. No new model, original assembly, tool binding, transform,
facing or animation semantics are inferred. This is an application preview of
the existing renderer, not a passing original pixel comparison.

The Workshop has its own modal Window, an explicit `game.unit_workshop` dialog
presentation identity, retained selected list ID, mounted preview surfaces/text
and ordinary keyboard events. Closing/removing the base, refreshing its data or
discarding its production pane removes the Workshop. Session tokens fence old
callbacks. Selection also rechecks the base identity, ownership, local player,
turn and currently available unit/production ID before transferring the draft.

`GLSMAC_data/tests/unit_workshop.gls.js` executes the actual production pane,
WORKSHOP button, Workshop controller and render helper through the existing
display boundary. It covers costs and source edits, guarded chassis identity,
naval/authored fallbacks, keyboard/cancel, draft-only transfer, normal production
validation, modal submission fencing, empty inventory and stale lifecycle/state.
The display boundary does not claim native hit testing, focus delivery, actual
resource loading, pixels, sound or animation cadence. Existing native production
and installed stock-Former graphics checks cover their separately stated scopes.

Custom design authoring, component customization, renaming, save/obsolete/upgrade
flows, original Workshop layout and controls, assembled previews, rotation,
movement facing, work animations and audio remain unsupported. Original Workshop
agreement adds zero cases; no original Workshop observation is currently supplied
to this implementation. Full visual and game fidelity remain incomplete.
