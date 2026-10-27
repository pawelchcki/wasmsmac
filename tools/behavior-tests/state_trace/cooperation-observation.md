# Cooperative work observation v4

`game.terrain_observation.v4` preserves every v3 field and adds one explicit
per-unit `cooperative_work` envelope and an aggregate coverage flag. A missing
native `unit.get_terraforming_schema_version()` is unsupported, with a reason
and no fabricated cohort. Known native schema 2 plus the actual source helper
`terraforming.gls.js::cohort_state(game,unit,freshReadCache)` can return null for
an absent, stale or ineligible job. This supported null differs from missing
observation capability. The cache exists for one synchronous full-world read.

Raw native work, optional four-field `job` metadata, and own contribution remain
unchanged. Helper totals and sorted participants are separate observed values.
Validation binds each participant's owner, job, target, domain, activity and own
counter to its captured native unit. Genuine paused contributions count toward
the total. Every eligible same-job native member must be present, including
opponents; the current UI owner never filters observation. Legacy v2/v3 packets
remain readable without inventing cooperation fields.

The bounded native proof shares the declared seven-owner fixture with the core
cooperation suite: source rate five, fourteen working Formers plus one additional
peer, seven initial native units and seven cities. It captures four complete
128-tile worlds: partial cohorts, a real paused opponent, a real third peer
contribution, and a fresh read after authoritative terrain mutation invalidates
another owner's job. Every capture fences the full native graph, RNG and queues.
The completion marker follows cleanup and normal Finish. No original cooperation,
UI, graphics or timing agreement is claimed.

After the matching native schema-2 runtime is built and a worker slot is granted:

```sh
python3 tools/behavior-tests/state_trace/cooperative_capture.py \
  --runtime /path/to/immutable/GLSMAC.js --artifacts /tmp/cooperative-observation
```

The replay preserves requested seed, runtime/worker/fixture/source fingerprints,
full snapshots, native inventories and raw process status. Pure schema checks
are transport validation; source staging is not native execution. Native proof
remains pending until the matching runtime succeeds with its real footer and
exit zero. Old-runtime failure must not be promoted from structurally valid data.
