# Packaging

## Building

`gos build --release` in an application's directory writes one native
executable to `target/release/`. gui-gos and windowing-gos compile into it;
SDL 3.4.10 is built from the pinned `sdl3-src` dependency and linked statically.
Fonts the toolkit draws with are embedded, so no font needs installing.

## Packages

`tools/package.sh APP_DIR [OUT]` runs `tools/package.gos` with `gos run` (set
`GOS` to choose the compiler). It builds into a
fresh temporary directory with `gos build --release --out-dir`, packages that
exact executable, and writes a SHA-256 sidecar for the archive. It lays it
out the way the platform it runs on installs applications, in `OUT` (default
`dist/`):

| Platform | Package | Contents |
|---|---|---|
| Linux | `<exe>-<version>-linux-<arch>.tar.gz` | `bin/<exe>`, `share/applications/<app_id>.desktop`, the icon in the hicolor theme, `share/doc/<exe>/` notices, and `install.sh` |
| macOS | `<Name>.app` and `<Name>.app.zip` | `Contents/Info.plist` (the application id as `CFBundleIdentifier`), `MacOS/<exe>`, `Resources/AppIcon.icns`, the notices; ad-hoc signed |
| Windows | `<exe>-<version>-windows-<arch>.zip` | `<exe>.exe` and the notices |

The application directory holds `packaging.toml` next to `project.toml`:

```toml
name = "Code Editor"
app_id = "dev.gossamer.gui-code-editor"
comment = "Edit source files with highlighting and completion"
categories = "Development;TextEditor;"
```

