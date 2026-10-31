# Text editing contracts

`editing::EditState` is the one editable-text controller. Every `TextInput`
kind (line, area, password, search), editable combos and the code editor's
line editing use it. It holds the edited text, the application's last value,
anchor and caret, input-method preedit, undo and redo history, and a revision
that increments on each committed change.

The toolkit core edits and lays out text; gui-gos reads a widget's state back
with `Session::edit_state`. `TextLayout`, its visual caret order and its range
geometry below are the Rust core's (`gui_engine::text` in gui-engine-gos),
where accessibility and painting use them.

## Offsets

Positions in `EditState`, `TextLayout`, syntax spans and selections are UTF-8
byte offsets. An editing position always lies on an extended grapheme cluster
boundary. Every range is half-open.

`text::offsets` gives each other unit its own type, so one unit cannot be passed
as another:

| Type | Unit | Who uses it |
|---|---|---|
| `ByteOffset` | UTF-8 bytes | `String` slicing, layout, editing state |
| `ScalarIndex` | Unicode scalar values | SDL text-editing cursor, AT-SPI text offsets, `s.len()`, `s[i]` |
| `Utf16Offset` | UTF-16 code units | Windows UI Automation and TSF, macOS `NSString` ranges |
| `GraphemeIndex` | Extended grapheme clusters | User-visible character counts, max-length policies |
| `LinePosition` | Logical line, byte column | Editor line and column, `LineIndex` |
| `VisualPosition` | Layout line, caret slot from the left | Bidi-aware caret placement |

A conversion answers `Result<_, OffsetError>` and never rounds to a nearby
position. It fails with `OutOfRange` (negative or past the end, in the unit
given), `InsideScalar` (inside a UTF-8 sequence), `InsideSurrogatePair`,
`InsideGrapheme`, `LineOutOfRange`, `Reversed` (a range ending before it starts)
or `NotLaidOut` (a position cut off by elision). `ByteRange` checks both ends
and converts whole ranges to and from scalars and UTF-16.

`LineIndex` records line starts for one text revision and converts byte offsets
to line and column, and back, in logarithmic time. Lines split at `\n` only; a
`\r` stays line content. The `\n` itself is the end of its line. A column may
reach the line's end but not pass it. A text ending in `\n`, and an empty
text, end with an empty line.

`visual_position` and `byte_of_visual` number the caret slots of one laid-out
line from left to right, the order `TextLayout::visual_carets` reports. A
soft-wrap boundary belongs to the later line.

The SDL text-editing cursor arrives as a `ScalarIndex` into the preedit.
`EditState::compose` converts it with `byte_of_scalar`. A cursor outside the
preedit, including SDL's -1 for "not set", places the caret after the preedit.

## Editing

- `sync` adopts the application's value when it changed outside the
  controller. It clamps anchor and caret to the new text, snaps them to grapheme
  boundaries and drops any preedit. A value the controller produced itself is
  not an external change.
- `replace_selection` is one transaction. A nonzero `max_graphemes` bounds the
  result, truncating the inserted text. Replacing an empty selection with
  nothing answers false and changes neither the revision nor the history.
- Backspace and Delete remove whole graphemes, including combining and emoji
  ZWJ sequences, or whole words with the word modifier.
- `step` moves in logical order; `visual_step` follows display order across
  bidi runs; `vertical` keeps a goal column across consecutive moves.
- Undo restores both text and selection, and a new edit clears redo. History
  keeps at most `UNDO_LIMIT` (200) entries. Consecutive insertions, or
  deletions, merge into one entry while the pauses between them stay under
  `GROUP_PAUSE` (1000 ms). A space, a newline, a paste and a cut each start
  their own entry. Paste in a single-line control turns newlines into spaces.
- `compose` keeps the preedit outside the committed text. `display` splices it
  in at the caret for drawing and reports its byte range. `insert` commits once
  and clears the preedit.

Each history entry is a whole-string snapshot. This is small-document storage,
not the piece table or rope with 10 MiB document fixtures that the editor plan
calls for.

## Selection from the application

A text input reports every selection change as `UiMsg::Caret(id, anchor, caret)`
in UTF-8 bytes, after any `UiMsg::Text` for the same event. `Effect::SelectText`
selects a byte range of a named input and scrolls the caret into view; offsets
inside a grapheme move to its start. `Effect::ReplaceText` replaces a byte range
as one undoable edit, leaving the caret after the new text; read-only inputs
ignore it. Neither effect moves keyboard focus.

## Find and replace

`editing::search::find_all` answers the non-overlapping matches of a query as
byte ranges on grapheme boundaries, so "e" never matches inside "e" plus a
combining accent. Matching folds case unless `match_case`, comparing the
folded text as a whole, so a character that folds to several (`İ` to `i` plus
a combining dot) still matches; `whole_word` accepts only matches whose ends
are word boundaries. `step` picks the next or previous
match from a selection, wrapping at either end, and `replace_all` rewrites
every match.

`FindBar` is the bar's model and view. The application folds bar messages
through `FindBar::update`, which answers a `FindRequest` (search, next,
previous, replace, replace all, close). Its toggles choose case, whole words
and regular expressions, shown compactly as "Aa", "W" and ".*" with their full
names as tooltips and accessible names, and `found(count, current)` shows how many
matches there are and which is selected. Replace changes the selection only when
it is exactly a match; otherwise it selects the next match first. The code
editor replaces all matches in one `ReplaceText` edit, so one undo restores
them, and gives focus back to the document when the bar closes.

`dialogs::request::go_to_line` asks for "line" or "line:column", both from 1,
and validates the line against the document; `parse_location` reads the answer.
The editor counts columns in graphemes and clamps a column past the line end.

## Saving

`services::write_atomic` writes the bytes to a sibling `<file>.tmp-<pid>`,
retrying short writes, flushes it with `sync_all`, renames it over the
destination and then syncs the parent directory. A crash leaves either the old
or the new contents. On failure the temporary file is removed and the error
names the step that failed. On Windows the directory sync is satisfied by NTFS
metadata ordering and flushes nothing. The code editor saves through it from
its worker goroutine. The editor does not detect a concurrent writer, and a
symlink destination is replaced by a regular file rather than written through.
No durability guarantee is claimed on untested filesystems or platforms.

## Visual range geometry

`TextLayout::range_rects(from, to, x, y)` answers pixel rectangles for a UTF-8
byte range in window coordinates. Pass the layout's actual drawing origin,
including the input's padding and scroll offset. Layout already includes the
font and display scale; the query applies no further scale. This API is for
accessibility geometry and does not change selection painting.

Rectangles remain separate at visual-line and resolved bidi-level boundaries,
even when their edges touch. Bounds round outward. Reversed ranges are
normalized, out-of-document offsets clamp, and partial graphemes expand to the
whole grapheme. Ligature advances are divided at grapheme boundaries. A real
newline contributes its one-pixel caret box; a soft wrap contributes no newline
box. A collapsed range answers its caret box. Only laid-out content has glyph
boxes, so an elided layout cannot describe hidden text. Callers performing
strict offset validation can use `text::offsets` before querying geometry.
