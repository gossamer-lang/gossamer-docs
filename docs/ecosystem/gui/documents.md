# Native document editing

All Rust text controls use a persistent UTF-8 rope. Small string-valued controls
keep their existing `UiMsg::Text` API. Large editors use
`gui::editing::document::Document` and `TextInput.document`, exchanging handles
and `UiMsg::DocumentChanged(id, handle, revision)` instead of copying a file
through every view/update callback.

```gos
use gui

let document = gui::editing::document::Document::new("initial text")
let mut input = gui::TextInput::new("editor", "", "Source", gui::InputKind::Area)
input.document = document.id
input.mono = true
input.wrap = false
```

`info()` reports revision, byte/line counts, selection and dirty state.
`replace(expected_revision, start, end, text)` applies an atomic transaction or
returns a stale-revision/budget error. Offsets are UTF-8 bytes on grapheme
boundaries. `anchor(byte, Affinity::Before/After)` creates a stable insertion
anchor; resolve and release it explicitly. Ordered bulk edits prepare a position
map before locking the registry, then resolve each anchor with a binary search.
Undo/redo preserve shared roots and selection within the history budget, including
the capacity of their change metadata. Composition stays outside committed text;
Escape cancels it and a platform text commit records one edit.

`freeze()` creates a native immutable snapshot handle. Use it for
`Operation::WriteDocument(snapshot.id, path)`; successful saves mark precisely
that snapshot as saved. Later edits remain dirty. `read(start, end)` and `text()`
are explicit copies into application-owned storage. `close()` releases a handle;
all remaining handles belong to their session and close with it. Rust readers
can share immutable `Buffer` snapshots across threads.

The worker provides `ReadDocument`, `AnalyzeDocument`, `CompleteDocument`,
`SearchDocument` and `ReplaceDocument`. Requests carry owners, request IDs,
revisions and deadlines. Search streams Unicode graphemes with KMP, preserving
case-fold expansion, grapheme endpoints and whole-word policy. Replace-all
validates every range before committing one transaction; cancellation or a stale
revision preserves the live document. Cancellation is rechecked under the commit
lock before mutation. Analysis and search for a superseded revision cancel
quietly; the editor also compares delivered results with the current native
revision before applying them. Search results are capped at 100,000.
Completion queries and indexed proposal labels are bounded to 4 KiB.

Native highlighting stores lexical state per line and bounded interned tokens.
An edit reparses its changed region and propagates state until the unchanged
suffix converges. Evicted token data regenerates on the worker. Paragraph
geometry is also computed there, including complete bidi/shaping context for
long lines. Viewport copies contain only visible glyphs. Sparse measured row
heights refine the scroll range as paragraphs are visited; unmeasured regions
use estimates. Small visible regions paint immediately while exact geometry
arrives. Native long-paragraph geometry is limited to 2 MiB of source.

`SaveSession(path, records, metadata)` atomically writes a versioned checkpoint.
Each record has an application key and native document handle. Checkpoints retain
committed text, save markers, selections, scroll policy and bounded undo/redo as
patches. `RestoreSession` validates the whole file, rolls back partial restores
on error, and returns new handles plus the application's metadata. Corrupt,
unsupported or oversized checkpoints leave the existing session intact.
Cancelled, unconsumed native results release their temporary handles.

The code editor has **Save Session** and **Restore Session** commands. It saves
tab order, paths, pinned state, active tabs and window ownership in metadata.
A saved checkpoint can include modified documents. Startup without file arguments
attempts restoration; restoring over modified live tabs is refused until the
user saves or closes them. Close review still offers Save, Discard and Cancel,
and tab transfers preserve the native document and its editing history.

Run `tests/documents/run.sh` for four-tier large-document validation. Rust tests
cover concurrent readers, Unicode/bidi edits, composition, anchors, state
propagation, stale revisions, malformed checkpoints, cancellation and disposal.
See [resource limits](resources.md) and [performance](performance.md).

Gossamer 0.75 compatibility: the adapter spells an idle edit group
`EditKind::NoEdit` to avoid colliding with prelude and standard-library `None`
variants. The Rust API retains `EditKind::None`; its wire representation is
`NoEdit` and deserialization also accepts the legacy `None` spelling.