`name` is what the desktop shows, and `app_id` must be the id the application
passes to `gui::application`. `runtime = ["media"]` declares a module the
toolkit loads at run time when it is present; the package manifest then lists
its distribution packages (GStreamer's base and good plugin sets for `media`),
and clean installs add them. Modules reached through dependencies, such as
`modules/webview`, are found without a declaration. The version and executable name come from
`project.toml`. The icon is the one the application sets with `App::icon`:
run with `GUI_EXPORT_ICON=<file>`, an application writes its icon there as a
PNG file and exits without opening a window. Export must exit with status 0
having written the file. An application without an icon declares `icon = false` in
`packaging.toml`; hello-world demonstrates this. Applications managing their own
session must honor icon export before claiming an instance or opening windows.

On Linux, `install.sh` in the unpacked folder installs under `PREFIX`
(default `~/.local`), and refreshes the desktop database where
`update-desktop-database` exists. Every example carries a `packaging.toml`,
and CI packages them on every platform. Linux archives are written
with the system `tar`, which keeps the executable modes of `bin/<exe>` and
`install.sh`.

## What the executable needs at runtime

On Linux a release executable loads these as shared libraries:

- libc and libm, from glibc, and libgcc_s. The executable needs the glibc of
  the machine that built it or a newer one: a build on Ubuntu 24.04 (glibc
  2.39) runs on Ubuntu 24.04, Debian 13 and Fedora 41, but not on Debian 12
  (glibc 2.36). Build packages on the oldest distribution you support.

Everything else is opened at runtime when present: libX11 (the X11 drag source
and frame theme) and libwayland-client (the Wayland drag source) by
windowing-gos, and the X11 extension libraries, libdecor and the input method
and GL libraries by SDL, so one executable serves X11 and Wayland sessions.
Accessibility, notifications and single instance speak D-Bus without libdbus. Check a build with `ldd`. Applications that
use `modules/webview` also need WebKitGTK 4.1 and GTK 3, and WebKit's helper
processes, which come with the system's WebKitGTK package.

On macOS the executable uses only system frameworks. Notifications need it to
run from an application bundle with a bundle identifier: `UNUserNotificationCenter`
asks the user for permission the first time, and outside a bundle
`App::notify` answers an error.

On Windows the executable uses only system DLLs (user32, gdi32, shell32,
ole32, oleaut32, comctl32, dwmapi, uiautomationcore). Notifications are
notification-area balloons, which Windows 10 and later show as toasts under
the executable's name.

## Clean installs

`tools/clean-install.sh PACKAGE.tar.gz [IMAGE...]` installs a Linux package
into fresh containers (default `ubuntu:24.04`, `debian:trixie`, `fedora:44`)
with the runtime packages declared in the artifact manifest. No workspace, SDK or
compiler is mounted. It checks the embedded executable checksum, installs under
a prefix containing spaces, verifies the desktop launcher and notices, and
compares exact fixture-output hashes. Set `GUI_INSTALL_REPORT` to retain image
IDs and results. Fedora uses `libwayland-client`; Ubuntu/Debian use
`libwayland-client0`. It checks the installed
executable finds every library, and runs its `--fixture` journey offscreen
against the transcript the package gives on the building machine. The combined
release gate runs this for every application with a scripted journey.
Hello-world is packaged but has no scripted fixture.

## Signing and distribution

- **macOS.** The script signs ad hoc, which is enough on the machine that
  built the bundle. For other machines, sign with a Developer ID with the
  hardened runtime, then notarize and staple:
  `codesign --force --options runtime --sign "Developer ID Application: ..." <Name>.app`,
  `xcrun notarytool submit <Name>.app.zip --keychain-profile <profile> --wait`,
  `xcrun stapler staple <Name>.app`.
- **Windows.** Sign the executable with `signtool sign /fd sha256 /tr <timestamp url> /td sha256 <exe>.exe`
  so SmartScreen knows its publisher. The window and taskbar icon comes from
  `App::icon` at run time. Explorer's file icon needs an `.ico` resource
  linked into the executable, which the script does not add.
- **Linux.** The tarball installs per user. A distribution package (deb,
  rpm, Flatpak) installs the same three paths system-wide: the executable, the
  desktop entry and the icon.

## Identity and settings

The application id given to `gui::application` names everything the
application keeps between runs: settings, saved window placement and the file
dialog's favorites live under `services::config_dir(app_id)`
(`$XDG_CONFIG_HOME/<id>` or `~/.config/<id>` on Linux,
`~/Library/Application Support/<id>` on macOS, `%APPDATA%\<id>` on Windows),
and `App::single_instance` claims the id on the session bus. Choose a
reverse-domain id and keep it stable across releases. Window sizes are saved
in interface units, so they survive a change of display scale.

Portable installs and tests can keep settings elsewhere with
`services::set_config_root(dir)`.

## Icon

`App::icon(icon)` (or `Session::set_icon`) gives every window of the
application one icon: the taskbar and title bar on Windows, the Dock on
macOS, `_NET_WM_ICON` on X11, and the toplevel icon on Wayland compositors
with `xdg_toplevel_icon_v1`. `AppIcon::drawn(glyph, size, background,
foreground)` makes one from a built-in icon; a decoded image works the same
way (`AppIcon { rgba, width, height }`).

Wayland shells without that protocol, such as GNOME, show the icon of the
desktop entry the application id names instead. A Linux package therefore
also installs `share/applications/<app_id>.desktop` with `Icon=<app_id>`
and the icon in the hicolor theme, as
`share/icons/hicolor/<size>x<size>/apps/<app_id>.png` (or
`scalable/apps/<app_id>.svg`), which `tools/package.sh` does.

## Notices to ship

- The embedded DejaVu fonts: their license (`licenses/dejavu-fonts.txt` in gui-gos).
- The embedded IBM Plex Mono, the terminal's font: its license (`licenses/ibm-plex-mono.txt` in gui-gos).
- SDL 3 (zlib license), through windowing-gos.
- libX11 and libwayland-client (MIT), opened at runtime on Linux.
- The Rust crates of windowing-gos and gui-engine-gos (MIT or Apache 2.0),
  linked statically; their `Cargo.lock` files list them.
- With `modules/webview`: WebKitGTK, GTK and GLib (LGPL 2.1 or later), linked
  dynamically.

`tools/package.sh` puts the font and SDL licenses and `package.json` in every
package. The manifest records the executable checksum, compiler version, project
manifest checksum, Linux linked libraries and per-distribution runtime packages.
Declared local dependency manifests are traversed to detect the WebView module
and include its WebKitGTK/GTK requirements. Missing declared dependencies fail
packaging rather than producing an incomplete manifest. [Dependencies](dependencies.md) records
each dependency's purpose and boundary.

## The release gate

`tools/release-gate.sh OUT` runs every check on the machine it runs on: on
Linux with a private session bus and X server, and on Windows or macOS with
that platform's native drivers. `--profile portable` skips the native display
tests, and `--list` prints the commands without running them. The Linux run
covers Rust formatting, Clippy and tests, four-tier parity, screenshots,
resources, documents, session cleanup, latency budgets, native rendering,
activation, platform probes, drag and drop, preferences, every example's
package and clean installs. Linux CI runs this same script, one `--group` per
parallel job, so each job's ledger covers its group.

`results.json` records every command, environment overrides, exit code, duration
and transcript checksum, toolchains and baseline Git revisions. The source hash
manifest identifies working files, including uncommitted changes. The gate fails
if sources change during its run. Each step runs in its own process group; one
still running after `GUI_RELEASE_STEP_TIMEOUT` seconds (default 1800) is
terminated and recorded with exit code 124. The `core` group starts with the gate's own
log-sealing test (`gos test tools/release-gate.gos`). Missing tools/checkouts fail preflight.

A run covers only its own platform, so `results.json` keeps
`complete_release_acceptance` false; a release needs a passing run on Linux,
Windows and macOS.

The gate packages every example with a `packaging.toml` and runs the scripted
journey of each, except hello-world, which declares `fixture = false`.
