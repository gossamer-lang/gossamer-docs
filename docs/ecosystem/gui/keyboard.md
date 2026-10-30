# Keyboard

## How a key press travels

The session offers each key press, in order, to:

1. The topmost popup that takes keys (menus, select lists, pickers). Escape
   closes it when it does not handle the key itself.
2. The focused widget, then its ancestors. A text field handles its editing
   keys here, so they never reach the shortcut table.
3. The command registry: the window's shortcuts, scoped commands first (see
   below). Pressing a disabled command's shortcut does nothing.
4. Focus traversal and dismissal: Tab and Shift+Tab move focus; F6 and
   Shift+F6 move it between the window's content and its modeless dialogs;
   Escape closes the top popup or cancels the dialog holding focus (else the
   modal one); Enter accepts that dialog's default button; the Menu key or Shift+F10 asks the focused widget for its context
   menu; F10 and Alt plus a mnemonic open the menu bar.

Holding Alt underlines menu mnemonics. Moving focus with the keyboard shows
the focus ring, which pointer input hides again.

## Shortcuts

Commands declare shortcuts as text: `Primary+S`, `Primary+Shift+P`,
`Alt+Left`, `F5`. `Primary` is Cmd on macOS and Ctrl elsewhere; `Ctrl`, `Alt`
(or `Option`), `Shift` and `Super` (`Cmd`, `Win`) name a modifier exactly. A
space separates the strokes of a chord: `Ctrl+K Ctrl+C` fires after both
strokes in turn, and a pending chord takes the next key. A command can carry
several shortcuts (`.key("Primary+Shift+Z").key("Primary+Y")`).

A command with `in_scope(key)` is active only while focus is inside the widget
with that key or id, and wins over a window-level command with the same
shortcut. `CommandTable::conflicts` lists shortcuts that two active commands
share. The command palette (Primary+Shift+P) lists every visible command with
its category and shortcut.

Built-in commands:

| Command | Shortcut |
|---|---|
| `edit.undo`, `edit.redo` | Primary+Z; Primary+Shift+Z or Primary+Y |
| `edit.cut`, `edit.copy`, `edit.paste` | Primary+X, Primary+C, Primary+V |
| `edit.select-all` | Primary+A |
| `gui.command-palette` | Primary+Shift+P |
| `gui.inspector` | Primary+Shift+I |
| `gui.quit` | Primary+Q |
| `gui.tab.new`, `gui.tab.close`, `gui.tab.reopen` | Primary+T, Primary+W or Primary+F4, Primary+Shift+T |
| `gui.tab.next`, `gui.tab.previous` | Ctrl+Tab or Ctrl+PageDown; Ctrl+Shift+Tab or Ctrl+PageUp |
| `gui.tab.move-left`, `gui.tab.move-right` | Ctrl+Shift+PageUp, Ctrl+Shift+PageDown |

An application's command with the same id replaces the built-in one.

## Text fields and areas

| Keys | Effect |
|---|---|
| Left, Right | One grapheme, in display order across bidi runs |
| Ctrl+Left, Ctrl+Right (Alt on macOS) | One word |
| Up, Down, PageUp, PageDown | Lines in a text area; Down opens completion in a field that has it |
| Home, End | The visual line's edges; with Primary, or in a one-line field, the text's |
| Shift with any of these | Extends the selection |
| Backspace, Delete | A grapheme; with Ctrl (Alt on macOS) a word |
| Enter | Submits a one-line field (`UiMsg::Submit`); a new line in an area |
| Tab | Moves focus, unless the input inserts tabs or a completion accepts with Tab |
| Escape | Closes the completion list |

Text is typed through committed text events, never synthesized from key
presses, so input methods and dead keys work. While an input method is
composing, the keys it uses stay with it.

## Buttons and choices

A button runs on Enter as the key goes down (auto-repeat does not run it
again) and on Space as the key comes up; moving focus away while Space is
held cancels it. Checkboxes and switches change on Space as it comes up. With
the pointer, a control acts on a release over the place it was pressed: a
press dragged off and released elsewhere does nothing, and so does a release
over a control the press did not start on. Radio groups and segmented
controls move their choice with the arrows (Left and Right swap in
right-to-left layouts), skip disabled options and wrap at the ends; choosing
the option already chosen reports nothing. A menu button opens its menu on
Enter, Space or Down, a split button on Down or a press on its arrow part
(Enter and Space run its main action), and a press on either while its menu is
open closes the menu; so does a press on a select whose list is open. A
disclosure header opens and closes its section with Enter or Space. A banner's
buttons (its actions, then Dismiss) are reached with Left and Right and run
with Enter or Space; Escape or Delete dismisses it. A toolbar is one Tab stop:
Tab enters it at the control it last had focused (the first, at the start),
Left and Right move between its controls (swapped in right-to-left layouts),
and the next Tab leaves it. A control that uses the arrows itself, such as a
text field, keeps them.

## Lists, menus and dialogs

Lists, tables and grids move their selection with the arrows, Home, End,
PageUp and PageDown, extend it with Shift, and activate with Enter; typing
letters jumps to a matching row. A select list opens with Alt+Down, F4,
Space or Enter; closed, the arrows change the choice directly (with nothing
chosen, Down takes the first item and Up the last), and typing letters selects
a matching item. Escape closes an open list without changing the choice. A
strict editable combo left with text that is not one of its items goes back to
the last item it held. Open menus move with the arrows, open submenus with Right,
close them with Left or Escape (Left and Right swap in right-to-left
layouts), and run the highlighted item with Enter or Space. In a dialog, Enter activates the default button and
Escape the cancel button.
