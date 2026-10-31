# Dependencies

gui-gos is the Gossamer surface of the toolkit: the widget descriptions,
`Session`, the update/view shell and their adapters are Gossamer. Widgets,
layout, text, painting and the application loop are the Rust core in
gui-engine-gos, on windowing-gos's Rust core. The table records what reaches
outside Gossamer, and why.

| Dependency | Purpose | Boundary | License | Platforms | Build/runtime requirement |
|---|---|---|---|---|---|
| Gossamer runtime and standard library | Language, collections, text, errors | The wrapper builds on the language and the two bindings only | Apache 2.0 / MIT | Linux, Windows, macOS | Gossamer `^v0.75.9` |
| [gui-engine-gos](../gui-engine/index.md) | Widgets, layout, retained state, text shaping and layout, software painting, themes, dialogs, localization, Linux AT-SPI, the application loop | Rust crate `gui-engine` behind the `gui_engine_host` binding module; widget trees, messages and queries cross as JSON | Apache 2.0 | Linux X11/Wayland, Windows, macOS | A Rust toolchain to build the binding |
| [windowing-gos](../windowing/index.md) | Native windows, input, event pump, software framebuffers, IME, clipboard, dialogs, displays | Rust crate `gos-windowing`, used by the toolkit directly and by gui-gos through `use windowing`; no SDL call leaves it | Apache 2.0 | Linux X11/Wayland, Windows, macOS | SDL 3, vendored through windowing-gos's build |
| [zbus](https://github.com/dbus2/zbus) | Linux AT-SPI, notifications, single instance | Rust crate inside gui-engine-gos and windowing-gos; nothing in gui-gos speaks D-Bus | MIT | Linux | Session and accessibility buses at runtime; no libdbus |
| [GStreamer](https://gstreamer.freedesktop.org/) 1.x (with GLib, GObject and the app library) | Audio and video playback in `gui::media` | Loaded with `libloading` when a player opens; `playbin` decodes, an `appsink` hands RGBA frames to the toolkit; nothing links it at build time | LGPL 2.1+ | Linux, Windows, macOS | Optional at runtime: without it players report `Unavailable`. Codecs come from the installed plugin sets. Verified on Linux only |
| CUPS (`lp`, `lpstat`, `cancel`) | Native printing in `gui::print` on Linux and macOS | The toolkit runs the CUPS command-line tools with the document as PDF; no CUPS library is linked | Apache 2.0 (CUPS 2.3+) | Linux, macOS | The CUPS client tools at runtime when printing; PDF export needs nothing. Windows prints through GDI instead |
| [WebKitGTK](https://webkitgtk.org/) 4.1 (with GTK 3, GLib, gdk-pixbuf, JavaScriptCore) | Web pages, in the optional `modules/webview` package only | Offscreen rendering on an engine thread, copied into RGBA frames; input forwarded as GDK events; typed Gossamer FFI in `modules/webview/src/gtk.gos` | LGPL 2.1+ (WebKitGTK, GTK, GLib) | Linux (X11 or Wayland display) | webkit2gtk-4.1 and gtk+-3.0 development files to build; the shared libraries, WebKit's web and network processes and a display at runtime; locally tested WebKitGTK 2.52.6, GTK 3.24.41 |

The Rust crates the toolkit core builds with (serde, serde_json, png,
zune-jpeg, gif, miniz_oxide, roxmltree, jiff, parking_lot, thiserror,
scopeguard, unicase, pulldown-cmark, ropey, wezterm-term, portable-pty,
libloading and the unicode-* crates) are listed in its `Cargo.toml`. Each is
available under MIT or Apache 2.0, except libloading, which is ISC.
wezterm-term, the terminal's emulator, comes from
[wezterm-lite](https://github.com/gossamer-lang/wezterm-lite), a fork of
WezTerm's terminal core under its MIT license; its image decoding uses the
`image` crate's PNG, GIF, JPEG and WebP decoders only, and its own
dependencies are MIT, Apache 2.0, Unlicense or Zlib.

SDL is not a widget toolkit: it supplies window surfaces and input events
only, the same boundary Qt and GTK sit behind. No Qt, GTK, Electron, or
other widget toolkit is introduced at any level of this package.

Optional integrations sit in their own packages under `modules/`, so the
toolkit itself never links them. The web engine is the first: applications
that do not depend on `modules/webview` carry no WebKit, GTK or GLib.
WebKitGTK draws its own pages, as a web engine must; no GTK widget appears in
a gui-gos window, which shows only the frames the engine renders offscreen.
Shaping is the toolkit's own (GSUB and GPOS, Indic syllable reordering); no
shaping library is linked. 

Installed fonts are optional. When they are allowed (the default; see
`text::fonts::use_system_fonts`), the toolkit summarises each installed face
from its naming and character-map tables and caches the summaries in
`services::cache_dir("gui-gos")/fonts-v1.json`, keyed by path, size and
modification time; characters the bundled faces lack fall back to the best
installed face that covers them.

Update owner: the gui-gos maintainers (this repository).

## Current minimums and distribution assets

The library manifest requires Gossamer `^v0.75.9`, and the example and test
projects state the same floor. windowing-gos and gui-engine-gos are
dependencies at their `v0.1.0` tags, which `gos fetch` (or `tools/fetch.sh`
for every project here) prepares.

The embedded fonts are DejaVu Sans and DejaVu Sans Mono 2.37, regular and
bold, which the engine compiles in from gui-engine-gos's
`rust/gui-engine/assets/fonts`, whose `SHA256SUMS` records the source files.
Preserve the font copyright and license (`licenses/dejavu-fonts.txt` in gui-gos) in
distributions. The terminal's font, IBM Plex Mono 2.5.0 regular and bold, is
embedded from the same directory under the SIL Open Font License 1.1; preserve
its license (`licenses/ibm-plex-mono.txt` in gui-gos) too. Runtime rendering does not need an installed font. The
toolkit's Unicode 15.1.0 property tables (`text/ucd.rs`) were generated from
the pinned data in `data/ucd-15.1.0`.

The Linux accessibility adapter is the toolkit's own AT-SPI implementation
over zbus, served on the UI thread. Distribution packages need the session
and accessibility buses at runtime and link no libdbus.

Packages of applications that use `modules/webview` must declare WebKitGTK 4.1
and GTK 3 and preserve their LGPL notices; WebKit's helper processes ship with
the system library, not with the application. The engine disables GTK's
XInput 2 device path (`gdk_disable_multidevice`) and WebKit's hardware
acceleration, so the offscreen windows can take forwarded input and their
pixels can be read. The gui-gos maintainers own the FFI declarations.
