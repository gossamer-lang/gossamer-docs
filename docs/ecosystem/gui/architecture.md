# Architecture and current boundaries

Three packages, each depending on the one before it:

| Package | Language | Holds |
|---|---|---|
| [windowing-gos](../windowing/index.md) | Rust core `gos-windowing` + Gossamer `use windowing` | Windows, input, IME, clipboard, native dialogs, displays, tray, menus, notifications, single instance, Windows and macOS screen-reader providers |
| [gui-engine-gos](../gui-engine/index.md) | Rust core `gui-engine` + binding module `gui_engine_host` | Widgets, layout, the retained state store, text shaping and layout, software painting, themes, dialogs, localization catalogs, Linux AT-SPI, the application loop |
| gui-gos | Gossamer, `use gui` | Widget descriptions, `Session`, the update/view shell, effects, and the adapters below |

The Rust engine depends on `gos-windowing` directly, so window and input
calls never cross into Gossamer and back. gui-gos talks to the engine through
one binding call per operation, passing JSON: a view's `Widget` tree, each
`UiMsg` the update receives, and every query a `Session` answers.

## Sessions and the update/view shell

`Session` holds a toolkit session id. `application(..).start()` registers the
program's `update`, `view` and command functions with the toolkit; the toolkit
owns the windows, routes native events, lays out and paints, and calls `update`
with each `UiMsg` and `view` for each window it rebuilds. Applications can also
drive a session directly (`press`, `type_text`, `click`, `inject`, `flush`) and
read it back through queries: `window_count`, `window_id`, `window_size`,
`window_pixel_size`, `window_theme`, `window_frames`, `edit_state`,
`choice_state`, `dialog_draft`, `part_rect`, `semantics`, `capture_window`,
`screenshot` and `log`. Native window operations belong on the UI thread.

## Closures in widget descriptions

A view's closures (validators, custom widget measure/draw/input, row sources)
cannot cross as JSON, so builders such as `Custom::new` and
`TextInput::validated` register each one with the toolkit and store its id in
the widget. A closure a view registers stays registered for two of that
window's views, so the tree one view old can still call back while the next is
built; one registered outside a view stays registered until the session
closes. `src/app/host.gos` keeps that bookkeeping and the typed adapters.

## State, focus and closing

Widgets use application string ids with generation tracking in the toolkit's
retained state store. Layout produces the tree used for hit testing, focus and
semantics. Inactive tab pages keep their state; cross-window page transfers
migrate state, generations and timers before disposal.

`Session::focus` validates that a focusable control is live and respects modal
focus. A window's ask-close policy produces `UiMsg::CloseRequested`, leaving it
open for an asynchronous document decision. Applications complete accepted
closes with `close_window`; quit review is separate.

File dialogs open in a modal window of their own, parented to their owner and
sized for browsing (900 by 620 units, at least 560 by 420), so they are not
limited by the owner's size; the toolkit remembers where the user left them.

## Workers

`Session::mailbox` posts messages that wake the event loop. Its queue, the
effect queue and worker requests share the session's byte ledger. The shared
worker handles file IO, catalogs, font loading, completion, document analysis,
viewport geometry and checkpoints. Requests carry owners, revisions and
cancellation/deadline tokens; supersession invalidates already-posted results.
Idle work sleeps on a condition variable. Shutdown cancels, joins and closes
posting before platform teardown. See [resource limits](resources.md).

The editor exchanges native document handles and revisions. Reads create the
rope on the worker, saves use immutable snapshots, and analysis retains a compact
line-state index with bounded token caches. Window disposal releases hosted
callbacks and cancels its owners. `Session::serve_instance(listener)` converts
file requests to `UiMsg::Open`, other schemes to `UiMsg::OpenUri`, and activation
to a window raise with the launcher's activation context. Linux forwards desktop
startup IDs and Wayland tokens to the existing surface. Claim/forwarding failures
are reported as `Launch::Failed`.

## Text and painting

The toolkit records retained scenes and renders damaged regions through the
software reference or the SDL GPU compositor. See [rendering](rendering.md).
Embedded font assets supply outlines, and installed faces supply characters
they lack: each grapheme cluster takes one face that covers all of it, chosen
from a cached catalog of installed faces by style, locale region and family;
clusters shown as emoji prefer color faces. The text engine handles grapheme
boundaries, shaping (GSUB/GPOS with Arabic joining forms and Indic syllable
reordering), bidi layout and paragraph geometry reuse. The paragraph cache has
an 8 MiB accounting budget. Full layouts have a 16 MiB cache; native document
views use bounded background paragraph geometry and viewport copies. Editing
uses persistent ropes, revisioned transactions and bounded shared history.
See [documents](documents.md). CFF2/COLR/sbix coverage and real accessibility
provider journeys remain separate work.
