# Resource limits and background work

The toolkit enforces admission budgets before retaining built-in session data.
`Session::resource_usage()` reports category charges and the shared reservation
ledger. `set_memory_limit(bytes)` changes the default 1 GiB session allowance;
it rejects a limit below current reservations. Window descriptions, widget state,
render surfaces/caches, effects, jobs, messages and session metadata reserve from
that ledger. A rejected window or update releases its temporary reservations.
Opaque application models and callback captures remain application-owned.

| Storage | Accounted limit | Admission and disposal |
|---|---:|---|
| Session | 1 GiB, configurable | Shared atomic reservations; explicit errors on exhaustion |
| Window description | 256 MiB | Reserve descriptions, retained tree and semantic copies before adoption |
| Widget states | 256 MiB per store, also session charged | Compact sparse maps; release on owner removal and tab/window disposal |
| Full text layouts / paragraphs | 16 / 8 MiB per process | Capacity-accounted LRU, oversized bypass |
| Monochrome / color glyphs | 12,000,000 bytes each | Same; both purge on low memory |
| Font fallback / loaded-system answers | 2 MiB each | Same |
| OpenType plans / color-wheel rasters | 4 MiB each | Same |
| Font registry / individual font | 128 / 32 MiB | Atomic batch admission; session-loaded faces release on shutdown; explicit registrations have `unregister` |
| Font/application catalogs | 16 MiB each | Streaming cancellable walks; bounded individual files and depth |
| Native syntax index / word index | 64 / 8 MiB per document | Compact line states and revisioned source snapshots; bounded word retention |
| Native syntax tokens / token references / failed requests | 64 / 64 / 16 MiB per process | LRU by bytes; evicted tokens regenerate on the worker |
| Explicit full syntax analysis | 16 MiB source, 256 MiB output charge, 2 MiB line | Recoverable budget errors; native document editing uses the compact index |
| Worker analysis cache | 64 MiB | LRU and shared session leases; owner cancellation removes retained analysis |
| Undo and redo together | 64 MiB, 200 entries per control | Persistent rope snapshots, changed-path and delta-vector capacity charges; oldest history eviction |
| Effects | 256, 128 MiB | Reject before retaining; reservation follows delivery |
| Background queue | 64 running plus queued, 768 MiB retained requests | Nonblocking payload admission; the running provider separately reserves bounded scratch/output from the session |
| One request / provider scratch | 512 MiB maximum each | Reject before cloning; provider-specific scratch limits apply only while running |
| Mailbox | 256 messages, 256 MiB | Explicit full/closed/oversized errors; worker backpressure remains cancellable |
| One message | 128 MiB | Reject before cloning; attempt a small terminal error |
| Directory listing | 10,000 entries, 1 MiB | Stream sorted bounded retention; explicit truncation |
| Collection key maps | 128 MiB, 4 million keys | Reject oversized model indexes |
| Frame pixels | 64 MiB per surface | Checked dimension arithmetic before allocation; reserve software/GPU/transfers together |
| Settings / palettes / icon-theme inputs | 1 MiB each, placement 64 KiB | Bound file reads before allocation; reject special files |
| Localization input / PNG input / SVG input | 8 / 32 / 2 MiB | Bound file reads before decoding |
| PNG output | 64 MiB default | Validate dimensions before allocation; explicit lower output cap supported |
| SVG input / nested layers | 2 / 128 MiB | Bound nodes, depth, dimensions, layers and filter scratch |
| Vector mask | 4 million pixels | Bound flattening, curve steps and mask dimensions |
| Full-layout source | 512 KiB | Explicit error; document views use background paragraph geometry |
| Native paragraph geometry | 256 MiB per process, 2 MiB source per paragraph | Byte LRU; UI copies only visible glyphs |
| Native viewport | 16 MiB per view, shared session charged | Sparse measured row counts, at most 16,384 row metrics per owner |
| Session checkpoint | 128 MiB, 64 documents, 1 MiB metadata | Versioned binary format, bounded patch history, atomic publication and rollback on failed restore |
| Localization / icon registries | 8 / 16 MiB | Recoverable admission methods |
| In-memory clipboard / primary selection | 16 MiB each | Oversized offers leave prior contents intact |
| Host callback registry | 8,192 handles | Disposed windows release both retained view generations immediately |
| External mailbox handles | 256 per session, 1,024 process | Closed and removed with their session |

These are conservative owned-storage charges, including capacities and container
allowances, rather than RSS measurements. Some process-wide immutable/cache data
has its own cap. Copies explicitly returned to callers become caller-owned.
PNG decoding also caps internal and scratch storage separately. OS calls are
cooperative cancellation points; a deadline cannot interrupt a blocked kernel IO.
File providers reject non-regular files. Unix opens also use nonblocking mode so
a path replaced with a FIFO cannot hang the worker before its next check.

Production sessions use the shared worker even when manually stepped. It sleeps
on a condition variable with no idle timer. File reads, atomic saves, catalogs,
font loading, large local completion sets and editor analysis run there. Saves
write a unique sibling temporary file, check cancellation between chunks and
before rename, sync, then publish atomically. Failure removes the temporary file.

`services::work::Work` carries owner, request, document revision, timeout and an
operation. `UiMsg::Worked` delivers throttled progress and terminal results. New
work supersedes the same owner/operation, including results already posted.
Completion delivery checks both request and edit revision. Owner/window disposal
cancels work and releases caches. Shutdown cancels queued/running work, wakes
backpressure waits, joins the worker and closes the inbox before platform teardown.

Small pure completion callbacks remain synchronous because host callbacks belong
to the UI runtime. Expensive providers use asynchronous completion and the work
service. Explicit synchronous utility APIs remain available to callers who choose
them. Deterministic fixtures select `GUI_TEST_INLINE_WORK=1`; production defaults
to real workers. The resource regression explicitly forces real workers.

Run `tests/resources/run.sh` for the VM, forced JIT, debug-native and release-native
resource journey. It checks shared-worker file/analysis/completion delivery,
low-memory window rejection, 40 repeated window lifetimes, callback disposal and
post-after-shutdown behavior. Rust tests additionally cover queue/mailbox
saturation, cancellation races, expiry, stale delivery, atomic-save cancellation,
font lifetimes, cache eviction and bounded raster allocations. Run each crate's
formatting, Clippy and tests from its crate directory so local configuration applies.
