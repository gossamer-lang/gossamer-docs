# Runtime internals

This page is a map - not a specification - of what happens between
`gos` and `main` returning. Each section links to the crate that
owns the stage so a new contributor can find the real source.

## Stages

```
source.gos
   │
   ▼
┌──────────────┐  gossamer-lex        tokens + source map
│  Lexing      │
└──────────────┘
   │
   ▼
┌──────────────┐  gossamer-parse      AST (items + uses)
│  Parsing     │  gossamer-ast        + diagnostics
└──────────────┘
   │
   ▼
┌──────────────┐  gossamer-resolve    name resolution, imports
│  Resolution  │                      path → DefId mapping
└──────────────┘
   │
   ▼
┌──────────────┐  gossamer-types      type inference, trait solve,
│  Type check  │                      exhaustiveness
└──────────────┘
   │
   ▼
┌──────────────┐  gossamer-hir        lowered program tree
│  HIR lower   │                      (match-desugars, for → loop)
└──────────────┘
   │
   ▼
┌──────────────┐  gossamer-interp     register-based bytecode VM;
│  Evaluation  │                      the LLVM and Cranelift backends
└──────────────┘                      live in gossamer-mir / -codegen-*.
```

## Evaluator

The register-based bytecode VM in `gossamer-interp` is the sole
`gos` / `gos test` engine. It:

1. Accepts an `HirProgram`.
2. Compiles every top-level function and inherent-impl method to a
   register-machine `FnChunk`, registered under both the unqualified
   (`foo`) and type-qualified (`Type::foo`) names.
3. Registers builtin callables for stdlib functions (`env::args`,
   `time::sleep`, `json::parse`, …) and variant constructors for
   every user enum.
4. Executes the compiled bytecode in a register machine, keeping
   locals in per-frame register files. Every construct - closures,
   `select`, `defer`, or-patterns, goroutines, custom iterators - is
   lowered to native bytecode; nothing is interpreted from HIR.

Struct values are `Vec<(Ident, Value)>`. Field assignment runs
through a copy-on-write helper that allocates a fresh `Rc` so alias
bindings never observe each other's mutations.

## Memory management

Compiled programs manage memory deterministically with a Swift-like
model - reference counting plus arenas, and no tracing collector:

- **Reference counting** (`gossamer-runtime::c_abi::rc`). Recursive
  heap enums and runtime containers carry an intrusive
  `[RcHeader | payload]` header. Codegen emits balanced
  retain/release pairs; a strong count hitting zero releases the
  value's reference-counted children iteratively and frees the
  payload. Weak references follow the Swift-ARC model.
- **Cycle collection.** The compiled tiers run a Bacon-Rajan
  trial-deletion pass over suspected cycle roots when the program asks
  for it (`runtime::collect_cycles()`); no collector runs on its own. The
  bytecode VM backs values with `Arc` and does not collect cycles, so
  `collect_cycles()` is a no-op there. A closure's captures are not
  traced on any tier, so a closure stored in a value it captures is
  never freed: capture the value weakly (`[weak o] || ..`).
- **Aggregate reclamation.** Structs / tuples / arrays are
  heap-allocated via `gos_rt_aggr_alloc` (plain zeroed malloc) and
  freed by the MIR drop pass via `gos_rt_aggr_free` at scope exit.
- **Arenas.** `arena { }` blocks bump-allocate and free wholesale
  at every block exit.

The bytecode VM piggy-backs on Rust's `Rc` / `Arc` for object
lifetime; its output is the semantic oracle the compiled tiers
match, cross-checked by the tier-parity suite and the VM-vs-LLVM-AOT
differential.

## Scheduler

`gossamer-runtime::sched` is the work-stealing M:N scheduler.
Every Gossamer binary links it through `libgossamer_runtime.a`, so
`spawn(|| expr)` in compiled code (and the bytecode VM) lands on the same
shared pool. Workers start as goroutines call for them: one at start,
and another when a goroutine is placed while every started worker
already has one. The pool's bound defaults to `num_cpus()`, overridable
via `GOSSAMER_MAX_PROCS=N` or `runtime::set_max_procs(n)` from
user code. A parked worker sleeps until a wake or its next timer, and
the watchdog sleeps while no worker needs it (on Linux, unless a worker sits
in a blocking call), so an idle program makes no system calls. A worker
that has had no goroutine of its own for 10 s exits, down to one, so a
program that once ran a burst of goroutines gives its threads and their
memory back.

