# Accessibility

Every window mirrors its widget tree into a semantic tree of `AccessNode`s:
role, name, description, value, states (focused, disabled, checked, selected,
expanded, pressed, read-only, required, invalid, modal), position in a set,
bounds in window pixels and the actions a node accepts. The tree is built from
the widgets, not from what they paint, so a control is announced the same in
every theme and scale. Platform bridges export it; tests read it as text.

## What an application provides

Built-in controls name themselves from their labels. Where a widget has no
visible text, or the visible text is not the right name, set it:

<!-- fragment -->
```gossamer
Widget::tool_button("browser.reload", Icon::Refresh, "Reload")        // icon button named "Reload"
Widget::image(pixels, 48, 48, "Profile photo")                        // alt text
Widget::text_field("q", m.q, "Search").described("Searches all notes")
Widget::column(rows, 4).role(gui::Role::Group).accessible("Recent files")
```

`accessible` sets the name, `described` the description, and `role` the role
of a decorated subtree. A `Custom` widget declares its own `role` and `label`.
`Effect::Announce(text)` speaks a status message through assistive technology
without moving focus, for results that appear away from the focus (a save
finished, a search found nothing). Toasts and dialogs announce themselves the
same way. Assistive technology hears at most one announcement every 750 ms: a
repeat of what was just said is dropped, and a burst keeps its newest three,
spoken in order, so status chatter never buries speech for focus and caret
moves. `Session::spoken()` answers what was actually said.

Keep controls reachable by keyboard (see [keyboard](keyboard.md)): every
focusable control is in the Tab order, and a modal dialog keeps focus inside
itself.

Dialogs open window-modal (`Effect::OpenDialog`), or with a `Modality` through
`Effect::OpenDialogWith(window, request, modality)`: `Application` blocks
every window of the application until it closes, and `Modeless` blocks
nothing, so its window keeps working and F6 moves between them. Modal dialogs
carry the `modal` state. Warnings, errors and questions with a destructive
answer are `alertdialog`s, described by their message and announced with it.

## Inspecting the tree

`Session::semantics(w)` answers a window's root node and `dump()` its text form,
one node per line with role, name, value and states:

```text
window "Hello"
  textfield "Name" = "Ada" [focused]
  button "Say hello"
  label "Hello, Ada!" [readonly]
```

Tests assert on this dump, and drive the actions assistive technology
would with `Session::accessible_action(owner, target, action, value)`: pressing
a select's list item chooses it, pressing a picker token removes it. A
collection or an open select exposes only the rows it shows, each with its
position in the whole set (`9/100000`). The inspector (Primary+Shift+I) shows the widget
hierarchy and stored state beside the window, not the semantic tree.

## Platforms

On Linux the session exports the tree to the AT-SPI accessibility bus, so Orca
and other assistive technology read it, and routes their actions (press,
set text, replace text, select text) back to the widget on the UI thread.
`Session::accessibility_status()` says whether the bridge connected. The bridge
stays off under the offscreen and dummy video drivers, or with
`GUI_ACCESSIBILITY=off`; `GUI_ACCESSIBILITY=on` forces it on.

On Windows and macOS windowing's providers answer the screen reader
(`windowing::access`): UI Automation, where each element is a COM provider
with the control patterns its state calls for (Invoke, Toggle, Value,
RangeValue, ExpandCollapse, SelectionItem), and NSAccessibility, where each
element is an `NSAccessibilityElement` reached from the window's content view.
After each frame the session hands them the same published tree AT-SPI uses,
as a flat list (`accessibility::native`), and their requests come back as the
same actions: press, toggle, select, focus, set text and set value. Focus
moves, value and state changes and announcements reach Narrator and VoiceOver
as their events. The providers start answering when a client first asks for a
window, and the session then describes every window. Element frames follow
the window when it moves.

Under Wine 9, a UI Automation client in another process reads a
gui-gos window's whole tree (window, menu bar, menu items, heading, label,
edit field, button, status) with their names and control types. Wine's client
cannot yet call control patterns, so `windowing-gos/tests/uia` (a client that
presses, toggles and sets every control and reads the results back) and the
macOS in-process NSAccessibility check (`--self-check`) run in windowing's CI
on real Windows and macOS runners. Screen-reader journeys with Narrator and
VoiceOver have not been run yet; see [capabilities](capabilities.md).
