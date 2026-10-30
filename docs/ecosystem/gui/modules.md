# Modules

Seven modules sit beside the core widgets: terminal, docking, printing/PDF,
charts, scene canvas, image viewer and media player. Each follows one
pattern. A module object (`Terminal`, `Chart`, `Viewer`, ...) is a handle the
session owns. Its `view` builds the widget that shows it. Changes made off the
UI thread (program output, background decoding, playback progress) wake the
session, and they arrive in `update` as a `UiMsg`. Every handle's memory is
charged to the session's byte budget (see [resources](resources.md)).
Closing the session closes every handle it still owns.

Every module has a four-tier example under `examples/` (VM, JIT, debug native,
release native; `tools/check-examples.sh NAME`). The Rust tests are in
`gui-engine-gos/rust/gui-engine/src/<module>/tests.rs`.

## Terminal (`use gui::terminal`)

`Terminal::open(Options)` creates VT screen state (the `alacritty_terminal`
emulator) with bounded scrollback
(2,000 rows by default, within a 64 MiB limit that holds the largest screen,
256 x 512, so the screen always follows its view). `spawn(Command)` runs a program on a
pseudo-terminal: a Unix PTY on Linux and macOS, ConPTY on Windows. Without a
program, `feed` writes a recorded stream straight to the screen. `input` sends
keystrokes, and `paste` sends text, bracketed when the program asked for
bracketed paste. `resize`, `scroll`, `select`
and `copy` behave as in a desktop terminal, and `snapshot` answers the
visible cells.

`UiMsg::Terminal(id, Event)` reports `Title`, `Bell`, `Exited(status)`
(128 + the signal for a killed program), `Failed` when the program cannot be
waited for, and `Refused` when a smaller byte limit keeps the screen from
taking its view's size. The terminal example quits on `Exited` and shows the
program's title as its window title. Output is parsed on the
UI thread while the session settles, so screen state is never shared between
threads. At most 16 programs run at once. Each program's input and output
queues are bounded (64 KiB in, 256 KiB out). Under sustained output the
screen keeps the newest rows.

When the view resizes, lines rewrap to the new width and rejoin when it
widens again, history included, as in VTE. The widget fills the space it is
given, takes keyboard focus, sends keys with
their modifiers, selects with the pointer, and scrolls with the wheel. It
answers the visible text as its accessible value. It draws in the bundled IBM
Plex Mono at 10 points unless `view` names another installed family or size,
and a family that is not installed falls back to the bundled monospace face.
The sixteen named colors follow the Tango palette on dark themes and a set
made for light backgrounds otherwise, and any text below a 4.5:1 contrast
against its background is darkened or lightened until it reads.

Limits: macOS PTYs and Windows ConPTY compile and pass Clippy for those
targets but have not yet run on those systems.

## Docking (`use gui::dock`)

`Layout::new(panes)` creates a dock: a tree of splits and tab groups, plus
floating windows. Panes are placed at a group's left, right, top or bottom
edge or in its center (`place`), reordered, detached into a window and
reattached, and closed. `Layout::handle` folds the toolkit's tab and drop
messages (`UiMsg::Dock`) into the layout and answers the resulting `Change`s
(`Layout`, `Opened`, `Closed`, `PaneClosed`, `Focus`). Dragging a tab over a
group shows the five drop zones.

From the keyboard, `commands()` lists move-to-edge, next/previous group and
ratio nudges. `Layout::command` runs one.

`save` writes a versioned layout (version 2). `restore` migrates version 1,
drops panes the application no longer knows, places new ones, and answers a
fresh layout for corrupt input, together with the reasons. A pane's widget
state follows it between groups and between windows of different scales.

## Printing and PDF (`use gui::print`)

A document is a list of `Item`s: headings, paragraphs, code, quotes, list
items, PNG images, raw pixels, drawings, rich documents (`Item::Rich`), rules,
spacers and page breaks. `PageSetup` chooses the paper (A3, A4, A5, Letter,
Legal, Tabloid or custom), orientation, margins, body font size, and header
and footer text.

`PrintDocument::open(items, setup)` paginates once. `preview(id, page)` is a
native widget that draws a page as it prints, and `page_text` is that page's
accessible text. `export_pdf` writes a PDF 1.7 file. Its text uses embedded,
subset Unicode fonts with ToUnicode maps, so it can be searched and copied.
`print_document(PrintOptions)` sends the document to a printer:

- Linux and macOS: CUPS. The PDF goes to the spooler with `lp`; `destinations`
  lists printers (`lpstat`) and `withdraw` cancels a queued job.
- Windows: each page is drawn into a GDI print job at the printer's resolution.

Exports and print jobs run in the background (at most 8 at once). They report
`UiMsg::Print(job, Event)`: `Paginated`, `Exported`, `Submitted`, `Failed` or
`Cancelled`, and `Job::cancel` stops one. Setups that leave no printable
area, and documents over 10,000 pages, are refused with a reason.

