# windowing-gos guide

How to use `use windowing`: the event loop, windows, drawing, input and the
platform services. The [README](index.md) has a complete first program.

## The event loop

`windowing::init` starts the platform session and answers the `App` every
other call goes through. `app.wait()` blocks until the next `Event`; the
thread sleeps, using no CPU, while nothing happens. `app.wait_timeout(ms)`
answers `None` at the timeout, for a loop that also animates, and
`app.poll()` answers the next event of the batch already delivered, without
waiting. `app.finalize()` ends the session; `defer` it right after `init`.

`Event` is one enum: window events (`Resized`, `PixelSizeChanged`,
`ScaleChanged`, `CloseRequested`, `FocusGained`, `Occluded`, ...), input
(`KeyDown`, `KeyUp`, `Text`, `Composing`, `PointerMoved`, `ButtonDown`,
`Wheel`, `TouchDown`, `Pinch`, `PenMoved`, ...), drag and drop
(`DropBegan`, `DroppedFile`, `DroppedText`, `DropEnded`), displays,
application lifecycle (`Suspending`, `Resumed`, `LowMemory`), and
`RedrawRequested`, `Wake`, and `QuitRequested`. Each event names its window
by `WindowId`; `app.window_by_id(id)` answers the window.

### Background work: the waker

Windowing calls run on the main thread (the platforms require it; a call
from a goroutine panics and says so). A goroutine that has a result sends it
on a channel and wakes the loop with a `Waker`; the loop answers `Event::Wake`
and drains the channel:

<!-- fragment -->
```gossamer
let tx, rx = channel()
let waker = app.waker()
cohort {
    spawn(|| {
        tx.send(fetch())
        waker.wake()
    })
    loop {
        match app.wait()? {
            Event::Wake => {
                while let Some(result) = rx.try_recv() { show(result) }
            }
            Event::CloseRequested { .. } => break
            _ => ()
        }
    }
    runtime::cohort_cancel()
}?
```

Wakes coalesce: any number of `wake()` calls before the loop runs again
answer one `Event::Wake`, so the channel carries the values and the waker
only says to look. Pair a waker with an unbounded or buffered channel; a
rendezvous `channel()` blocks the sender until the loop receives.
`examples/ticker` is the complete program.

## Windows

`app.window(title:, width:, height:, resizable:, borderless:, transparent:,
hidden:, maximized:, fullscreen:, always_on_top:)` opens a window; every
argument has a default. `app.window_with(WindowOptions { .. })` adds the
rest: a position, a GPU surface (`graphics: Graphics::OpenGl`, `Vulkan`,
`Metal`), a window kind (`Utility`, `Popup`, `Tooltip`, `Modal`) with its
`parent`, high pixel density, and focusability.

Sizes and positions are in logical units; `pixel_size()` and `scale()` give
the framebuffer's pixels and the display scale. A `Window` changes its
title, size, limits, position, fullscreen state (desktop or an exclusive
`Mode`), opacity, parent, and icon, and answers its state (`is_maximized`,
`has_focus`, `display`, ...). `request_redraw()` queues a
`RedrawRequested`. `set_hit_test(..)` declares draggable and resizable
regions of a borderless window's own title bar.

`app.on_live_resize(|win| ..)` redraws while the user drags a window border
on Windows and macOS, where the system runs a loop of its own until the drag
ends and `wait` does not return meanwhile.

## Drawing

**Software.** `win.framebuffer()` answers a `Frame`: `pixels`, `width`,
`height`, `stride`, and the pixel `format` (`format.rgb_offsets()` says where
red, green, and blue sit). Draw into it, rows in parallel with
`frame.pixels.par_chunks_mut(frame.stride, |y, row| ..)`, then
`win.present(frame)`. Take a new frame after a resize or a scale change; an
old one is refused. `win.capture()` reads back what the window shows.
On X11 a frame presents through X11 shared memory and loads no OpenGL driver;
`SDL_FRAMEBUFFER_ACCELERATION=1` picks SDL's GPU-backed path.

The Rust core additionally exposes `compositor::Compositor` for accelerated
2D target/layer composition. It is owned on the UI thread and released before
the window. `Event::RenderReset` reports native renderer reset/device loss;
applications recreate resources or fall back to their software reference.

**GPU.** `win.raw_handle()` answers the native window and display
(`RawHandle::Xlib`, `Wayland`, `Win32`, `AppKit`, `Drm`) for a GPU binding.
`win.gl_context(GlOptions { .. })` creates an OpenGL or GLES context with
`make_current`, `swap`, `set_swap_interval`, and `proc_address`. Vulkan:
`windowing::surface::vulkan_instance_extensions()`,
`windowing::surface::vulkan_get_instance_proc_addr()`, and
`win.vulkan_surface(instance)`. Metal: `win.metal_view()`.

