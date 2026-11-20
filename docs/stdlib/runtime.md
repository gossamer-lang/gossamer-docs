# `std::runtime`

Status: experimental

Goroutine / scheduler introspection and tuning.

## Items

| Item | Signature | Description |
|---|---|---|
| `collect_cycles` | `fn collect_cycles() -> ()` | Requests collection of unreachable reference cycles; returns `()`. |
| `max_procs` | `fn max_procs() -> i64` | The most worker threads that run goroutines at once: what `set_max_procs` set, else `GOSSAMER_MAX_PROCS`, else the core count. |
| `set_max_procs` | `fn set_max_procs(n: i64) -> i64` | Caps the worker threads that run goroutines at once and answers the cap before the call, as Go's `runtime.GOMAXPROCS`; a value below 1 only reads it. Goroutines themselves stay unbounded. |
| `cycle_collection_supported` | `fn cycle_collection_supported() -> bool` | Reports whether this execution tier reclaims unreachable reference cycles. |
| `backtrace` | `fn backtrace() -> String` | The calling goroutine's call stack as text, outermost frame first, one `at function (file:line:column)` line each, with the file's name. The function that calls it is always named, at the call's position; an optimized build names the frames above it that it kept, without positions. |
| `is_main_thread` | `fn is_main_thread() -> bool` | Whether the caller runs on the process main thread, the one `main` starts on. Libraries whose platform APIs belong to that thread, such as windowing on macOS, check it before calling them. |
| `scheduler_stats_json` | `fn scheduler_stats_json() -> String` | Returns a compact JSON snapshot of goroutine scheduler counters. |
| `version` | `fn version() -> String` | `version() -> String`: the Gossamer release that built and runs the program, such as "0.75.6". Go's `runtime.Version`. |
| `arena_push` | `fn arena_push() -> ()` | Opens an arena region for bump allocation. |
| `arena_pop` | `fn arena_pop() -> ()` | Closes the innermost arena region, freeing its slabs. |
| `set_panic_hook` | `fn set_panic_hook(hook: Fn(String) -> ()) -> ()` | Installs a hook invoked with the message on panic. |
| `at_exit` | `fn at_exit(hook: Fn() -> ()) -> ()` | Runs a closure when the program ends: returning from `main`, `process::exit`, or an uncaught panic. Hooks run last registered first. |
| `cohort_push` | `fn cohort_push(policy: i64, timeout_ms: i64, isolation: i64, on_error: i64, uncancellable: i64, drain_ms: i64) -> ()` | Opens a cohort on the running goroutine. Written `cohort { }` in source; the block desugars to this plus `cohort_join` and a deferred `cohort_pop`. |
| `cohort_join` | `fn cohort_join() -> Result<(), errors::Error>` | Waits for every child of the running goroutine's cohort and answers `Result<(), errors::Error>`. |
| `cohort_pop` | `fn cohort_pop() -> ()` | Closes the running goroutine's cohort, cancelling and joining anything still running. |
| `cohorts` | `fn cohorts() -> Vec<String>` | One descriptor line per live cohort, oldest id first: id, parent, completion policy, error disposition, outstanding count, and the spawn indices still running. A cohort is enumerable so a program can say what it is waiting on without joining it. |
| `root` | `fn root() -> String` | The root cohort's descriptor line, in the shape `cohorts()` answers, or an empty String when no cohort is open. The root is the one cohort every program has - `main` runs inside it - and the one whose drain bounds process exit. |
| `cohort_cancelled` | `fn cohort_cancelled() -> bool` | Whether the running goroutine's cohort has been cancelled. A CPU-bound child polls this to cooperate at a point of its own choosing. |
| `cohort_cancel` | `fn cohort_cancel() -> ()` | Cancels the running goroutine's cohort, winding its siblings down without failing it. |

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->

## Cycle collection

`collect_cycles()` is experimental. The compiled runtime collects
thread-local RC graphs; values that have crossed a goroutine boundary are
excluded because concurrent mutation cannot safely participate in its
thread-local trial-deletion pass. Break such cycles with `Weak<T>`.

The bytecode VM uses `Arc`-backed values and currently treats this call as a
no-op. `Weak<T>::upgrade()` remains valid for the supported VM heap values,
but collection-driven weak invalidation is not a cross-tier guarantee yet.
