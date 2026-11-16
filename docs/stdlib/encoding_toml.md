# `std::encoding::toml`

Status: experimental

TOML 1.0 parsing and emission over `json::Value`, and typed `toml::decode::<T>` / `toml::encode::<T>`.

## Items

| Item | Signature | Description |
|---|---|---|
| `parse` | `fn parse(source: String) -> Result<json::Value, errors::Error>` | Parses a TOML document into a `json::Value`, its tables by key. |
| `encode` | `fn encode<T>(value: T, sort: bool = false) -> Result<String, errors::Error>` | Encodes a value whose top level is a table as a TOML document, answering `Result<String, errors::Error>`: a struct's members in declaration order (by key with `sort: true`) with an `Option` member that is `None` left out, a `json::Value` object's and a `Map`'s keys sorted. `toml::encode::<T>(v)` names the type. |
| `decode` | `fn decode<T>(source: String) -> Result<T, errors::Error>` | `toml::decode::<T>(text)` decodes a TOML document into any type with a JSON form, as `json::decode::<T>` decodes JSON. |
| `to_json_text` | `fn to_json_text(source: String) -> Result<String, errors::Error>` | Converts a TOML document to JSON text, each table's members by key. |
| `from_json_text` | `fn from_json_text(source: String) -> Result<String, errors::Error>` | Converts JSON text to a TOML document, each object's members by key; the top level must be an object. |
| `is_valid` | `fn is_valid(source: String) -> bool` | Reports whether the text is a well-formed TOML document. |
| `pretty` | `fn pretty(source: String) -> Result<String, errors::Error>` | Rewrites a TOML document in the pretty-printer's layout. |

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->

## Usage

`toml::decode::<T>(text)` and `toml::encode(value)` are the typed codecs,
with the same attributes, member order, and `sort: true` as
`json::decode` / `json::encode`. TOML has no null: a struct member that
is an `Option` holding `None` is left out, and a `null` anywhere else,
or an integer past `i64::MAX`, is an `Err`. The top level of a document
is always a table.

```gossamer
use std::encoding::{json, toml}
use std::errors

struct Database {
    url: String
    pool: i64
}

struct Config {
    name: String
    owner: Option<String>
    database: Database
}

fn main() -> Result<(), errors::Error> {
    let config = toml::decode::<Config>("name = \"billing\"\n[database]\nurl = \"pg://db\"\npool = 16\n")?
    print(toml::encode(config)?)                 // owner is None, so it is left out
    let doc = toml::parse("b = 1\na = [true]\n")?
    println(f"{json::keys(doc)}")
    Ok(())
}
```

`toml::parse` answers a `json::Value` and `toml::encode` of one writes
it back; `toml::to_json_text` and `toml::from_json_text` convert text
directly, each table's members by key.
