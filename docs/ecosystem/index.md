# Ecosystem

Libraries built for Gossamer that live outside the standard library. Each
is its own package with its own release, and each page here is that
package's documentation.

## Desktop applications

Three packages stack to build native desktop programs:

| Package | Import | What it is |
|---|---|---|
| [GUI](gui/index.md) (`gui-gos`) | `use gui` | The toolkit applications use: an Elm-style application loop, widgets, commands, dialogs, themes, localization, accessibility, and modules for a terminal, docking, printing, charts, a scene canvas, an image viewer and a media player. |
| [GUI engine](gui-engine/index.md) (`gui-engine-gos`) | `use gui_engine` | The toolkit's engine, written in Rust: layout, text shaping, painting, the widget state and the platform services `gui` calls. Applications reach it through `gui`. |
| [Windowing](windowing/index.md) (`windowing-gos`) | `use windowing` | Native windows, input, the event loop and desktop services over SDL 3. It is usable on its own by programs that draw for themselves. |

An application depends on `gui`; `gui` brings in the engine and windowing.
A program that only needs windows and input depends on `windowing` alone.
[GUI libraries](gui-libraries/index.md) diagrams how the packages, their
Rust cores, SDL 3 and the Gossamer toolchain fit together.
