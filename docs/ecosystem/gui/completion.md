# Completion

One completion controller serves every control that proposes values: text
fields and areas, editable combos, autocomplete fields, the code editor and the
command palette. A `TextInput` gets proposals by setting `completion`:

<!-- fragment -->
```gossamer
let mut field = gui::TextInput::new("city", m.city, "City", gui::InputKind::Line)
field.completion = Some(gui::Completion::local(cities, gui::MatchMode::Prefix))
```

## Sources

| Source | Built with | Answers |
|---|---|---|
| A fixed list | `Completion::local(items, mode)` | Inside the widget, as the text changes |
| A function | `Completion::provider(|query| items)` | Synchronously, inside the widget |
| The application | `Completion::asynchronous(debounce_ms)` | Later, through messages |

`MatchMode` decides how a local list matches: `Prefix`, `Substring`, or
`Fuzzy` (the query's characters in order, not necessarily adjacent). Matching
compares case-folded text (`text::folding`); an item's `matches` are byte
ranges of its original label, widened to whole characters, which the list
highlights.

For an asynchronous source the widget waits `debounce_ms` after typing stops,
then emits `UiMsg::CompletionRequest(id, request, query, revision)`. The
application answers with `Effect::Complete(id, request, items, error)`, from
`update` or after work on a worker goroutine. Results for anything but the
latest request, for a text revision the field has moved past, or for a widget
that has gone away, are dropped, even when the provider ignored cancellation.
While a request is out, the list shows a loading row and no earlier query's
items, so Enter cannot accept a result for other text. An error shows in the
list in place of items; Enter asks again with the same query. Accepting a
proposal cancels any request still out.

## Items

`CompletionItem::new(key, label)` makes an item; `with_detail` adds a
description (bounded to `DOC_LIMIT` characters). `insert` sets the text
accepted in place of the label; `icon`, `category`, `disabled` and `score`
affect presentation and ranking. Keys are stable: the highlight follows an
item's key as results change, never its row. Ranking is deterministic: score,
then label, then key.

## Behavior

- Proposals appear once `min_chars` characters are typed (default 1), at most
  `limit` of them (default 200).
- Enter or a click accepts; Tab accepts only with `accept_tab`; Escape closes
  the list without touching the typed text; leaving the field never accepts.
- With `word`, acceptance replaces only the word at the caret (editors);
  otherwise it replaces the whole text.
- With `ghost`, the top proposal's remainder shows as uncommitted text.
- No requests run while an input method is composing.

The code editor feeds `Completion::local` from its document's words plus the
language keywords, with `word` set and `min_chars` 2.
