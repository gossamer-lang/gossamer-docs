# Toolchain reference

Every subcommand of `gos`. Auto-generated output coming with
Stream H polish - for now this page is hand-written and may lag
the implementation by a rev.

## Front-end

| Command | Purpose |
|---------|---------|
| `gos parse FILE` | Print the AST. |
| `gos check [--timings] FILE` | Parse + resolve + typecheck + exhaustiveness. With `--timings`, prints per-stage wall-clock times. The whole result is cached, so a re-invocation over unchanged inputs skips every front-end stage ([incremental front end](design/incremental.md)). Set `GOSSAMER_CACHE_TRACE=1` to log cache hits, `GOS_NO_CACHE=1` to disable the cache. |
| `gos run FILE` | Execute via the register-based bytecode VM. Recursive helper workloads may promote through the in-process Cranelift JIT. |
| `gos run --native FILE` | Build and run the native executable `gos build` makes: a current release build starts at once, otherwise a debug build runs while the release build follows in the background. |
| `gos watch [PATH] [--] [ARGS...]` | Validate and restart a development service when project inputs change. This is process replacement, not in-process code patching. |
| `gos build [--release] [--target TRIPLE] FILE` | Produce a native binary (ELF/Mach-O/PE) by lowering through MIR + LLVM (checked debug arithmetic, with a minimal `opt` pipeline over `llc -O1`; `--release` runs `opt -O3 | llc -O3`) and linking the user's `.o` against `libgossamer_runtime.a`. Release builds may use `--pgo-collect PATH.profraw` to emit an instrumented binary or `--pgo-profile PATH.profdata` to apply merged LLVM profile data; the modes conflict, profile input must exist, and an input older than the source produces a warning. `GOS_SYMBOL_ORDER=FILE` names the functions a native Linux or macOS build lays out first and together, one symbol a line, hottest first, so the code a program runs at start fills fewer pages; Linux links with lld when it is set, and names the program no longer has are skipped. The Cranelift code path is reserved for the in-process JIT (`gos run`), not this command. Tier 2 cross deployment is `{x86_64,aarch64}-unknown-linux-musl`, QEMU-differential-tested in CI. Other registered triples are not supported merely because a local link succeeds; macOS/Windows as cross targets are out of scope. |

## Formatting + linting + docs

| Command | Purpose |
|---------|---------|
| `gos fmt [--check] FILE` | Rewrite canonically. |
| `gos doc [--html OUT] FILE` | List items (plain-text) or write an HTML page. |
| `gos lint [--deny-warnings] [--explain ID] [--fix] PATH` | Run the lint suite (56 lints), Rust's naming conventions among them. `--fix` writes auto-applicable suggestions back to disk; `--explain ID` prints long-form rationale. |
| `gos explain CODE` | Long-form rationale for a diagnostic code. |

## Testing + benchmarking

| Command | Purpose |
|---------|---------|
| `gos test PATH` | Run `#[test]` functions **and** doc-tests extracted from `` ``` ``-fenced code inside `//` doc comments. `` ```text `` and other language tags are skipped. Accepts a file or a directory. A test that records no assertion fails: a body that only prints decides nothing. A test declared `-> Result<(), E>` is exempt, since reaching `Ok` past every `?` is its verdict. |
| `gos bench [--parallel N] [PATH]` | Discover and time `#[bench]` functions; reports `ns/op` plus JIT tier-up, compile-time, native-code, peak-RSS, and bypassed-VM-work counters. Per-bench iteration counts auto-tune against a 50 ms calibration window (cap 2^20). `PATH` defaults to the project's `src/`. |

## Watch

| Command | Purpose |
|---------|---------|
| `gos watch [PATH] [--] [ARGS...]` | Validate and restart a development service when project inputs change. `gos dev` is accepted as a compatibility alias. |

## Serving files

| Command | Purpose |
|---------|---------|
| `gos serve [DIR] [--port PORT] [--bind ADDR]` | Serve the files under `DIR` (default the current directory) over HTTP, as `python -m http.server` does. Listens on `127.0.0.1` port `8000` unless `--bind` and `--port` say otherwise; `--bind 0.0.0.0` answers every network the machine is on, and `--port 0` picks a free port. The first line on stdout names the URL; each request is logged to stderr. A directory's `index.html` is its page, and a directory without one is listed. `GET` and `HEAD` are answered, with `ETag` / `Last-Modified` revalidation and byte ranges; a path that leaves `DIR` is `404`, and any other method is `405`. |

```sh
gos serve                         # ./ at http://127.0.0.1:8000/
gos serve site --port 3000        # ./site at http://127.0.0.1:3000/
gos serve --bind 0.0.0.0          # reachable from other machines
```

`gos serve` is for development and sharing files on a trusted network: it
has no TLS and no access control. A program that serves files in
production uses `http::static_files::FileServer` behind its own router.

## Housekeeping

