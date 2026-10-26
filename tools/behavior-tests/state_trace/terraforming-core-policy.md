# Terraforming core implementation ledger

The exhaustive request covers the 19 playable land declarations, seven sea
variants, and ten composite/automation orders in the installed source. Monolith
is editor-only (`Disable` on both surfaces). The shared action IDs come from
`default/game/terraforming_actions.gls.js`.

This document describes application infrastructure, not additional original-game
observations. Source names, prerequisites, work declarations and component facts
are inputs; they do not establish work multipliers, fees or terrain effects.
Original expected observations remain immutable. The master completion ledger is
maintained separately and must retain pending actions until their actual command,
work, terrain and traversal paths have been exercised.

## Explicit technology policy

`game.get_settings().global.rules.get_terraforming_policy()` returns version 1
and `ignore_technologies`. Normal play defaults to `true`, as requested by the
user. `set_terraforming_ignore_technologies(false)` selects real respect-tech
mode. The native Rules codec, copies and settings transfer retain the policy.
Legacy candidate comparison fixtures explicitly request respect-tech mode; this
is not a claim that their availability observations describe the new default.
`Disable` terrain rows and editor-only Monolith remain disabled in either mode.
No policy grants technologies or modifies any player's research ownership.

## Worker and sea access

The native immutable `Def.can_terraform` capability is derived from installed
Terraforming weapon mode 9, rather than a translated unit name or the broad
civilian category. It has a versioned definition-wire extension. Colony modules,
conventional weapons and legacy psi definitions do not implicitly become workers.

A separate `SeaFormers` application composition uses the installed Foil chassis,
Terraforming module, basic armor and fission reactor, with the existing component
cost calculator. It does not enable or reinterpret the disabled predefined
`*Sea Formers` template, append to the three-unit starting inventory, or claim
original recipe availability. The temporary production choice is available in
normal technology-waiver mode. Unverified naval artwork keeps the previous
portrait fallback.

Application naval-worker production uses a water city's own tile or the first
friendly unlocked adjacent water tile in W, NW, N, NE, E, SE, S, SW order. Inland
or blocked launches reject without consuming project credit. Production still
charges the actual mineral price and preserves the existing receipt, population,
worker-link, allocation-ID, random-state and lifecycle rollback guarantees.
This launch order is application policy, not an original-game observation.

## Detached terrain observations

`game.get_tm().get_terrain_state(x,y)` returns version 1, exact native coordinates,
world dimensions, actual neighbor pointers as detached coordinates, center and
four corner elevations, land/water classification, moisture, rockiness, bonus,
raw and named feature/improvement flags, and retained imported provenance.
Unavailable imported values are `null`. Elevations and imported centers are
engine units; the original map's raw height byte is not retained by this API.

The natural-startup test fixture's `audit_snapshot` additionally records every
player's native serialization, all units and bases, terrain, technology ownership
and definitions, research, rules policy, random state and allocation identities.
`audit_inspect` records actual pending native queues. These are read-only audit
seams, not seeded expected results.

## Atomic terrain changes

`apply_terrain(patches, worker_ids)` validates a bounded complete batch before
changing any field. Patches identify coordinates and optional complete named
feature/improvement dictionaries, moisture, rockiness and four engine-height
corners. Duplicate tiles, conflicting shared vertices, invalid fields, out-of-range
values and locked affected tiles reject atomically. Actual shared vertices refresh
all affected centers/classes and invalidate imported provenance only when their
corners change. Existing terrain rendering regenerates neighboring layers and
repositions resident units and bases from the refreshed tile coordinates.

A declared conservative application safeguard rejects class changes that alter a
city's land/sea ground or strand unrelated units. Explicit live capable initiating
workers may finish on a changed class; the command layer must retain ordinary
compatible retreat and reverse-height controls. No drowning, conversion or
teleport behavior is inferred. Native rollback validates the current grid's
lifetime, every affected tile and any new occupants before restoring any field.
It restores shared corners and imported centers/classes together. Changed world
identity, stale terrain, locks and incompatible occupants reject the entire undo.

These engine operations do not define the original raise/lower amount, neighbor
cascade, fee, aquifer flow or improvement replacement policy. Those action-level
outcomes need their own recorded contracts or explicitly declared application
fallbacks and meaningful end-to-end tests.

## Treasury prerequisite

`player.get_energy_state()` exposes native credits and last income turn.
`change_energy(delta, expected_credits, turn_id)` and
`credit_energy_income(amount, turn_id)` require authoritative write scope, a live
player, current turn, affordable bounded arithmetic and current balance. Income
is credited at most once per turn. Receipt undo is fenced by native player
lifetime, turn, transaction revision and expected ledger state. Copies and the
versioned Player wire retain balances; exact legacy records remain unfunded zero.
No opening grant, infinite funds or free height work is implied.

Normal-play income will reuse the existing actual base energy allocation's
economy share once per completed turn as declared application policy. Original
opening treasury, income timing and height fee formulas remain unsupported until
recorded separately. The technology waiver never waives fees.

## First foundation checkpoint: verified, incomplete action coverage

The first native runtime is bound to source `ffa9d296` (C++ tree
`ea493cd3c36650d14c12246596da5c22cb0d3201`), FastDebug/Emscripten 4.0.22.
Its JS SHA256 is
`c062e77ab4bb735e8184ea1588b51947d8740e5b7851a13e0a3546b955d5e1de`;
WASM SHA256 is
`7cbedfef7c7a73c400bc922af02e0d91fa7849e8fb29e01f10ce7781302252c5`.
Current host scripts override embedded scripts in the strict isolated workers.

Focused native checks passed 68 scenarios / 213 assertions across terrain,
source-component and land/naval production suites. The terrain suite includes
all-seven-owner completed-turn income from declared resource inputs, pure
preflight, unknown raw flag preservation, an actual capable worker's controlled
land/water transition, ordinary retreat validation, reverse edit and LIFO undo.
These synthetic engine edits are application invariants. They are not original
height-operation, fee or animation observations.

The exact main `048596fe` CI engine (`40396556071`, artifact `12688085153`)
rejects the new native naval recipe and lacks the full terrain observer. A
separate actual mounted-control probe records visible Raise and Lower rows
submitting zero commands while preserving its complete native fixture graph.
That control baseline contains two owners, three units and one base; it is not
seven-owner original agreement. Preliminary reports with invalid test syntax are
retained separately and are not valid feature evidence.

The existing four work effects remain the only action completion implementation
at this checkpoint. The full parser inventory, worker metadata and native edit
API do not count the other actions, sea work variants, height commands or ten
automation/composite orders as implemented. Original height effects, duration,
fees, refunds, cascades, victim handling and energy timing remain unaccepted or
unsupported. Subsequent batches must complete the full requested matrix.

The same immutable runtime also passed 14 compatibility suites: 203 scenarios /
880 assertions, including existing Former controls/work/first ticks/movement,
Rules and unit production codecs, research, turn playability, punctuation input
and exact Float transport. An independent Python raw-bits audit confirmed all
eight numeric samples, including `1/3` and signed zero, using actual native
execution. The strict JSON value equals the exported native binary32 value;
reconstructing merely the same rounded binary32 from a shorter JSON decimal is
not accepted. These checks add no original terraforming agreement totals.