Limits: the GDI path compiles for Windows but has not printed on Windows.
CUPS on macOS has not been run.

## Charts (`use gui::chart`)

`Chart::open(Spec)` creates a chart with titled axes. The scales are linear,
logarithmic (base 10), time (labelled dates) and category. `add_series`
adds a line, area, bar or scatter series (up to 64 per chart). `append` may be
called from any thread. Each series keeps the newest `capacity` points
(100,000 by default; 2,000,000 at most). Large series are drawn decimated per
pixel column, keeping each column's minimum and maximum.

The widget shows the nearest point under the pointer (`UiMsg::ChartPoint`),
pans by dragging, zooms with the wheel (Shift zooms the vertical axis), and
hides a series when its legend entry is clicked; a double click restores the
fitted view. From the keyboard, Left and Right move a cursor point by point
and Up and Down move it between series, reading each value aloud. Ctrl+arrows
pan, Page Up and Page Down zoom, H hides the current series and Home restores
the view. `table` and `summary` are the accessible data
alternatives. `export_png` and `print_item` draw the same picture the widget
shows.

## Scene canvas (`use gui::scene`)

`Scene::open(nodes)` creates a retained scene of rectangles, ellipses, paths,
text, images and clipping groups, each with a position, rotation and scale.
Edits (`add`, `replace`, `remove`, `restack`, `translate`, `resize`) are
undoable. The history is bounded (100 steps, 64 MiB), and a pointer drag
counts as one step. `hit` finds the topmost object at a point (`deep`
reaches inside groups); locked objects are skipped.

The widget selects the topmost object under a click (Shift adds or removes
it), drags the selection to move it or its corner handle to resize it, pans
by dragging empty space or with the middle button, zooms with the wheel, and
follows the UI scale. From the keyboard, Page Down and Page Up (Home and End)
walk the objects and announce them, the arrows move the selection (Shift
moves farther), Delete removes it, Escape clears it, and Ctrl+Z and Ctrl+Y
undo and redo. Objects appear in the accessibility tree as children of the
canvas. `export_png` and `print_item` draw what the canvas shows. Scenes hold
up to 100,000 nodes, and hit-test geometry is cached within 8 MiB.

## Image viewer (`use gui::imageview`)

Supported formats:

| Format | Support |
|---|---|
| PNG | Every color type and bit depth, widened to RGBA |
| JPEG | Baseline and progressive; EXIF orientation is applied |
| GIF | The first frame |
| SVG | The toolkit's SVG subset, rendered at up to 2048 pixels on the long side |

`Viewer::load(path)` decodes on a background thread. A second `load`
supersedes the first, whose result is discarded. `cancel` stops one.
`UiMsg::Image(viewer, Status)` reports `Ready`, `Failed(reason)` or
`Cancelled`. Malformed files fail with the decoder's reason. Images over 64
megapixels, and files over 128 MiB, are refused before any pixels are
allocated.

Decoded images are cached up to 256 MiB, keyed by path, length and
modification time, so `reload` decodes a replaced file afresh. Images larger
than 2048 pixels keep a reduced copy that is drawn when they are shown small.

The widget fits by default. A double click toggles actual size, the wheel
zooms about the pointer, and dragging pans. From the keyboard, Page Up/Page
Down zoom, Home fits, 1 shows actual size, the arrows pan and R rotates. Its
accessible description gives the image size and the current zoom.

## Media player (`use gui::media`)

Audio and video play through GStreamer 1.x, which is loaded at run time and is
optional. Applications build and run without it, and `Player::status` then
reports `Unavailable(reason)`. The playable formats are the ones the installed
GStreamer plugins decode.

| Platform | Libraries loaded |
|---|---|
| Linux | `libgstreamer-1.0.so.0`, `libgstapp-1.0.so.0` and GLib/GObject from the distribution's packages (gstreamer1.0 base plus the plugin sets for the codecs needed) |
| macOS | The GStreamer framework in `/Library/Frameworks/GStreamer.framework`, or the same libraries on the library path |
| Windows | `gstreamer-1.0-0.dll`, `gstapp-1.0-0.dll`, `gobject-2.0-0.dll` and `glib-2.0-0.dll` from the GStreamer runtime on `PATH` |

`Player::open(output)` sends sound to the system or discards it, keeping
playback timing. `load` takes a path or URI. `play`, `pause`, `seek`,
`set_volume` and `set_muted` control playback. The video surface draws only
the newest decoded frame; frames over 64 MiB are dropped.
`UiMsg::Media(player, Status)` reports state changes, and progress every
250 ms while playing. `controls(prefix)` builds play/pause, a seek slider, the
time, volume and mute from ordinary accessible widgets, and `handle` folds
their messages back into the player. Closing a player stops its pipeline and
joins its threads before returning.

An application that plays media declares `runtime = ["media"]` in its
`packaging.toml`, so its package names the GStreamer packages to install (see
[packaging](packaging.md)).

Limits: playback is verified on Linux. The macOS and Windows library loading
compiles but has not run on those systems.
