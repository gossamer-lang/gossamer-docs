# Editor measurements

Run `./tests/performance/run.sh` with the rebuilt Gossamer 0.75.0 compiler in
`GOS`. The runner preserves its report directory and prints its location. Set
`GUI_PERFORMANCE_OUT` to choose that location. It records hardware/OS/compiler
metadata, per-operation nanoseconds and a percentile summary for VM, forced JIT,
debug native and release native. JIT runs must install native entries.

The fixed fixtures repeat one source-line template 32 and 2,048 times. Repetition
favors paragraph reuse and does not represent diverse source files. Measurements cover session
startup with the document, committed typing, alternating cursor movement,
alternating wheel scrolling and a completion open/dismiss cycle. They include
model updates, layout and software presentation. Compilation precedes the
in-process startup timer; OS process startup and file IO are not included.
Completion includes dismissing suggestions and removing the query to restore
the next sample's starting point.

Default sampling is 12 operations per category and one startup per process.
`GUI_BENCHMARK_SAMPLES` changes that count. Percentiles use nearest rank; twelve
samples are exploratory and do not establish stable tail-latency budgets.
`GUI_PERFORMANCE_TIERS='debug release'` selects native-only diagnostic runs;
only the default four-tier run supplies the complete matrix.
`GUI_PERFORMANCE_TIMEOUT` bounds each process (default 900 seconds, followed
by forced termination after five seconds). Incomplete runs fail and retain
partial CSV files rather than reporting successful measurements.

Use an idle machine and repeat runs before comparing performance. Concurrent
compiler builds affect timings. The runner isolates Linux settings so saved
window placement cannot change the viewport. Other platforms still need an
isolated application-settings profile and actual presentation measurements.

Layout, shaping and painting run in the Rust toolkit core
(gui-engine-gos); the paragraphs below describe that engine. The layout looks up grapheme boundaries and lines by binary search rather
than rescanning the document for each glyph or caret operation. Paragraph
shaping is reused through a cache with an 8 MiB accounting budget, and paragraph
discovery splits the source once. Rounded border painting skips its untouched
interior. Unicode/selection, warm/cold geometry and border clipping checks cover
these changes. Native documents now keep rope indexes and persistent snapshots, shape paragraphs
on a cancellable worker and copy only viewport glyphs. Full layouts have a 16 MiB
cache. `tests/documents/run.sh` exercises 10+ MiB source and a 1 MiB line, while
`tests/resources/run.sh` verifies shared byte admission and disposal. These CPU and
offscreen gates do not establish real-platform input-to-present calibration.

An exploratory controlled cache comparison (`tests/performance/reports/2026-10-18-paragraph-cache/README.md` in gui-gos)
retains raw timings and hashes for the same compiler and system-allocator runtime.
It isolates paragraph reuse from the earlier, confounded runtime-build comparison.
The final four-tier diagnostic (`tests/performance/reports/2026-10-18-four-tier/README.md` in gui-gos)
also retains resource measurements and artifact sizes with the default runtime.
Both reports use two samples per operation.

## Latency budgets

`./tests/perf/run.sh` checks release-native latency budgets, separate from
`tests/performance/run.sh`'s four-tier editor diagnostics. It measures startup,
idle wakeups, committed typing, scrolling a million-row two-column table,
opening a 100,000-choice picker and resizing. Every fixture emits one record
and fails on semantic errors or exceeded ceilings. Reports retain compiler
hashes and environment details; see fixture definitions (`tests/perf/README.md` in gui-gos).

Software/offscreen ceilings, checked against the recorded baseline:

| Fixture | p95 | p99 |
|---|---:|---:|
| Startup to first frame | 500 ms | 500 ms |
| Typing | 8 ms | 16.7 ms |
| Million-row table scroll | 8 ms | 16.7 ms |
| 100,000-choice picker opening | 200 ms | 250 ms |
| Resize | 16.7 ms | 33.4 ms |
| Static idle over 60 seconds | 0 extra loop wakeups | 0 extra frames |

Typing and scrolling use the guide's initial UI-work targets. Startup, picker
and resize ceilings are initial regression limits, to be assessed against the
baseline before claiming calibrated performance. The picker remains separately
subject to cancellable background-provider and input-responsiveness work.

Reference host inspected 2026-10-21: AMD Ryzen 9 9900X (12 cores, 24 threads),
Linux Mint 22.2 (Zara), Linux 7.0.0-31-generic, Gossamer 0.74.0. PCI graphics
identities are NVIDIA `2d04` and AMD `13c0`; the connected DP-5 display advertises
3840 x 2160. These fixtures use a synthetic offscreen display at scale 1 and
640 x 480 windows (idle: 320 x 200), so physical refresh and GPU are outside
the measurement. The runner records the full PCI and CPU descriptions. Actual
display refresh and native presentation still need a real-platform baseline.


The 2026-10-21 release baseline (`tests/perf/reports/2026-10-21/README.md` in gui-gos)
passes all six fixtures. With 100 samples, p95 is 15.63 ms startup, 1.46 ms
typing, 2.42 ms table scrolling, 109.55 ms picker opening and 1.39 ms resize.
The 60 second idle observation reports zero extra loop wakeups and frames.
Completion ranking extracts score/label/key once per item for sorting, keeping
its existing score-descending and label/key-ascending order. The initial
ceilings are now enforced regression limits on this host; repeated runs and
real-platform input-to-present calibration remain release work.

The 2026-10-22 run after the toolkit moved into the Rust core, on the same
host with Gossamer 0.75.0, passes five fixtures and fails one. With 100
samples, p95 is 22.84 ms startup, 1.27 ms typing, 3.64 ms table scrolling and
1.28 ms resize, with zero idle wakeups. The picker opens in 205.60 ms at p95
(219.29 ms at p99), over its 200 ms ceiling, against 109.55 ms before. Each
view the toolkit rebuilds now crosses the binding as JSON, about 13 MB for the
100,000 items (about 12 ms to encode); how many views one press rebuilds is
not yet measured.

The native document runner records 30 committed edits per size, including model
updates and software presentation. Its four-tier functional ceiling defaults to
1,000 ms p95 to detect stalls independently of VM/JIT compilation. Set
`GUI_DOCUMENT_P95_MS=75` for the stricter release-native regression gate on this
host; `--timings` prints raw percentile and reservation diagnostics separately
from the deterministic transcript. Compile before timing and run on an idle host.
