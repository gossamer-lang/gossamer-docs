# Structured documents

`gui::rich::Document` owns structured blocks in the native toolkit. Its immutable
snapshots share unchanged blocks and rope chunks. Application models keep handles
and revision numbers; they do not copy the entire document on each keystroke.
`examples/rich-editor` demonstrates editing, outline paging, a selectable preview,
formatting, list commands and background import/export/image loading.

```gossamer
use gui::rich::{Document, Format, Edit, Mark}
let document = Document::import(Format::Markdown, "# Notes\n\nHello **world**")?
let block = document.outline(0, 1)?[0].block
let info = document.info()
document.transact(info.revision, #[Edit::SetMark {
    block: block, start: 0, end: 5, mark: Mark::Strong, enabled: true
}])?
let editor = document.input(block, "editor")?
let preview = document.preview("preview", 0, 16)?
```

Create handles during application initialization/update so their storage belongs
to that session. Close explicit handles when their owner disappears, including
frozen handles after a save/export. Session shutdown closes its remaining handles.
Small explicit synchronous imports/exports are useful for initialization and tests.
Use `Operation::ImportRich`, `ExportRich` and `ReadRichImage` for user documents.
They use the shared bounded worker, deadlines, cancellation and owner supersession.
A delivered import transfers ownership of its `Record.document` to the application;
an undelivered result automatically closes it. Reject results whose source revision
or owner no longer matches the current editor. `rich-editor` shows this check.

## Model and editing

Blocks have stable positive identities, a kind, rope text, inline spans and child
blocks. Supported kinds are paragraphs, headings 1 through 6, fenced code,
quotations, ordered/unordered lists, list items and horizontal rules. Inline marks
include bold, emphasis, underline, strike, code, links and image objects. Containers
hold child blocks; leaves hold text. Code blocks accept plain text only. Invalid
structure, duplicate identities, invalid ordinals, unsafe links and out-of-range
spans produce explicit errors before publication.

Positions use UTF-8 bytes at grapheme boundaries within a text block. Each
transaction checks its expected revision and publishes all edits atomically.
Replace, mark/link changes, insert/remove/move, split/join and kind changes share
one undo/redo history. Formatting a collapsed selection changes the pending typing
marks without making the document dirty. Selection, typing marks and content are
restored by undo. IME composition stays local until committed text arrives.

`Document.input` returns an ordinary text area connected to a structured leaf.
Ctrl/Cmd+B, I and U format its selection, and Ctrl/Cmd+Z/Y use structured history.
Enter splits a paragraph or list item and selects the new leaf; Shift+Enter inserts
a hard break. Code-block Enter inserts a newline. Tab/Shift+Tab indent/outdent list
items. An empty single-paragraph item exits its list. The application follows
`UiMsg::RichChanged` and retargets its editor using `info().selection.caret.block`.
`Document.enter`, `indent` and `wrap` expose the same commands for toolbars.
Text clipboard operations use the existing text controller.

`freeze` creates a read-only immutable handle. After successfully writing that
snapshot's exported text to disk, `mark_saved(snapshot)` marks exactly that root
saved; later edits remain dirty. A snapshot from another document is rejected.
The document API supports cross-block selection coordinates, while the example
edits one selected leaf at a time. Rich search/replace across blocks is not a
separate rich-document API; plain document search remains available in the source
editor.

## Markdown and HTML contract

Markdown supports paragraphs, headings, strong/emphasis/strike/code, links,
images, hard breaks, fenced code, quotations, nested ordered/unordered lists and
rules. Import uses pinned `pulldown-cmark` 0.12.2. Underline and styles that
CommonMark cannot express use the supported inline HTML tags. Export checks its
own semantic round trip; blocks that would lose spacing, empty paragraphs or
styles use explicit supported HTML rather than silently dropping content.

HTML is a strict, well-formed XHTML-compatible document/fragment subset, parsed
without DTDs or entity declarations. It supports `p`, `h1` through `h6`,
`blockquote`, `ul`, `ol`, `li`, `hr`, `pre`/`code`, inline `strong`/`b`, `em`/`i`,
`u`, `s`/`del`, `a`, `br` and `img`. Use self-closing `br`, `img` and `hr`
in imported fragments. Attribute-free `html`, `body` and `div` wrappers are
also accepted. Links accept `href`/`title`; images accept `src`, `alt`,
`title`, `width` and `height`; ordered lists accept `start`. Code language uses the
supported `language-` class on `code` inside `pre`. Unknown tags/attributes,
scripts, styles, event handlers, unsafe schemes and malformed nesting are rejected.
This parser does not implement browser HTML error repair. These are documented
subsets, so arbitrary web pages and unsupported Markdown constructs can fail.
Import errors retain the original document.

No HTML, scripts, URLs or images execute or fetch automatically. Links emit
`UiMsg::RichLink` for application handling. Images use explicit source keys and
alt text; `ReadRichImage(document, source, local_png_path)` decodes a local PNG on
the worker. Unsupported/missing images show an alt-text placeholder. Image
references survive import/export; binary assets remain external. Dimensions of
1 through 4096 pixels are supported, with a 128 by 96 preview box when unspecified.
No implicit network access or natural-size decode runs during painting.

## Rendering, accessibility and bounds

Software rendering remains the permanent default. Rich text uses the existing
paragraph bidi/font/shaping machinery, including joining context across style
runs. Inline styles split ligatures at boundaries; image dimensions participate
in line layout and hit geometry. Long paragraphs shape on the worker. While exact
geometry is pending, the editor uses bounded viewport geometry and the preview
reserves its estimated height. Completion wakes the owning window; no busy timer
is required. Owner disposal cancels pending geometry, and font changes purge it.

The preview exposes a document role, real heading levels, selectable paragraph
text, list items, link actions and named image children with geometry. Keyboard
and accessibility link actions emit the same message. The editor exposes the
existing editable text semantics. This does not certify complete AT-SPI, UIA or
NSAccessibility coverage; real assistive-technology acceptance remains item 11.

Limits are 8 MiB aggregate text/attributes, 256 KiB per paragraph, 10,000 blocks,
65,536 inline spans and nesting depth 32. History retains at most 200 entries and
64 MiB conservatively charged roots. There are at most 1024 native document
handles. Geometry and each document's image cache use byte-bounded 64 MiB caches
with session admission. A PNG input is at most 32 MiB and decoded pixels at most
16 MiB. Oversized source, structure, requests and outputs fail explicitly. Frozen
handles, caches, history, imports and temporary shaping/serialization all reserve
session storage; low-memory admission leaves committed content unchanged.

Run `tools/check-examples.sh rich-editor` for its four execution tiers, including
real-worker import/export and image decode. Native rich regressions live in the
Rust `rich` module; `tools/check-rust.sh` includes them. The canonical release gate
also builds/packages the example and runs its installed artifact on clean Linux
images. Existing software screenshot goldens must continue to pass exactly.