## Input

Keys come two ways. `Key` is what the key cap says under the current
layout: letters, digits, and the keys that print nothing have variants
(`Key::A`, `Key::Num1`, `Key::F5`, `Key::Escape`); any other key that types
a character is `Key::Char(c)`. `Scancode` is the physical position, for game
controls that should not move with the layout. `KeyDown` carries both, the
modifiers (`Mods`), and whether it repeats; `mods.shortcut()` is Command on
macOS and Control elsewhere.

Text is separate from keys: `Event::Text` carries what the user typed,
after the layout, dead keys, and the input method; `Event::Composing`
carries the input method's preedit. Call `win.start_text_input()` while a
text field has focus and `win.set_text_input_area(rect, cursor)` so the
candidate window appears beside it.

The pointer reports `x`, `y`, the motion, the held `Buttons`, and its
`PointerSource` (mouse, touch, pen). `set_relative_pointer` locks it for
camera control, `set_pointer_confined` keeps it in the window, and
`app.capture_pointer(true)` keeps delivering motion outside the window
during a drag. Touch, pinch, and pen events carry pressure, tilt, and the
eraser state.

## Platform services

- `windowing::clipboard`: text, any MIME type (`set_data` offers several
  types at once; another application pastes the one it asks for), and the
  primary selection X11 and Wayland keep.
- `windowing::dialog`: native file open, save, and folder dialogs
  (`app.open_file_dialog(FileDialog { .. })`; the choice arrives as
  `Event::DialogClosed`), and message boxes (`message_box`, `ask`).
- `windowing::cursor`: system cursors and custom RGBA ones, show and hide.
- `windowing::display`: every display's bounds, usable bounds, scale,
  orientation, and modes.
- `windowing::system`: the light or dark theme, the preferred locales,
  opening a URL, revealing a file, and inhibiting the screensaver.
  `system::preferences()` answers the desktop's high-contrast,
  reduced-motion, accent-color and text-scale preferences, each `None` where
  the platform does not say (the XDG desktop portal on Linux, system
  parameters, DWM and the Accessibility registry key on Windows, AppKit on
  macOS); after the first call `Event::PreferencesChanged` says to read them
  again. The text scale is what the desktop applies beyond the display's
  content scale: on X11, where the content scale comes from the DPI the
  desktop publishes and that DPI already holds the text factor, it is `None`.
  `tests/preferences/run.sh` checks it against a stand-in portal on all four
  tiers, and on X11 against a nested Xephyr with each source of the scale.
- `windowing::tray`: an icon in the system tray with a native menu
  (`app.tray(Some(icon), "tooltip")?`, then `tray.set_menu(entries)`); a
  chosen item arrives as `Event::MenuSelected` with `MenuSource::Tray`.
  Linux needs a StatusNotifier host and libayatana-appindicator.
- `windowing::menu`: the menu model the tray and the macOS menu bar share
  (`MenuEntry::Action`, `Check`, `Radio`, `Separator`, `Submenu`, each with
  an enabled flag and an optional `Shortcut`). Item identities are the
  program's; it updates its own state on `Event::MenuSelected` and installs
  the menus again.
- `windowing::notify`: desktop notifications (`app.notify(Notification { .. })`)
  through the session's notification server on Linux,
  `UNUserNotificationCenter` on macOS (the program must run from an
  application bundle; the user is asked once), and a notification-area
  balloon on Windows, which Windows 10 and later show as a toast;
  `notify::has_notifications()` says whether this platform has an adapter.
- `windowing::drag`: dragging data out to other applications
  (`app.start_drag(win, #[DragItem { mime, data }], DragOperation::Copy)`,
  called while a button is held); `Event::DragFinished` reports the target's
  operation, or `None` when nothing accepted the drop. X11 speaks XDND and
  Wayland the core data-device protocol (copy and move; a link answers an
  error there). Windows runs OLE's `DoDragDrop`, which returns when the drop
  ends, offering each item under its MIME type and as the standard format
  (text, files as `CF_HDROP`, URLs, HTML). macOS starts an AppKit dragging
  session, each URI of a `text/uri-list` its own item.
  `drag::has_outbound_drag()` is false on drivers without a drag source.