Deferred JIT promotion reports compile time, emitted native-code bytes, and
process RSS through VM diagnostics. Set `GOS_JIT_MAX_CODE_BYTES=N` to reject a
promotion whose retained code would exceed `N` bytes for that VM; set
`GOS_JIT_MAX_RSS_MB=N` to reject a promotion before compilation when the
process is already at its RSS budget. A rejected artifact releases its MIR
snapshot and remains on bytecode.

A `MultiScheduler` owns:

- one work-stealing deque per worker M (a `crossbeam_deque::Worker`),
- a global injector (`crossbeam_deque::Injector`) for cross-thread
  pushes and the netpoller's wakeup path,
- a `parked` map keyed by `Gid` for goroutines suspended on I/O,
  channels, mutexes, sleeps, or the blocking-syscall pool,
- a watchdog thread that asks a worker running past its 10 ms slice to
  yield (on Linux each worker times itself instead, on its own CPU
  clock; see [Preemption](#preemption)), starts workers for blocked
  system calls, and applies the allocator purge.

## Goroutines

`spawn(|| expr(args))` is a real stackful coroutine. Construction:

1. `gossamer_runtime::sched_global::spawn(closure)` allocates a
   1 MiB `corosensei::Coroutine` stack (override:
   `GOSSAMER_GOROUTINE_STACK=N`). The stack is an `mmap` reservation
   fronted by a guard page; the OS commits pages on first touch, so
   resident memory tracks the depth a goroutine actually uses rather
   than the reservation. See [Goroutine stack model](goroutine_stacks.md).
2. The coroutine's entry shim publishes its `Yielder` pointer to a
   shared slot, sets the worker's TLS yielder, then runs `closure`.
3. The scheduler wraps the coroutine in a `GoroutineTask` whose
   `step()` calls `coroutine.resume()`. Result `Yield` →
   `Step::Yield`; result `Return` → `Step::Done`.

When user code blocks (channel recv on empty, mutex contention,
`time::sleep`, `net::TcpStream::read` returning `WouldBlock`,
filesystem syscall via `blocking_pool::run`), the helper calls
`sched_global::park(reason, |parker| { register parker.gid with
the wakeup source })` and then `gossamer_coro::suspend()`. The
worker M sees `Step::Yield` plus a pending-park flag and moves
the task into `MultiScheduler::parked` keyed by gid. The wakeup
source (poller readiness, channel send, mutex unlock, blocking-pool
worker, ...) calls `MultiScheduler::unpark(gid)` which pushes the
task back onto its home worker's inbox. A stackful coroutine cannot
migrate between OS threads while suspended, so a goroutine resumes on
the worker it first landed on.

A blocked goroutine costs only the few KiB of stack its shallow
frame actually touched - not an OS thread, and not the 1 MiB
reservation. Thousands of concurrent goroutines stay in the tens of
MiB of resident memory; the 1 MiB reservations consume address space
(abundant on 64-bit) that never becomes resident until used. The
[Goroutine stack model](goroutine_stacks.md) note explains why this
guard-page / lazy-commit scheme was chosen over Go-style copyable
stacks.

The wake-before-park race window (where `unpark(gid)` arrives
before the goroutine has actually been moved into `parked`) is
closed by a `pre_unpark` set: if `unpark(gid)` finds the gid not
yet parked, it records the gid; the worker about to park the
task observes the pre-unpark and immediately re-ejects the task
to the injector instead of leaving it parked.

## Preemption

Scheduling is **cooperative**: nothing moves a running goroutine off its worker
without that goroutine reaching a safepoint. This is the one place the runtime
is weaker than Go 1.14 and later, whose signal handler relocates a goroutine
from a loop that never yields.

A goroutine yields the worker M at *safepoints*:

- every park point - channel send/recv, `select`, mutex contention,
  `time::sleep`, scheduler-aware network reads, and core filesystem operations,
- in compiled code (the LLVM native tier and the Cranelift JIT), the head of
  the outermost loop of each loop nest, once per pass of that loop. A poll is a
  test of the runtime's `gos_rt_preempt_requested` byte and a branch to a cold
  call when it is set (`gossamer-mir/src/preempt.rs` chooses the headers). A
  nest that is counted all the way down and calls none of the program's own
  functions is not polled: it is the numeric kernel whose trip counts its
  caller chose, and it runs to completion. A call into the program's own code
  is not itself a safepoint; it makes the nest that contains it polled,
- loop back-edges **on the bytecode VM**, which polls every 1,024 taken
  back-edges.

A goroutine is asked to yield once it has run for a 10 ms slice:

- On Linux each worker arms a timer on its own thread CPU clock
  (`CLOCK_THREAD_CPUTIME_ID`) once for its life. The timer delivers `SIGURG`
  to that worker alone at every 10 ms of CPU it uses, and the handler sets the
  yield request. The clock stands still while the worker is parked, so a park
  or resume costs no system call, and the watchdog thread sleeps unless a
  worker sits in a blocking call.
- Elsewhere, and on a Linux host that refuses the timer, the watchdog thread
  (`sched::multi::watchdog_loop`) checks each running worker's last yield every
  ~5 ms and raises the yield request for one that has run more than 10 ms
  without one.

Neither path interrupts a worker from another thread; the request is read at
the goroutine's next safepoint. The watchdog also starts workers for goroutines
waiting behind a blocked system call, drives vacant pollers, and applies the
allocator purge.

### What this means for a program

A CPU-bound loop nest that is counted all the way down (`for` over ranges) and
calls none of the program's functions holds its worker until it finishes; any
other loop yields within a slice. On the bytecode VM every loop yields through
the back-edge poll.

With max-procs workers this starves one worker, not the program: peers keep
running. It becomes visible when such nests outnumber the workers, or when a
single-worker configuration runs one. To hand the worker back from a long
counted kernel, call one of the program's own functions in its outer loop, or
make the outer loop a `while`; either makes the nest polled at its head.
`runtime::cohort_cancelled()` is a cancellation check, not a safepoint.

A VM configured with one goroutine worker can still be monopolized by one
nonterminating task; replacing that pool with resumable VM frames remains a
tracked limitation.

Not every host operation is scheduler-aware yet. Core filesystem file and path
I/O, HTTP client work, channels, timers, and socket readiness are routed or
parked. Specialty filesystem bridges, some process pipe operations, compression,
terminal calls, and third-party binding code still require effect-ledger audit.

## Netpoller

`gossamer-runtime::sched::poller::OsPoller` wraps `mio` (epoll on
Linux, kqueue on macOS / BSD, IOCP on Windows). Each scheduler
worker has a poller of its own: a worker with nothing to run blocks in
it until a descriptor is ready or its earliest timer is due, and the
goroutines that become runnable resume on that worker. Threads outside
the scheduler share one more poller, driven by a `gos-netpoller` thread
started the first time it is needed. Timers (`time::sleep`,
`time::after`, I/O deadlines) live in the same pollers. Every
`os::signal::on` subscription is relayed by one `gos-sig` thread.

## HTTP server

`gossamer-std::http::server::run` and the compiled-tier
`gos_rt_http_serve` both:

- bind a non-blocking `TcpListener`,
- park on the netpoller for accept readiness,
- spawn each accepted connection as a goroutine via
  `sched_global::spawn`,
- read / write under the netpoller - `WouldBlock` parks the
  goroutine; the worker thread immediately picks up another
  connection.

Graceful shutdown is driven by:

- `GOSSAMER_HTTP_MAX_REQUESTS=N` - env var, stop after N requests.
- `gossamer_interp::set_http_max_requests(N)` - safe-Rust test hook.
- `config.shutdown: AtomicBool` - for in-process callers.

## Panic recovery

`panic(msg)` in user code returns `RuntimeError::Panic(msg)` from
the evaluator. The native HTTP server catches that per-request,
logs it, and returns a 500. A panic inside a goroutine body
unwinds the coroutine's stack and propagates to the worker M's
resume site - the worker exits with the panic, but other
goroutines on other workers continue running. A program-wide
panic handler can be installed via `panic::set_hook` from user
code.

## Where each stage is tested

| Stage | Test location |
|-------|---------------|
| Lexing | `gossamer-lex/tests/` |
| Parsing | `gossamer-parse/tests/` |
| Resolution | `gossamer-resolve/tests/smoke.rs` |
| Type check | `gossamer-types/tests/typeck.rs`, `tests/exhaustiveness.rs` |
| HIR lower | `gossamer-hir/tests/lower.rs` |
| Interpreter | `gossamer-interp/tests/{eval,run_pass,vm,http_end_to_end}.rs` |
| Stdlib | `gossamer-std/src/*` (`#[cfg(test)]` modules) |
| Driver | `gossamer-driver/tests/` |
| CLI | `gossamer-cli/tests/cli.rs` |