| Command | Purpose |
|---------|---------|
| `gos clean [--all] [--frontend] [--ir] [--bindings] [--packages] [--build-cache] [--vendor] [--dry-run]` | Remove selected toolchain caches. With no cache-class flag it clears frontend and IR caches; `--all` includes Rust-binding builds, packages, and legacy build artifacts. `--vendor` also deletes `./vendor/`. |
| `gos cache [--path] [--prune] [--clear] [--trim] [--scope SCOPE] [--dry-run]` | Show cache roots and usage, print paths only, prune entries unused for 30 days (`GOS_CACHE_MAX_AGE_DAYS`) and the least recently used beyond the total cap (`GOS_CACHE_MAX_BYTES`, 20 GiB) or a class's own (`GOS_CACHE_<CLASS>_MAX_BYTES`), or clear every class. `--scope local` (the default for `--prune` / `--clear`) reaches this project's `.gos-cache/`; `--scope global` reaches the shared roots every project reuses; `--scope all` reaches both, and is what the report shows. `--trim` prunes the shared roots at once, leaving package sources: the trim build commands start in the background, at idle CPU and disk priority, once a day on their own, recorded in the user cache's `trim.txt`. `GOS_CACHE_TRIM` sets how often (`never`, `always`, or an interval such as `30m`, `12h`, or `7d`). No prune or trim removes a directory a running `gos` builds in or reads from. |

## Package manager

| Command | Purpose |
|---------|---------|
| `gos new ID [--path DIR] [--template bin\|lib\|service\|workspace\|binding]` | Scaffold a project, or a Rust binding crate. |
| `gos init ID` | Create `project.toml` in the CWD. |
| `gos add SPEC` | Add a dependency (`name` or `name@version`). |
| `gos remove ID` | Drop a dependency. |
| `gos update` | Update locked dependencies within declared ranges. |
| `gos tidy` | Remove unused project dependencies and canonicalise the manifest. |
| `gos fetch` | Prepare each git / registry / tarball dependency's source in the local cache. |
| `gos vendor` | Copy the same trees into `./vendor/`. |
| `gos bindgen FILE [--output DIR] [--module NAME]` | Scaffold a Rust binding crate from a Rust source file's `pub fn` items. |

## Registry workflow

| Command | Purpose |
|---------|---------|
| `gos publish [--dry-run]` | Pack, Ed25519-sign, and upload the project to a registry. `--dry-run` packs + signs and prints metadata without uploading. |
| `gos yank` | Yank a previously-published version. |
| `gos login` / `gos logout` | Save / drop a registry bearer token in `~/.gossamer/credentials.toml`. |
| `gos owner` | Manage the publisher ACL of a published project. |

## REPL

`gos` with no arguments - or `gos repl` - drops into an interactive session.
It starts with `gos <version> REPL [<architecture>-<os>]`. The REPL supports:

- A `>>>` input prompt; successful expressions print only their value, with
  no numbered input or output markers.
- Quiet declaration and binding updates by default. Pass `gos -v repl` or
  `gos repl -v` to show progress messages.
- Declarations persisting across inputs (`fn` / `struct` / `enum`
  / `use` / `const` / `type`).
- `let` bindings persisting across inputs; every subsequent
  expression sees previously-bound locals in scope. `%bindings`
  lists the active set.
- `%help` lists REPL commands.
- `%info [name]` (`%i`) answers the public language and standard-library
  catalog and the current session for one name. The name is matched exactly, so
  `%i Set` reports the set type and `%i Set::new` reports that one associated
  function; a `*` widens it to a prefix (`Set*`), a suffix (`*Set`, which also
  reaches `BTreeSet` and `flag::Set`), or a substring (`*Set*`). A name is
  matched the way source spells it: a type, a macro, a prelude builtin, and a
  method by its bare name, a module item through the module that declares it
  (`fs::read_to_string`). A type reports its fields, the traits implemented for
  it, and its methods, each tagged with the trait it came from or `[inherent]`;
  a trait reports its methods and the types implementing it. A session `impl`
  on a builtin type adds to that type's catalog entry rather than replacing it.
  `%explain NAME` (`%e`) inspects a persistent binding under the same matching
  rules, showing the same fields and traits with methods in receiver form, and
  filters the catalog methods by the binding's type and mutability. Add
  `--details` for descriptions and examples.
- `%bindings [pattern]` (`%b`), `%declarations [pattern]` (`%d`), and
  `%history [regex]` (`%h`) show persistent bindings, declarations, and input
  history. `%bindings` filters binding names, and `%declarations` filters
  declaration names. `%drop NAME` ends one persistent binding's lexical lifetime
  and removes it, which releases any source protected by a reference binding.
  `%drop` also accepts a declared name, removing the declaration that introduced
  it along with the declarations that name it, so `%drop f` frees `f` to be
  declared again. `%reset` (`%r`) clears bindings and declarations.
- Tab completes the word at the cursor: a keyword, a `module::item` path,
  every member a binding reaches after `.` - the methods its type and
  mutability can call, a session-declared type's fields, a tuple's positions -
  and a type's own methods and associated functions after `::`. What
  `%explain` lists for a binding is what completion offers for it.
