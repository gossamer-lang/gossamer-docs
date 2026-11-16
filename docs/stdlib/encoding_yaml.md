# `std::encoding::yaml`

Status: experimental

YAML 1.2 parser/emitter (serde_norway-backed).

## Items

| Item | Signature | Description |
|---|---|---|
| `Value` | `type Value` | Dynamically typed YAML value. |
| `parse` | `fn parse(source: String) -> Result<json::Value, errors::Error>` | Parses a YAML document into a Value. |
| `encode` | `fn encode<T>(value: T, sort: bool = false) -> Result<String, errors::Error>` | Encodes a value as a YAML document, answering `Result<String, errors::Error>`: a struct's members in declaration order (by key with `sort: true`), a `json::Value` object's and a `Map`'s keys sorted. `yaml::encode::<T>(v)` names the type. |
| `encode_all` | `fn encode_all(values: Vec<json::Value>) -> Result<String, errors::Error>` | Encodes a `Vec<json::Value>` as a multi-document YAML stream, as `parse_all` reads it back. |
| `decode` | `fn decode<T>(source: String) -> Result<T, errors::Error>` | `yaml::decode::<T>(text)` decodes a YAML document into any type with a JSON form, as `json::decode::<T>` decodes JSON. |
| `set_max_size` | `fn set_max_size(bytes: i64) -> ()` | Caps the bytes a YAML document may have for every later parse and decode in the process; 0 or less removes the cap. There is no cap by default. |
| `set_max_depth` | `fn set_max_depth(levels: i64) -> ()` | Caps how deeply YAML collections may nest for every later parse and decode in the process; 0 or less removes the cap. The default is 128. |
| `parse_all` | `fn parse_all(source: String) -> Result<Vec<json::Value>, errors::Error>` | Parses a multi-document YAML stream into a Vec<Value>. |
| `to_json_text` | `fn to_json_text(source: String) -> Result<String, errors::Error>` | Converts a YAML document to JSON text, each mapping's members by key. |
| `from_json_text` | `fn from_json_text(source: String) -> Result<String, errors::Error>` | Converts JSON text to a YAML document, each object's members by key. |
| `is_valid` | `fn is_valid(source: String) -> bool` | Reports whether the text is well-formed YAML. |

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->

## Usage

YAML works the way JSON does. `yaml::decode::<T>(text)` and
`yaml::encode(value)` are the typed codecs, with the same attributes,
member order, and `sort: true` as `json::decode` / `json::encode`;
`yaml::parse` answers a `json::Value`.

```gossamer
use std::encoding::{json, yaml}
use std::errors

struct Step {
    name: String
    run: String
}

fn main() -> Result<(), errors::Error> {
    let steps = yaml::decode::<Vec<Step>>("- name: build\n  run: make\n")?
    print(yaml::encode(steps[0])?)
    let docs = yaml::parse_all("kind: a\n---\nkind: b\n")?
    println(f"{json::get(docs[1], "kind")}")
    print(yaml::encode_all(docs)?)
    Ok(())
}
```

`yaml::to_json_text` and `yaml::from_json_text` convert text directly,
each mapping's members by key. An integer past `i64::MAX` stays exact.
There is no size cap by default (`yaml::set_max_size`), and the nesting
cap is 128 (`yaml::set_max_depth`).
