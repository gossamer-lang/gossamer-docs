# Toolkit and platform checkpoint

This checkpoint adds working controls and picker workflows. It does not close
all foundation or platform release gates in the implementation guide.

## Controls and dialogs

`Widget::date_field`, `time_field`, `datetime_field` and `duration_field` retain
incomplete/invalid drafts, expose validation through semantics, and emit
`UiMsg::Date(id, canonical_value)` only for a changed valid value. Configure
`TemporalEditor.min/max` for bounds. Dates use the Gregorian calendar, years
1 through 9999. ISO input and nonnegative `hours:minutes:seconds` durations are
locale independent. Invalid bounds prevent acceptance. `temporal::resolve_local`
uses the timezone database and returns the standard library's explicit unique,
DST gap or fold result. A civil picker does not silently choose an instant.

`Calendar` supports arrows, Home/End, month paging, Ctrl+Page Up/Down for years,
mouse selection, minimum/maximum dates and RTL. Native accessibility identifies
each calendar cell by its ISO date. Out-of-range grid cells are disabled;
leading/trailing cells outside the supported year range are omitted.

`ColorPicker` is a caller-owned draft model:

<!-- fragment -->
```gos
let mut next = model
if let Some(color) = next.picker.update(msg) {
    // Reversible preview; the application decides when to commit it.
}
// view:
next.picker.view()
```

The wheel, RGB/HSV/HSL numeric channels, alpha slider and CSS field share that
model. Invalid/incomplete CSS preserves the last valid color. Unpremultiplied
sRGB, alpha, canonical CSS, hue retention for gray colors, original/current
checkerboard previews and keyboard alternatives are implemented. Labels are
above their fields, with wrapped labels and a separate visible CSS label.
The layout regression checks three widths, fractional scale, RTL and 200% text.
The CSS subset remains documented in `style/color.gos`; context-dependent and
wide-gamut expressions are reported unsupported.

Color dialogs have separate `DialogPreview` events and one terminal `Dialog`
outcome. Cancel or owner disposal queues the original preview before the
terminal outcome. Favorite named colors and a bounded recent-color history use
`services::palette::ColorPalette`; dialog storage is the application's
`color-swatches` settings file. Add/rename/remove and CSS copy actions are
keyboard reachable. Storage failures remain visible. An acceptance can succeed
when saving optional swatch history fails; it does not roll back the color.

Font dialogs support searchable installed/registered families, style, size and
sample preview. The catalog reads metadata while retaining file references,
with limits of 512 files, 64 MiB read and 64 faces per collection. Selected
families load lazily. Missing fonts show fallback text and cannot be accepted.
Font axes and asynchronous catalog discovery are still open.

Preferences have searchable pages, field validation, defaults, nonterminal
Apply, a committed Apply baseline, OK/Cancel, and explicit dirty-discard review.
Wizard pages retain drafts, support Back/Next and conditional skipping, and
validate all visible pages before Finish. Asynchronous service acknowledgments,
progress/cancellation and failure recovery for these two templates remain open.

The toolkit file browser now has stable favorite identities, labels,
rename/reorder/remove/relink actions, persistence and missing-location feedback.
Legacy path favorites migrate on load. Favorites and per-purpose recent history
remain separate. Removing a favorite never removes its folder. Back/Forward
history is bounded to 32 locations; failed navigation preserves both stacks.
Breadcrumbs, refresh, relative locations, a persistent hidden-file toggle and
inline new-folder creation are implemented. New-folder validation rejects path
separators and existing names, preserves the Save filename, and restores focus.
Directory IO is still synchronous; bounded asynchronous listing, path completion,
details/sort controls and grant-aware sandbox integration remain open.

`widgets::navigation` supplies a virtual sidebar, breadcrumbs, toolbar,
status bar, disclosure and accordion composition using standard focusable
controls. Sidebar selection uses `Select`; breadcrumb buttons use `Click`;
disclosure headers use `Toggle`. The showcase has date/color and navigation
pages and color/font/date/preferences/wizard dialog launchers.

## Localization

`localization::Catalog` supports contexts, integer plural forms and safe
single-pass named substitution. `Effect::SetLocale` installs a catalog, applies
its direction and rebuilds windows. Standard dialog action labels consult the
catalog. Catalogs must still be authored/extracted and applied throughout all
built-in strings. Locale-sensitive number/date presentation, broader plural
coverage and complete language-change/RTL journeys remain open. ISO/CSS storage
must remain locale independent.

## Native accessibility

On Linux, the toolkit core publishes a real AT-SPI application over zbus: cache,
accessible tree, names/states, actions, component bounds, text/selection/editing
and numeric ranges. Stable native paths are retained across updates and never
reused after removal. Cache/structure, focus, state, text/caret and announcement
signals accompany updates. Requests are polled and dispatched on the UI thread;
modal-layer checks reject background requests. Connections and snapshots are
released at shutdown. No foreign callback thread accesses toolkit state.

D-Bus introspection describes the live object namespace and the implemented
methods and properties of each object. EditableText disappears for read-only
fields; password fields do not advertise Text. Unsupported methods are omitted.
Signatures follow the [GNOME AT-SPI interface definitions](https://github.com/GNOME/at-spi2-core/tree/main/xml),
including the signed 16-bit Component stacking order. The private-bus probe
parses the XML, checks the actual reply type, discovers objects, edits a field
through AT-SPI and verifies graceful disconnect. This is protocol evidence;
screen-reader acceptance and text geometry remain open.

`GUI_ACCESSIBILITY=off` disables the connection. `on` requires an available
session/accessibility bus; auto skips offscreen/dummy video. Inspect
`Session::accessibility_status()` and `accessibility_endpoint()` for the actual
result. Failure to connect is reported as unavailable, rather than a listener.

The bridge is an initial Linux provider. Visual text ranges/line boundaries,
complete selection/table/virtual-item interfaces, live-region throttling,
full introspection and real screen-reader journeys still need completion.
Windows UIA and macOS accessibility providers are unavailable. Source checking
on those targets is not native accessibility evidence. Mixed-DPI global bounds
and real Wayland interaction are not certified by X11 or offscreen checks.
Native menu state, outbound drag/drop, notifications/tray/activation/printing,
and platform IME/clipboard/appearance journeys also remain release gates.

## Validation

Run `tests/toolkit-platform/run.sh` for the fixed four-tier journey. Set
`GUI_TOOLKIT_MEMORY=1` and `GOS_RUNTIME_LIB` to a system-allocator runtime archive
for strict debug/optimized Valgrind checks. `tests/toolkit-platform/atspi.sh`
launches only this fixture on an isolated session/accessibility bus and checks
native cache discovery, text query, an edit applied by the UI thread and
normal shutdown. Native AT-SPI protocol probes complement semantic tests; they
do not constitute a screen-reader acceptance journey.

The existing editor memory gate and four-tier parity remain required. Retain
raw reports, compiler/runtime hashes and any failures. Never infer zero leaks
from functional output alone.

The retained toolkit verification report (`tests/memory/reports/2026-10-18-toolkit-platform/README.md` in gui-gos)
records 140 passing tests, matching four-tier journeys, clean strict native
memory checks and the private-bus AT-SPI protocol probe.

The editor confirmation report (`tests/memory/reports/2026-10-19-confirm-exit/README.md` in gui-gos)
adds actual Save/Don't Save/Cancel button clicks, file-content checks and native
exit verification. Its four strict memory runs pass. After the additional browser-navigation
regression, the current GUI suite passes 142 tests and 974 assertions.
