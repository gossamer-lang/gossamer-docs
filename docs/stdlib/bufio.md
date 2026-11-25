# `std::bufio`

Status: experimental

Buffered readers, writers, and line scanners.

## Items

| Item | Signature | Description |
|---|---|---|
| `Reader` | `type Reader` | Reads an `fs::File` a chunk at a time: `Reader::new(file)`, then `read_line` (answers `Ok(None)` at the end; the line leaves out its `\n` and a `\r` before it), `lines`, and `read_to_string`, each answering a `Result`. |
| `Writer` | `type Writer` | Writes to an `fs::File` through a buffer: `Writer::new(file)` (4096 bytes) or `Writer::with_capacity(file, n)`, then `write`, `write_bytes`, and `flush`. Buffered bytes reach the file before any other call on it, at `flush`, when the last handle to the file goes, and when the program ends. |
| `Scanner` | `type Scanner` | Line / token scanner. |
| `read_lines` | `fn read_lines(path: String) -> Result<Vec<String>, io::Error>` | Reads every line from a file path; one-shot convenience over the streaming Scanner. |
| `read_lines_of` | `fn read_lines_of(path: String) -> Result<Vec<String>, io::Error>` | Reads every line of a file path into a Vec<String>. |
| `read_to_string` | `fn read_to_string(path: String) -> Result<String, io::Error>` | Reads an entire file path into a String. |
| `split_whitespace` | `fn split_whitespace(text: String) -> Vec<String>` | Splits a String on runs of whitespace. |

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->
