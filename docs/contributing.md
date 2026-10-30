# Contributing

## House rules

- Safe Rust in the front-end: the parser, resolver, type checker,
  MIR, LLVM codegen, lints, and scheduler crates forbid
  `unsafe_code`. The runtime, the Cranelift JIT, the stackful-coroutine
  layer, and the FFI binding surface contain contained, reviewed
  `unsafe` (C ABIs, executing generated code, context switching) -
  keep it in the smallest possible scope.
- `cargo clippy --workspace --all-targets -- -D warnings` is the
  gate.
- `cargo fmt --all --check` must pass.
- One focused change per PR. No drive-by refactors.

The full style guide is in
[`GUIDELINES.md`](https://github.com/gossamer-lang/gossamer/blob/main/GUIDELINES.md).

## Getting oriented

- Start with the [language spec](https://github.com/gossamer-lang/gossamer/blob/main/SPEC.md) for grammar and semantics.
- Each crate under `crates/` has a module-level `//!` doc
  describing the compiler phase it belongs to.
- Design notes live under
  [`docs/`](https://github.com/gossamer-lang/gossamer/tree/main/docs)
  (diagnostics style guide, runtime internals, self-hosting study).

## Picking an issue

Streams ordered by impact, smallest to biggest:

1. Landing a new lint in `gossamer-lint` (the framework is in
   place; each lint is ~20 lines).
2. Wiring a new native stdlib module (see the `std::regex`
   wrapper for the pattern).
3. Extending the diagnostics style guide with acceptance
   fixtures.
4. Closing a security item in the roadmap.
5. Implementing a major language feature (Cranelift codegen,
   scheduler, LSP capabilities beyond the shipped slice).

## Running the tests

```sh
cargo test --workspace
```

Per-crate:

```sh
cargo test -p gossamer-mir
cargo test -p gossamer-std --lib
```

Release benches:

```sh
cargo bench -p gossamer-interp
```

## Docs

The documentation and the website live in their own repository,
[gossamer-docs](https://github.com/gossamer-lang/gossamer-docs), with a
Gossamer checkout beside it:

```sh
pip install -r requirements.txt
mkdocs serve
```

Opens at `http://localhost:8000/`. Edit `docs/*.md` and save; the site
reloads. `./run-site.sh` serves the whole site the way it deploys: the home
page, the tour, the playground (`--wasm` builds the real VM from the
Gossamer checkout) and the docs.

`tools/check-docs.gos` holds the docs to the toolchain. Every ` ```gossamer `
fence must be a program `gos check` accepts. A fence that is a piece of a
larger program the prose describes is preceded by `<!-- fragment -->`; one
that shows a rejected program is preceded by `<!-- compile_fail CODE -->` and
must fail with that diagnostic; one preceded by `<!-- output: TEXT -->` must
print `TEXT` when run. The markers are HTML comments, so they do not render.
Fences in the Ecosystem pages are checked in a project that depends on the
library they document. The tour's lessons and the home page's listings must
run.

Some pages are generated from Gossamer's sources: the stdlib and language
reference pages by `gos doc --emit-stdlib docs/stdlib`, which also writes each
module's item table from the manifest and the checker's signatures, and the
stdlib overview, coverage matrix, lint and diagnostic catalogues and API
catalogs by `cargo xtask docs-all --docs DIR`. `tools/generated.sh`
regenerates all of them from the Gossamer checkout, and with `--check` fails
when a page drifts, a description names a library path no module declares, or
a documented feature has no page.
