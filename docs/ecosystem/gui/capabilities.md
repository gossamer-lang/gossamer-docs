# Capabilities

What gui-gos does today, area by area, and the limits of each. gui-gos is the
Gossamer library over the Rust engine in gui-engine-gos, which runs on
windowing-gos.

| Area | Implemented behavior | Current limits |
|---|---|---|
| Requirements | Gossamer 0.75.6+, Rust, CMake and a C compiler; windowing-gos and gui-engine-gos come in at their v0.1.0 releases | Source builds need the compatible Gossamer binding SDK; see the READMEs |
| Runtime | Multiple windows, retained state, focus, timers, bounded mailbox and built-in desktop jobs, close review | Built-in storage and providers share byte admission, cancellation and disposal rules. Opaque application models remain application-owned. See [resources](resources.md) |
| Rendering | Rust software paths, clipping, gradients, image and font rasterization | See [rendering](rendering.md) for retained scenes, budgets and GPU backend validation |
| Text | Grapheme editing, bidi, Arabic and supported Indic shaping, installed-font fallback, CBDT emoji, variable TrueType and checked offset conversions | Persistent native documents, incremental indexes, viewport geometry and checkpoint restoration are implemented. CFF2, COLR and sbix coverage and real OS IME journeys remain separate work |
| Layout/styles | Flex, grid, split, scroll, constraints, theme tokens, subtree overrides, desktop preference following and high-contrast palettes | Mixed-DPI, RTL and preference behavior requires native-platform validation |
| Controls/dialogs | Standard and choice inputs, calendars, colors, menus, toolbars, popups, preferences, wizards and an asynchronous file browser | Full control contracts and platform interaction require journey tests |
| Commands | Enabled/visible/checked state, scopes, multi-stroke shortcuts, conflict queries and palette entries | Only macOS has a native menu bar; elsewhere menus are drawn in the window |
| Models/tabs | Virtual collections, retained tab pages, state transfer, tear-off/merge and docking (splits, tab groups, edge/center placement, floating windows, versioned layouts) | Document checkpoints preserve tab/window metadata and edit state; mixed-DPI docking is verified offscreen, not on mixed hardware |
| Desktop | Installed-application catalogs, notification/tray/drag effects and platform preference readers | Single-instance forwarding uses Linux D-Bus or per-user locks and acknowledged loopback on Windows/macOS. Windows and macOS behavior is tested in their CI jobs |
| Accessibility | Semantic trees, text geometry and AT-SPI/UIA/NSAccessibility adapters | Real Orca/Narrator/VoiceOver journeys are not established by offscreen tests |
| Examples | Hello world, widgets showcase, code editor, launcher, rich editor, terminal, docking, printing, charts, scene editor, image viewer and media player | Hello world has build checks; the other applications have fixture journeys on all four tiers |
| Optional webview | Linux WebKitGTK adapter | Page composition/accessibility, other platforms and distribution are unverified |
| Modules | Custom widgets, drawing descriptions, rich documents, terminal, docking, printing/PDF, charts, scene canvas, image viewer and media player; see [modules](modules.md) | Terminal, printing and media are verified on Linux only: ConPTY, GDI printing, macOS CUPS/PTYs and GStreamer on Windows/macOS have not run natively. Animation timelines are not implemented |

[Architecture](architecture.md), [testing](testing.md) and
[performance](performance.md) describe the design and how it is tested.
Tests run offscreen and cross-compiled cannot prove native input methods,
desktop portals, screen readers or mixed-DPI hardware; those need real
desktops.
