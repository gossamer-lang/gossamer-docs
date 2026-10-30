# Testing windowing-gos

## Tiers

Every function works the same on the bytecode VM (`gos run`), the JIT, and
native builds (`gos build`). `tests/parity` runs the library's fixtures on
SDL's `offscreen` video driver, which needs no display, on all four
(VM, JIT, debug and release native) and compares the transcripts byte for
byte:

```sh
tests/parity/run.sh
```

`app.simulate(event)` queues any `Event` as the platform would deliver it,
with the fields given: input, window and display changes, the theme, the
clipboard, a dialog's result, and the application's lifecycle. That is how
those fixtures, and your own tests, drive a window without a user; the
fixtures queue input and service events and check that each reads back equal to
what was queued. `SDL_VIDEO_DRIVER=offscreen gos test .` runs the Gossamer wrapper unit suite. SDL structures are declared by `sdl3-sys`
in the Rust core, rather than handwritten Gossamer C layouts. The parity fixtures need Gossamer 0.75.0, which compares
an `Event` by its fields on every tier. `tests/smoke` opens a real window on the platform's own driver,
presents a frame, reads it back, and closes it through the event queue; CI
runs it on Linux X11 and Wayland, macOS, and Windows. `tests/instance/run.sh` hands two paths from a second launch to the first on
a private session bus on all four tiers. `tests/xdnd/run.sh`
drags text between two windows on a private X server (Xvfb, or Xephyr
nested in the current display) with XTest on all four tiers.
`tests/wldnd/run.sh` drags text on a private Weston whose input comes from a
nested Xephyr, dropping on the program's own window and on a second process,
on all four tiers. `tests/platform` applies a frame theme, a backdrop and a
notification to a real window and reads the frame theme back from the window
system (DWM on Windows 11 and Server 2025, `_GTK_THEME_VARIANT` on X11).
`tests/oledrag` drags text and a file between two processes on Windows
(`run.ps1`, with SendInput) and `tests/uia` drives the UI Automation provider
from a client in another process (`client.c`, `run.ps1`) or checks the
NSAccessibility provider in-process on macOS (`--self-check`); CI runs them
on Windows and macOS runners. Under Wine 9 on Linux the two-process drag
passes and a client reads the provider's tree. `./quick-check.sh`
formats, lints, and checks the generated `src/keys.gos` against its generator.
Run the Rust checks from their crate directories:

```sh
(cd rust/gos-windowing && cargo fmt --all --check && cargo clippy --all-targets -- -D warnings && cargo test)
(cd rust/binding && cargo fmt --all --check && cargo clippy --all-targets -- -D warnings && cargo test)
```

## Single instance

Linux single-instance tests need `dbus-run-session` (the `dbus` package) and
start private session buses through `tools/private-bus.sh`, which starts only
the D-Bus services a suite names, so a desktop's portals never join one. The
Rust tests run two real processes: concurrent
launches, activation, forwarding, and restart after a normal exit or a crash.
`tests/instance/native.sh` runs two native processes on private X11 and Wayland
displays, checks Unicode/URI forwarding, verifies that the existing primary gets
keyboard focus while the secondary stays open, then closes and reacquires the
claim. Linux needs Xvfb, Sway, Xwayland, a C compiler and X11 development headers.
The nested compositor supplies a real keyboard seat and xdg-activation; an old
headless compositor without those capabilities cannot test foreground focus.
Windows/macOS CI runs the same Rust `instance-check` example on their own drivers.

## Building the binding crate

The binding crate needs the Gossamer binding SDK, which is not published on
crates.io. Programs get it from `gos`; standalone Cargo checks take the one
`gos env` reports as `binding_sdk`, a Gossamer checkout's
`crates/gossamer-binding` or a release tag:
`--config 'patch.crates-io.gossamer-binding.path="/path/to/gossamer/crates/gossamer-binding"'`.

## Resource budgets

`tests/measure/measure.sh` measures one idle window for 60 seconds and event
throughput on each tier, beside the same programs written in C over the same
SDL build. With `--gate` it fails above the budgets CI holds it to: the idle
software window at most 32 MiB, 2 threads and one wakeup a second, the GL
window within 25% (plus 8 MiB) of C's memory, and native and JIT events at
most 4 and 20 times C's cost.
