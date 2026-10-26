# Bounded installed CVR component previews

The texture loader recognizes `.cvr` resources and produces a transparent
100×75 preview from a single geometry component. The geometry and physical
palette come from the installed resource, through an independent implementation
of the [public tagged Caviar format description](https://alphacentauri2.info/wiki/Caviar.html).
No original executable, renderer implementation, proprietary bytes or generated
original artwork is included in these tests.

This first slice is an application rendering policy: an unlit orthographic local
view with a fixed isometric projection, six-pixel fit margin and depth buffer.
It does not reproduce the original camera, scale, lighting, faction colors,
object transforms, visibility, facing selection, equipment assembly or animation
frames/timing. Parsed per-frame flags, matrices, locations and object pivots are
retained as metadata; their rendering semantics are deliberately not guessed.
Multi-component previews reject explicitly rather than silently dropping parts.
Existing sprite serialization and the billboard/movement pipeline are unchanged.
No stock role is assigned a model merely from its filename or scene name.

The decoder bounds input to64MiB, parts to256, frames to4096 and total voxel
records to2,097,152 before output growth. It accepts documented flat and jump
layouts with the observed nonlinked, five-zero-byte tail variant. Installed
flat counters include their terminal colored record; jump counters exclude one
terminal record per group. These are resource-format observations, not original
gameplay or renderer algorithms. Unknown chunks, multi-header/linked geometry,
inconsistent counters, truncated records, nonfinite transforms and unsupported
versions reject. Physical RGB and optional material/shade tables remain distinct;
the preview uses physical RGB without claiming original shading agreement.

`python3 tools/texture-tests/run.py` compiles asset-free C++ tests for both FLIC
and CVR. CVR fixtures exercise signed Z/X/Y coordinates, all26 neighbor codes,
emit-before-advance direction semantics, colored terminal records, independent
jump positions, raw animation metadata, palette colors, depth occlusion,
transparent background, clipping and fit margins. Malformed inputs include every
truncated prefix, unknown/duplicate chunks, invalid counts/links/tails/directions,
invalid scales and bounds. They are application invariants, outside recorded
original comparison totals. An optional local CLI input can inspect an installed
resource without copying it into the repository.

The independently repeated original three-role motion record observes distinct
Scout, Former and Colony bodies, visible intermediate translation and stable
all-seven-player state. It establishes neither CVR component binding nor this
preview projection. Stock wiring requires a separate clean asset-binding
observation. Full unit visual and animation parity remains unsupported.
