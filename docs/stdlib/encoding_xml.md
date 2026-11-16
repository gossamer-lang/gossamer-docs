# `std::encoding::xml`

Status: experimental

XML parse and encode (quick-xml) over a `json::Value` tree.

## Items

| Item | Signature | Description |
|---|---|---|
| `parse` | `fn parse(source: String) -> Result<json::Value, errors::Error>` | Parses an XML document into a `json::Value` tree: an element is `{"__xml_type": "element", "name", "attrs", "children"}`, a text node `{"__xml_type": "text", "value"}`. |
| `encode` | `fn encode(value: json::Value) -> Result<String, errors::Error>` | Serialises a tree of the shape `parse` answers to XML text, answering `Result<String, errors::Error>`; a value of any other shape is an `Err`. |
| `is_valid` | `fn is_valid(source: String) -> bool` | Reports whether the text is a well-formed XML document. |
| `set_max_size` | `fn set_max_size(bytes: i64) -> ()` | Caps the bytes an XML document may have for every later parse in the process; 0 or less removes the cap. There is no cap by default. |
| `set_max_depth` | `fn set_max_depth(levels: i64) -> ()` | Caps how deeply XML elements may nest for every later parse in the process; 0 or less removes the cap. The default is 128. |
| `escape` | `fn escape(text: String) -> String` | Escapes XML metacharacters in text. |

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->

## Usage

`xml::parse` answers the element tree as a `json::Value`, and
`xml::encode` writes such a tree back, answering an `Err` for a value of
any other shape:

```gossamer
use std::encoding::xml
use std::errors

fn main() -> Result<(), errors::Error> {
    let tree = xml::parse("<note id=\"7\"><to>Tove</to></note>")?
    println(f"{tree.get("name")}")                 // Some("note")
    println(xml::encode(tree)?)
    println(f"{xml::is_valid("<a>")}")             // false
    Ok(())
}
```

Entity references may expand to eight times the document (at least
1 MiB), as libxml2 bounds amplification. There is no size cap by default
(`xml::set_max_size`), and the nesting cap is 128 (`xml::set_max_depth`).
