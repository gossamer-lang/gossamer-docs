# Custom widgets

Most interfaces compose the built-in widgets. When something needs its own
drawing and input (a chart, a canvas, a game board, an embedded document),
`Widget::custom` takes a `Custom`, built by `Custom::new`:

```gossamer
use gui
use gui::{UiMsg, Widget}

fn meter(id: String, level: f64) -> Widget {
    let mut c = gui::Custom::new(
        id,
        gui::Role::Slider,
        f"Level {(level * 100.0) as i64}%",
        |c, t| c.constrain(gui::geometry::Size::new(t.px(200), t.px(24))),
        |size, t| #[
            gui::DrawOp::RoundRect { rect: gui::geometry::Rect::from_size(size), radius: t.px(4), color: t.surface_alt }
            gui::DrawOp::RoundRect { rect: gui::geometry::Rect::new(0, 0, (size.width as f64 * level) as i64, size.height), radius: t.px(4), color: t.accent }
        ],
        |i| match i {
            gui::CustomInput::Press { x, .. } | gui::CustomInput::Drag { x, .. } => #[UiMsg::Custom(id, f"{x}")]
            _ => #[]
        },
    )
    c.focusable = true
    Widget::custom(c)
}
```

`Custom::new` registers the three functions with the toolkit, which calls
them from its own layout, paint and event code, and stores their ids in the
widget; `focusable` and `captures_input` start `false`. A view rebuilds its
custom widgets each time, and a window's registrations are released two of
its views later.

## The contract

- `measure(constraints, theme)` answers the natural size in pixels. Use
  `theme.px(units)` to scale interface units for the display, and stay inside
  the constraints (`c.constrain`).
- `draw(size, theme)` answers draw operations in local pixels: rectangles,
  rounded rectangles and strokes, lines, circles, filled and stroked paths,
  text with a `TextStyle`, RGBA images, clipping and opacity groups. Colors
  come from the theme (`t.text`, `t.surface`, `t.accent`, `t.border`, ...),
  so the widget follows light, dark and high-contrast themes.
- `input(event)` receives `CustomInput` in local pixels and answers the
  messages to emit: `Press` (with button, click count and modifiers), `Drag`
  (moved with a button held), `Hover`, `Release`, `Leave`, `Wheel` (with
  position and modifiers), `KeyPress`, `KeyRelease`, committed `Text`, and
  `Focus`. A press focuses the widget when it is `focusable` and captures the
  pointer until the release.
- An input that emits messages is consumed. With `captures_input` every event
  the widget receives is consumed, even with nothing to emit, so keys such as
  Tab and shortcuts reach it instead of focus traversal and the command
  registry; use it only for embedded documents.
- `role` and `label` describe the widget to assistive technology (see
  [accessibility](accessibility.md)).

The functions run on the UI thread at layout, paint and event time; keep them
quick and free of side effects other than the messages they answer. State
belongs in the application's model: the view rebuilds the widget from it on
every update.

## Dragging content out

`.drag_source(id, items, operation)` on any widget lets the pointer drag
`items` (each a MIME type and bytes) to other applications. A press and a move
of a few units start the platform drag, answered by
`UiMsg::DragFinished(id, operation)`; the operation is `None` when the drop
went nowhere or the platform has no drag source (X11 only, for now).
Collections offer rows through `Collection::drag`, and text inputs drag their
selected text on their own.
