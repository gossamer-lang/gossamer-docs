# Testing

Set `GOS` to a Gossamer 0.75.9 or newer executable when `gos` on your `PATH`
is older; `tools/check-toolchain.sh` checks it. `tools/fetch.sh` fetches the
tagged windowing-gos and gui-engine-gos releases for the library and every
example and test project, and the release gate runs it first.
`tools/check-rust.sh` checks the Rust cores of windowing-gos and
gui-engine-gos checkouts beside this one.

Toolkit behavior (widgets, layout, text, painting, dialogs, accessibility,
retained state and widget lifetimes) is tested in the Rust core:

- `cargo test` in `../gui-engine-gos/rust/gui-engine`: the engine's unit and
  session tests. They run one at a time (`.cargo/config.toml` sets
  `RUST_TEST_THREADS=1`), and every session runs on one UI thread the test
  build keeps, since SDL expects video on the thread that started it. They
  use the offscreen video driver, so no test opens a window on a desktop.

The suites here check the Gossamer surface over it, on every tier:

- `./quick-check.sh`: format-check every source except the hashed reproducers under `tests/memory/reports`, then lint and typecheck every manifest.
- `./tests/wrap/run.sh`: drive sessions through the wrapper (choices whose items change under them, filters, focus) on all four tiers.
- `./tests/toolkit-platform/run.sh`: dialogs, the file browser, menus, tabs and windows through `Session` queries on all four tiers.
- `./tests/parity/run.sh`: compare VM, forced JIT, debug native and release native with a fixed transcript. It covers editing, offset conversions, syntax, completion, dialogs, tab transfer, a feature-gated module (also checked with `--no-default-features`) and worker posts through a session mailbox.
- `./tests/resources/run.sh`: real-worker file/analysis/completion, aggregate admission, repeated window/callback disposal and shutdown on all four tiers.
- `./tests/documents/run.sh`: 10+ MiB Unicode/bidi source and a 1 MiB line, native handles, typing, immutable snapshots, anchors, worker search, undo/redo, save markers and checkpoint restoration on all four tiers.
- `./tests/screenshots/run.sh`: render fixed scenes (themes, right to left, text, selection, menu, dialog, table) through `Session::screenshot` with the embedded fonts only and compare each with its golden PNG exactly, on all four tiers; see the scenes (`tests/screenshots/README.md` in gui-gos).
- `./tools/check-examples.sh [NAME...]`: build hello-world on both native profiles and run each named example's scripted journey (every example with one when no name is given) on all four tiers.
- `./tools/check-rust.sh`: run formatting, Clippy and tests for both Rust cores and bindings. Set `GOSSAMER_BINDING_PATH` to the compatible SDK crate when it is not published on crates.io.
- `./tools/check-source-policy.sh`: reject non-Gossamer sources in this package; the Rust cores live in their own packages.
- `./tests/perf/run.sh`: release-native latency budgets (startup, typing, scroll, a 100,000-item picker, resize, idle wakeups); `./tests/performance/run.sh` preserves editor measurements; see [method and limits](performance.md).
- `./tests/scale/run.sh`: drive a select and a searchable picker with 100,000 choices by keyboard as release native code, failing on a wrong outcome and printing each step's time.
- `./tests/memory/run.sh`: fail on invalid accesses and all lost allocation categories; see runtime setup (`tests/memory/README.md` in gui-gos).
- `./tests/memory/journeys/run.sh`: repeat window, popup, tab tear-off and editor lifecycles at two lengths on all four tiers, failing when live objects at exit or open descriptors grow; see the journeys (`tests/memory/journeys/README.md` in gui-gos).

Sessions under these suites use the offscreen video driver
(`SDL_VIDEO_DRIVER=offscreen`). Text that falls back to installed fonts writes
the font catalog cache under `$XDG_CACHE_HOME/gui-gos`; point
`XDG_CACHE_HOME` elsewhere to keep a run self-contained, as every suite but
`toolkit-platform` and `memory` does on its own.

The example runner bounds each fixture process to 300 seconds (override with
`GUI_FIXTURE_TIMEOUT`) and forces termination after five additional seconds.
It isolates Linux settings and keeps logs on failure.

Expected transcripts are never regenerated after a failure. Offscreen tests
cannot show real screen-reader behavior, input-method candidate placement,
desktop portals or mixed-DPI hardware.

Regression runners link native programs into fresh output directories and keep
binding caches inside their run directory. This prevents a previously compiled
executable from masking a Rust-only engine edit. Reusing an explicit screenshot
or wrapper report directory still creates a fresh work directory for each run.

The native single-instance regression is `../windowing-gos/tests/instance/native.sh`.
It uses Xvfb and a nested Sway compositor with a keyboard seat, verifies real
foreground handoff between two processes on X11 and Wayland, and retains the
Wayland activation exchange. The portable ownership and crash/restart cases also
run in the Windows and macOS CI jobs.

## The release gate

`tools/release-gate.sh OUT` runs every check above, the native display tests,
cross-target checks for Windows and macOS, packages each example and installs
it in clean Ubuntu, Debian and Fedora containers. It records each command, its
exit code, duration and log checksum in `OUT/results.json`, and fails if a
source file changes while it runs. `--list` prints the commands and the group
each belongs to without running them, `--group NAME` runs one group, and
`--profile portable` skips the native display tests.

## Continuous integration

The Gossamer packages build against the tagged releases their manifests
name. CI also checks out windowing-gos and gui-engine-gos beside gui-gos, at
those same tags, for the Rust cores and windowing's native tests; the
`WINDOWING_REF` and `ENGINE_REF` repository variables move both to a newer
compatibility set together.
