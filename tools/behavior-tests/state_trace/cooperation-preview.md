# Cooperative work preview

Source checkpoint only; the mounted native suite has not yet run on a frozen
runtime. This adds no original-game agreement or browser-pixel claims.

The selected unit's native contribution remains unchanged. A current multiworker
cohort renders its actual pure `terraforming.cohort_state` total and requirement,
with the selected worker's own contribution on the same existing progress line.
Solo, paid-height and legacy native work keep their existing native progress.
Stale/ineligible work has no fabricated cohort total.

`terraforming_progress.signature` reads ordered native same-tile unit IDs,
owners, health, domains, orders and detached work state, plus the actual base ID,
turn and a versioned process-local revision. It performs no terrain search.
Only selection/show or a changed signature computes the pure cohort helper with
a fresh per-call cache. No helper terrain cache survives that call. Existing
control availability polling is separate and may still perform work eligibility
queries; this patch does not claim the entire old HUD poll is search-free.

`terraforming_view_revision_v1` is an actual Game custom-global Int, initialized
lazily on first change and excluded from Game/world serialization. Work tick,
cancel, authoritative undo, inline invalidation and improvement-owner apply/undo
advance it without calling view listeners. It never appears in peer events,
jobs, quotes, payments or native gameplay snapshots. A changed revision can only
cause a new read; it cannot authorize work or make stale work eligible.

`terraforming_cooperation_preview.gls.js` mounts the production object panel with
the declared native seven-owner source fixture and a display/timer boundary.
It checks native partial/peer/paused contributions, true completion and undo,
selection isolation, fresh terrain reads, ownership invalidation and unchanged
poll read counts. Every explicit poll compares the full native audit snapshot
and entity/queue inventory. A direct view-revision update also must leave the
full native snapshot unchanged. Cleanup removes the panel and its owned timers.
The fixture requires the real `uncomplete_turn` setup correction because natural
startup intentionally marks offline computer turns complete.
