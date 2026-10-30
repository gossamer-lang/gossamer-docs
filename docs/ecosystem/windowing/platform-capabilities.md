# Platform capabilities

Platforms differ in what a window can do. `windowing::capabilities()` answers
the active video driver and a record for each named feature, and
`get(name)` answers the record for one feature, or nothing for a name it does
not know. Each record is one of:

- `Available`: the driver implements the operation.
- `Conditional`: it works when the hardware, desktop service, permission or
  setup it needs is present.
- `Unavailable`: this driver has no implementation.

An available operation can still fail at run time, so handle its error. Read
the records again after input devices change. An unknown or uninitialized
driver reports everything unavailable.

| Area | How it works | Limits |
|---|---|---|
| Windows, resizing, scaling, frames | SDL, with checked sizes; a frame taken before a resize is refused | |
| Placement and stacking | X11, Windows and macOS | Wayland lets the compositor place windows; position, always-on-top and whole-window opacity are unavailable there |
| Parent and modal windows, transparency, hit testing | SDL | |
| Live resize | Normal events; a redraw hook while Windows and macOS run their own resize loop | |
| OpenGL, Vulkan, Metal | Native surfaces and contexts per backend | |
| Keyboard and IME | SDL composition, commit, input purpose and caret area | |
| Surrounding text and reconversion | | Unavailable: SDL 3.4 has no API for them |
| Pointer capture, confinement, relative motion | SDL | Needs focus, and on Wayland the compositor's permission |
| Touch and pen | SDL events with pressure and tilt | Needs the hardware |
| Clipboard | Text and any MIME type; the X11 or Wayland primary selection | Primary selection needs desktop support |
| File dialogs | Native choosers, answered asynchronously | `App::cancel_dialog(id)` stops the answer; an open chooser cannot be closed from the program |
| Cursors | System cursors and custom RGBA ones | |
| Drag and drop | XDND on X11, data devices on Wayland, OLE on Windows, AppKit on macOS | |
| Tray, notifications, desktop preferences | SDL tray and native notification and preference adapters | Need a tray host, a notification service, or on macOS an application bundle and the user's permission |
| Activation | EWMH startup context, Wayland activation tokens, Windows foreground permission, AppKit | The window manager or compositor decides whether focus moves |
| Accessibility providers | UI Automation on Windows, NSAccessibility on macOS | On Linux the toolkit speaks AT-SPI itself |

## Checking a platform

`cargo run --release --example platform-check` (in `rust/gos-windowing`)
exercises these operations on the current native driver; it fails on the
offscreen driver. `tests/instance/native.sh` runs it, with the single-instance
probe, on private X11 and Wayland displays with a real input seat.

## File dialogs

A dialog's answer arrives as `Event::DialogClosed`. `App::cancel_dialog(id)`
delivers one `Cancelled` answer and drops the native one when it comes.
Finishing the session drops answers that have not been delivered. At most 64
choosers can be open, and 64 finished answers waiting, at a time.