- `windowing::access`: the screen-reader providers of Windows (UI
  Automation) and macOS (NSAccessibility). `access::update(win, elements)`
  describes a window's semantic tree as `AccessElement`s (role, name, value,
  bounds in framebuffer pixels, states, range, actions, children), the first
  being the window; `access::focus` and `access::announce` follow the
  program's focus and speak; `access::take_requests()` answers what the
  screen reader asked (an element's action, `focus`, `set-text`,
  `set-value`) after an `Event::Wake`. `access::listening()` says whether a
  client is reading. On Linux the toolkit speaks AT-SPI itself and
  `access::has_provider()` is false.
- `windowing::instance`: single-instance ownership, activation and bounded request forwarding on Linux, Windows and macOS.
  `instance::claim(app_id, Request::Open { uris })` answers `Claim::Primary`
  in the first process, whose `Listener` a goroutine parks on with
  `os::fd::wait_readable` and drains with `take_requests()`, and
  `Claim::Forwarded` in a later one, which has handed its request over. Linux
  serves `org.freedesktop.Application` on the session bus; macOS keeps one
  instance itself and delivers opened documents as `Event::OpenRequested`.
  `instance::file_uri` and `uri_path` convert between paths and `file://`
  URIs.

### Platform polish

On macOS every program gets the application menu (About, Hide, Quit, with
Cmd-Q, Cmd-H, and Cmd-M) and a Window menu. `app.set_menu_bar(menus)` puts
the program's own menus between them, with enabled, checked, and shortcut
state; `Event::MenuSelected` names the item and the key window. Elsewhere
`set_menu_bar` answers an error and `menu::has_native_menu_bar()` is false,
so a toolkit draws the menus in the window.

On Windows 11, `win.set_backdrop(Backdrop::Mica)` (or `Acrylic`, `Tabbed`)
sets the material the system draws behind the window: in its title bar, and
in a `transparent` window's client area where its pixels are clear. The
title bar follows the system's light or dark theme on its own;
`win.set_frame_theme(Some(Theme::Dark))` draws it dark (or light) when the
program's theme differs, and keeps that choice when the desktop's theme
changes. macOS applies the same call through the window's `NSAppearance`,
X11 window managers through `_GTK_THEME_VARIANT`; on Wayland it answers an
error, since the compositor or libdecor draws the frame.

`set_backdrop` answers an error on the platforms without the feature, so a
program calls it unconditionally and ignores that answer where it does not
apply.

See [platform capabilities](platform-capabilities.md) for what each driver
supports. `App::cancel_dialog(id)` stops a dialog's answer from being
delivered; SDL cannot close a native chooser that is already showing.

### Single instance in detail

Single-instance listeners support `wait(timeout_ms)` on every platform. Only
Linux provides a descriptor for integrating the listener with an FD event loop.
Forwarding acknowledges admission to a bounded queue; queue/transport failures
are explicit errors. CLI launches retry primary startup/exit races. Windows
secondaries grant the primary foreground permission before activation. Claims
release on close, drop or process exit; the stable ownership lock file is never
unlinked, preventing an inode-replacement race. A separate endpoint file remains
readable while Windows holds the exclusive ownership lock. URI conversion handles Unicode,
Windows drive paths and Windows UNC paths.

`Listener.take_forwarded()` preserves each request's `Activation` context;
`take_requests()` remains available for callers that only need paths/actions.
Pass the context to `Window.focus_with_context()`. On Linux this carries D-Bus
`activation-token` and `desktop-startup-id` values instead of discarding them:
Wayland applies the token to the existing SDL surface, and X11 forwards the
startup identity and its server timestamp. `Window.activation_token()` can mint
a token for an eligible Wayland surface with a two-second deadline. Compositor
policy still controls focus; a compositor without xdg-activation returns an
explicit unsupported error. Other platforms use their native focus request.

## Capability differences by platform

| Capability | Availability |
|---|---|
| Single-instance claim/forward | Linux D-Bus; Windows/macOS per-user ownership lock plus authenticated, acknowledged loopback; native macOS launch events remain supported |
| Surrounding text/reconversion | Not supported by the current SDL text-input adapter; capability reports false |
| Native menu bar | macOS; other desktops use toolkit-drawn menus |
| Frame theme | Windows, macOS and X11; Wayland compositor owns decorations |
| Mica/Acrylic backdrop | Supported Windows versions only |
| Outbound drag | X11, Wayland, Windows and macOS adapters; query `has_outbound_drag()` |
| Primary selection | X11/Wayland desktop support required |
| Tray | A tray host is required; Linux also needs libayatana-appindicator |
| Notifications | Linux session service; macOS application bundle and permission; Windows notification-area balloon |
| Screen-reader provider | Windows UIA and macOS NSAccessibility; Linux AT-SPI belongs to the toolkit |
