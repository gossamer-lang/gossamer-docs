# Theming

Widgets paint from a `Theme`, never from literals: colors, type, sizes,
shadows, timings and icons are tokens, so a palette swap, a density change,
200% text or an application's own look reaches every control.

## Palettes

`ThemeKind` picks the colors: `Light`, `Dark`, `HighContrastLight` and
`HighContrastDark`. Each names its tokens by role (`background`, `surface`,
`field`, `text`, `text_muted`, `accent`, `selection`, `selection_inactive`,
`danger`, `border`, `focus`, `link`, ...); the high-contrast palettes keep
every text pair above 7:1 and double border widths.

A session follows the desktop until the application decides otherwise:

- its light or dark setting and its high-contrast setting pick the palette,
  and its accent color becomes the accent and selection of the light and
  dark palettes (deepened until checkboxes and selected rows show against
  the background, with black or white text, whichever reads better);
- its reduced-motion setting and its text size apply to every window.

Each comes from `windowing::system::preferences()` where the platform states
it (the XDG settings portal on Linux, system parameters and DWM colors on
Windows, the workspace's accessibility options on macOS), and changes arrive
as `PreferencesChanged` or `ThemeChanged`, repainting every window. Sessions
under `gos test` keep the defaults on every desktop.

- `Effect::SetTheme(kind)` switches every window and stops following the
  desktop's palette and accent; `Effect::FollowSystemTheme` follows them again.
- `Effect::SetTextScale` and `Effect::SetReducedMotion` set those for every
  window, and the desktop's no longer apply.
- `Effect::SetDensity` (`Compact`, `Normal`, `Comfortable`) and `SetRtl` keep
  the palette and the tokens below.
- `Effect::SetDisplayScale(Some(scale))` draws every window as if its display
  had that scale (previews, mixed-DPI checks); `None` follows each display
  again. The showcase's Navigation page switches theme, density, display
  scale and text size live.

The inspector (`gui.inspector`, Primary+Shift+I) shows, beside the window,
its focus, hover path, capture, popups and dialogs, why it was last laid out
again, the theme and tokens in use, the widget hierarchy with each widget's
position and size, the focus chain, the commands with their shortcuts,
scopes and enabled state, the accessibility tree, cache counters and the
recent input log.

## Tokens

`ThemeTokens` holds what is not color. A palette change keeps it.

- `typography`: one `Typeface` (size in interface units, bold, mono) per
  `TextRole` (`Body`, `Small`, `Caption`, `Label`, `Heading`, `Title`,
  `Hero`, `Mono`). `theme.font(role)` applies the display scale and the text
  scale.
- `shape`: corner `radius`, `control_height` and `row_height` (density
  adjusts them), checkbox `indicator`, spacing step `space`, `border` and
  `focus` widths, icon sizes by role (`icon` for buttons and list items,
  `field_icon` for field chevrons and steppers, `small_icon` for tabs,
  headers, tree rows and menu arrows, `close_icon`, `grid_icon`), and the
  `tooltip_elevation`, `popup_elevation` and `dialog_elevation` shadows.
  Controls reserve space from the same tokens they draw with, so a larger
  icon widens its button rather than overlapping the label.
- `motion`: `caret_blink`, `double_click` and `tooltip_delay` in
  milliseconds. `reduced_motion` on the theme stops animation (progress
  stripes, spinners); toasts appear and leave without motion.
- `icons`: the registered icon set to draw from (below), or "".

```gossamer
use gui

let mut tokens = gui::ThemeTokens::standard()
tokens.shape.radius = 12
tokens.typography.body.size = 20.0
tokens.motion.tooltip_delay = 300
gui::perform(gui::Effect::SetThemeTokens(tokens))
```

`ThemeTokens::standard()` is the default look; its values are the ones the
screenshot goldens are drawn with.

## Subtrees

`Widget::themed(ThemeOverride { kind, density, rtl, text_scale, tokens })`
changes the theme below one widget: a dark sidebar, a compact toolbar, a
right-to-left preview or a branded panel. Unset fields keep the window's.

## Icon sets

Icons are `gui::Icon` values: the 60 built-in ones (`Icon::Check`,
`Icon::Search`, ... in `render::icons::BUILT_IN`), drawn on a 24-unit grid, and
`Icon::Custom(name)` for an application's own. An application draws icons on
the same grid into a set, and names the set in its tokens:

```gossamer
use gui::Icon
use gui::render::icons
use gui::render::vector::Path

let mut tick = Path::new()
tick.move_to(5.0, 12.5)
tick.line_to(10.0, 17.5)
tick.line_to(19.0, 7.0)
icons::register("brand", Icon::Check, icons::IconArt { fill: Path::new(), stroke: tick })
icons::register("brand", Icon::Custom("mascot"), icons::IconArt { fill: tick, stroke: Path::new() })
```

A theme whose `icons` is `"brand"` draws the set's check mark wherever a
control asks for `Icon::Check`, and the built-in icon for
every one the set lacks; a custom icon no set has draws as a neutral box.
`Icon::named(text)` reads a built-in icon's name from data. `fill` is filled even-odd and `stroke` is stroked 2 units wide,
as the built-in icons are.
