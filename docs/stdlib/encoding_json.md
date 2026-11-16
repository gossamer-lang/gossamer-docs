# `std::encoding::json`

Status: experimental

JSON parser, emitter, and derive support.

## Items

| Item | Signature | Description |
|---|---|---|
| `Serialize` | `trait Serialize` | Trait for converting a value to JSON. |
| `Deserialize` | `trait Deserialize` | Trait for parsing a value from JSON. |
| `encode` | `fn encode<T>(value: T, sort: bool = false) -> Result<String, errors::Error>` | Encodes a value as compact JSON text, answering `Result<String, errors::Error>`: a struct's members in declaration order under their serde keys, or by key with `sort: true` (`json::encode(v, sort: true)?`); a `json::Value` object's and a `Map`'s keys sorted. `json::encode::<T>(v)` names the type. |
| `decode` | `fn decode<T>(source: String) -> Result<T, errors::Error>` | `json::decode::<T>(text)` decodes JSON text into any type with a JSON form (a struct or enum, generic ones included, a collection, an `Option`, a tuple, a scalar), ignoring members it does not declare; a failure names the path to the value and what it found. |
| `to_value` | `fn to_value<T>(value: T, sort: bool = false) -> Result<json::Value, errors::Error>` | Encodes a value as the `json::Value` its JSON text reads as, answering `Result<json::Value, errors::Error>`, the counterpart of `from_value`. |
| `from_value` | `fn from_value<T>(value: json::Value) -> Result<T, errors::Error>` | `json::from_value::<T>(value)` decodes a `json::Value` as `json::decode::<T>` decodes text, for a subtree a program navigated to. |
| `Value` | `type Value` | Dynamically typed JSON value. |
| `Error` | `type Error` | Error raised by encoding/decoding operations. |
| `parse` | `fn parse(source: String) -> Result<json::Value, errors::Error>` | Parses JSON text into a dynamic Value. |
| `encode_pretty` | `fn encode_pretty<T>(value: T, sort: bool = false) -> Result<String, errors::Error>` | Encodes a value as indented JSON text, answering `Result<String, errors::Error>`, members in the order `encode` writes them (`sort: true` orders a struct's members by key). |
| `is_valid` | `fn is_valid(source: String) -> bool` | Reports whether the text is well-formed JSON. |
| `get` | `fn get(value: json::Value, key: String) -> Option<json::Value>` | Looks up an object field on a dynamic Value. |
| `set` | `fn set(value: json::Value, key: String, next: json::Value) -> json::Value` | Sets an object field on a dynamic Value. |
| `at` | `fn at(value: json::Value, index: i64) -> Option<json::Value>` | The element at an index of an array; None past the end and for a value that is not an array. |
| `keys` | `fn keys(value: json::Value) -> Option<Vec<String>>` | Object field names of a dynamic Value. |
| `len` | `fn len(value: json::Value) -> Option<i64>` | The element count of an array or the member count of an object; None for any other value. |
| `is_null` | `fn is_null(value: json::Value) -> bool` | Reports whether a dynamic Value is null. |
| `as_str` | `fn as_str(value: json::Value) -> Option<String>` | Reads a dynamic Value as Option<String>. |
| `as_i64` | `fn as_i64(value: json::Value) -> Option<i64>` | Reads a dynamic Value as Option<i64>. |
| `as_u64` | `fn as_u64(value: json::Value) -> Option<u64>` | Reads a dynamic Value as Option<u64>, for a non-negative integer up to u64::MAX. |
| `as_f64` | `fn as_f64(value: json::Value) -> Option<f64>` | Reads a dynamic Value as Option<f64>. |
| `as_bool` | `fn as_bool(value: json::Value) -> Option<bool>` | Reads a dynamic Value as Option<bool>. |
| `as_array` | `fn as_array(value: json::Value) -> Option<Vec<json::Value>>` | Reads a dynamic Value as an array of Values. |
| `entries` | `fn entries(value: json::Value) -> Option<Vec<(String, json::Value)>>` | An object's members as (key, value) pairs in key order; None for any other value. |
| `pointer` | `fn pointer(value: json::Value, pointer: String) -> Option<json::Value>` | Looks up the value an RFC 6901 JSON Pointer names (`/current/weather_descriptions/0`): each token is an object member, or an array index. An empty pointer names the whole value; a pointer that names nothing answers None. |
| `set_max_depth` | `fn set_max_depth(levels: i64) -> ()` | Caps how deeply arrays and objects may nest for every later parse and decode in the process; 0 or less removes the cap. The default is 128, as serde_json's. |
| `set_max_size` | `fn set_max_size(bytes: i64) -> ()` | Caps the bytes a JSON document may have for every later parse and decode in the process; 0 or less removes the cap. There is no cap by default. |

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->

## Typed values

`json::decode::<T>(text)` and `json::encode(value)` convert between JSON
text and any type with a JSON form: structs and enums (generic ones
too), `Vec<T>`, `Map<String, V>`, `Option<T>`, tuples, fixed arrays, and
scalars. The target of a decode comes from its turbofish or from the
binding it initialises:

```gossamer
use std::encoding::json
use std::errors

struct Address {
    city: String
    zip: String
}

struct User {
    name: String
    age: i64
    address: Address
}

fn main() -> Result<(), errors::Error> {
    let user: User = json::decode(
        "{\"name\":\"ann\",\"age\":30,\"address\":{\"city\":\"Oslo\",\"zip\":\"0150\"}}",
    )?
    println(json::encode(user)?)              // members in declaration order
    println(json::encode(user, sort: true)?)  // members by key
    println(json::encode_pretty(user.address)?)
    let scores = json::decode::<Map<String, i64>>("{\"b\": 2, \"a\": 1}")?
    println(f"{scores}")
    Ok(())
}
```

Every encoder answers `Result<String, errors::Error>`. A struct's
members are written in declaration order, as `serde_json` writes them;
`sort: true` orders them by key. A `Map`'s keys and a `json::Value`
object's members are always written by key. Each encoder writes through a walk
generated for the value's concrete type, so encode where the type is known:
inside `fn text<T>(v: T)`, `json::encode(v)` is GT0126.

Decoding is strict: every member a struct declares must be present
(unless it is an `Option` or carries `#[default]`), members the struct
does not declare are ignored, and a failure names the path to the value
that failed and what it found:

```text
address.zip: expected string, found 150
missing field `address`
```

### Attributes

| Attribute | On | Effect |
|---|---|---|
| `#[rename("key")]` | field, variant | Writes and reads the member or variant under `key`. |
| `#[rename_all("camelCase")]` | struct, enum | Respells every field or variant without its own `#[rename]`; also `snake_case`, `PascalCase`, `kebab-case`, `lowercase`, `UPPERCASE`, `SCREAMING_SNAKE_CASE`, `SCREAMING-KEBAB-CASE`. |
| `#[skip]` | field | Never written; filled with the type's zero value on decode. |
| `#[default]` | field | A missing member decodes as the type's zero value. |
| `#[default(value)]` | field | A missing member decodes as `value`: a literal, `None`, or a unit variant. |
| `#[tag("type")]` | enum | Each variant is one object holding the tag member beside its fields: `{"type": "Circle", "r": 2}`. |

Enums are externally tagged by default: a unit variant is its name, any
other an object whose one key is its name. An `Option<Option<T>>` member
tells a missing member (`None`) from `null` (`Some(None)`), and a `None`
there is left out when encoding. A misplaced or malformed attribute is
GP0068.

## Dynamic values

`json::parse(text)` answers a `json::Value` for a document whose shape
arrives at run time. Every lookup answers an `Option`, so lookups chain:

```gossamer
let doc = json::parse("{\"ports\": [8080, 8443], \"limits\": {\"cpu\": 1.5}}")?
let second = json::get(doc, "ports").and_then(|p| json::at(p, 1))   // Some(8443)
let cpu = json::pointer(doc, "/limits/cpu").and_then(json::as_f64)  // Some(1.5)
let count = json::len(doc)                                           // Some(2)
for (key, value) in json::entries(doc).unwrap_or(#[]) {
    println(f"{key} = {value}")
}
```

`json::get` answers `None` for a missing member and `Some(null)` for a
`null` one; `json::at` answers `None` past the end; `json::len`,
`json::keys`, and `json::entries` answer `None` for a value that is not a
container. The same queries are methods (`doc.get("ports")`).
`json::to_value(v)` converts any typed value into a `json::Value`, and
`json::from_value::<T>(value)` decodes a subtree a program navigated to
without writing it back to text.

## Limits

There is no size cap by default, as in `serde_json` and Go;
`json::set_max_size(bytes)` sets one for every later parse and decode in
the process, and `json::set_max_depth(levels)` changes the nesting cap
from its default of 128 (0 or less removes either cap).
