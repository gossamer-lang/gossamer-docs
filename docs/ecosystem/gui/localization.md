# Localization

Every string the toolkit shows or announces passes through the installed
catalog: dialog titles, buttons and messages, field labels, placeholders,
validation errors, accessible names and descriptions, announcements and tab
menus. Applications translate their own strings the same way.

## Catalogs

A `localization::Catalog` holds a `locale` (`de-DE`, `ar`, `pt_BR`) and its
messages, each keyed by a context and the English source text, with one form
per plural category (`one`, `few`, `many`, `other`, ...):

<!-- fragment -->
```gossamer
use gui::localization

let label = localization::tr("Cancel")
let summary = localization::message("files", "{count} files in {folder}", n, { "folder": name })
```

`{name}` placeholders are filled in one pass, so translated text and the
values put into it are never read as more placeholders. `{count}` is the
count. `plural(locale, count)` picks the CLDR category for the shipped locale
families (Arabic, Russian and Ukrainian, French, East Asian, and one/other).

The installed catalog lives in the toolkit core, which translates its own
strings from it; `localization::install`, `locale`, `rtl`, `tr` and `message`
reach that one catalog, so the application and the toolkit always speak the
same language. Number and date formatting runs in the Rust toolkit from the installed
locale.

`Effect::SetLocale(catalog)` installs a catalog while the program runs: every
window and open dialog is built again in the new language, and right-to-left
languages (Arabic, Hebrew, Persian, Urdu) mirror the layout.

## Numbers, dates and times

`localization::conventions(locale)` says how a locale writes numbers and
dates: decimal and group separators, day/month/year order and separator, and
12- or 24-hour time. With the installed catalog's locale:

| Call | `en-US` | `de-DE` | `fr` | `ja` |
|---|---|---|---|---|
| `format_number(1234.5, 1)` | 1,234.5 | 1.234,5 | 1 234,5 | 1,234.5 |
| `format_date(2026, 3, 7)` | 03/07/2026 | 07.03.2026 | 07/03/2026 | 2026/03/07 |
| `format_time(14, 5)` | 2:05 PM | 14:05 | 14:05 | 14:05 |

`parse_number(text)` reads what people type: the locale's decimal separator
makes group separators and spaces ignorable; without it a group separator
counts only between groups of three digits (`1,234`), and any other `.` or
`,` is the decimal point (`1,5` is 1.5 in English). Spin boxes show and read
numbers this way, the file browser writes sizes with it, and calendars name
the month (`month_name`). Locales outside the table write English numbers and
ISO dates.

## Checking coverage

The pseudo-locale `qps-ploc` (`localization::PSEUDO_LOCALE`) brackets every
translated string. With it installed, any unbracketed text on screen came
from somewhere that skipped the catalog; the toolkit's own tests open every
dialog and a gallery of controls this way and fail on any such string.