- Up/down cycles history. Enter continues until braces close. Ctrl-D or
  `%quit` (`%q`) exits.

Meta-command output adapts to the current terminal width and is capped at 80
columns, so `%help`, `%info`, `%explain`, `%bindings`, and `%declarations` remain
readable in narrow terminals.

## Editor integration

| Command | Purpose |
|---------|---------|
| `gos lsp` | Start a language-server-protocol adapter on stdio. |

`gos lsp` is intended for editors, not humans. It analyses the whole
package a file belongs to, so every answer sees the other files of the
project, open or not:

- Diagnostics - every document runs through parse, resolve, typecheck,
  and lints, and is published on open and on every edit, with the same
  findings `gos check` reports.
- `hover`, `signatureHelp` - the type and doc comment of what is under the
  cursor, and the parameters of the call being written.
- `definition`, `typeDefinition` - the declaration of a local, an item, or
  a value's type, in whichever file of the package declares it.
- `references`, `documentHighlight`, `prepareRename` / `rename` - semantic
  occurrences across the workspace; a rename answers one `WorkspaceEdit`
  over every file it touches.
- `completion` - keywords, items in scope, `module::item` paths, and the
  methods and fields a receiver's type answers after `.`.
- `documentSymbol`, `workspace/symbol`, `foldingRange` - the outline, a
  workspace-wide symbol search, and folds.
- `inlayHint`, `semanticTokens/full` - inferred types of `let` bindings and
  closure parameters, and semantic highlighting.
- `formatting` and `codeAction` - `gos fmt` as a document edit, quick fixes
  for the suggestions diagnostics carry, and `source.fixAll.gossamer`.

At `initialize` the server indexes every `.gos` file under the workspace
folders. Files the editor has not opened are read from disk; when the
client supports dynamic registration the server asks it to watch `*.gos`
and `project.toml` files, so changes made outside the editor (a
`git checkout`, a code generator) reach the analysis. Text sync is
incremental, and positions are UTF-16 columns as LSP 3.16 specifies.

### Pre-built editor integrations

Plug-ins that wire `gos lsp` into common editors live in a separate
repo:
[`gossamer-lang/gossamer-editor-support`](https://github.com/gossamer-lang/gossamer-editor-support)
- ships VSCode, Vim, Neovim, Helix, Emacs, Sublime, Zed clients
plus a tree-sitter grammar.

## Agent integration

| Command | Purpose |
|---------|---------|
| `gos mcp` | Start a model-context-protocol server on stdio. |

`gos mcp` speaks the Model Context Protocol so AI coding agents
(Claude Code, OpenCode, Cursor, Zed) can drive the toolchain
directly:

- `check` - parse + resolve + typecheck + lints; one JSON object per
  diagnostic (the `--message-format json` schema). With `fix: true` it
  applies the rewrites the diagnostics carry, as `gos check --fix` does.
- `fix` - the toolchain's source migrations (`gos fix`); `list: true`
  names them and `check: true` reports without writing.
- `lint` - the lint suite, with `fix` and `deny_warnings`.
- `explain` - long-form rationale for a diagnostic code.
- `execute` / `build` / `test` - execute programs and test suites;
  exit code, stdout, and stderr come back, bounded by a per-call
  `timeout_ms` that ends the whole process tree the call started.
  `execute` with `native: true` runs the native executable `gos build`
  makes instead of the VM.
- `fmt` / `doc` - formatting and item listings.
- `audit` / `feature_status` - dependency advisories, and whether a
  language or library feature is settled.
- `check`, `execute`, `fmt`, `doc`, `lint`, and `fix` take an inline
  `source` in place of a path; a tool that rewrites it hands the rewritten
  text back.
- `hover` / `definition` / `references` / `workspace_symbols` -
  semantic navigation backed by the same analysis engine as
  `gos lsp`.
- The [AI skill card](https://github.com/gossamer-lang/gossamer/blob/main/SKILL.md)
  ships as the `gossamer://skill-card` resource and the
  `skill-card` prompt; `gos skill-prompt` prints the same text.

MCP framing is newline-delimited JSON-RPC; LSP framing is
`Content-Length`-headed. `gos lsp` belongs in an editor's LSP
configuration and `gos mcp` in an agent's MCP configuration - the
two are not interchangeable.

Claude Code:

```bash
claude mcp add gossamer -- gos mcp
```

Generic client config:

```json
{ "mcpServers": { "gossamer": { "command": "gos", "args": ["mcp"] } } }
```

## Smoke-test

```sh
python3 - <<'PY'
import json, subprocess
p = subprocess.Popen(["gos", "lsp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"processId": None, "capabilities": {}}}).encode()
p.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body); p.stdin.flush()
header = p.stdout.readline()
p.stdout.readline()
print(json.loads(p.stdout.read(int(header.split(b":")[1])))["result"]["serverInfo"])
PY
```
