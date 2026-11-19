# `lang::struct`

Product type declaration.

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->

## Functional record update

A struct literal may spread a base value with `..base` and override
individual fields:

<!-- fragment -->
```gossamer
let p2 = Point { x: 10, ..p1 }
```

- Explicit fields win over the base for the same name.
- Exactly one `..base` spread is allowed (a second is a parse error).
- A spread references every field the literal does not name, so the whole
  struct has to be visible where the update is written. A struct with any
  private field cannot be updated from outside the module that declares it,
  exactly as it cannot be constructed there - see
  [visibility](visibility.md).
- Fields copied from the base share its heap children and are retained,
  so the base stays usable after the update with no double-free. Output
  is identical across the VM, Cranelift, and LLVM tiers.

## Declaration and construction

Struct declarations follow Rust's three shapes: unit structs, named-field
structs, and tuple structs. Empty named structs use braces, and empty tuple
structs use parentheses:

```gossamer
struct Unit
struct Empty {}
struct EmptyTuple()
struct Pt { x: i64, y: i64 }
struct Pair(String, i64)

let unit = Unit
let empty = Empty {}
let empty_tuple = EmptyTuple()
let p = Pt { x: 3, y: 4 }     // keyed fields, any order
let pair = Pair("row", 4)
println(f"{p.x} {p.y}")
println(f"{pair.0} {pair.1}")
let Pt { x, y } = p
```

Named structs must be constructed with keyed fields in `Name { field: value }`;
both `Name(...)` and positional `Name { value }` forms are rejected. Unit
structs use either `Name` or `Name {}`, while tuple structs must be constructed
with `Name(...)`.

On one line, commas separate fields. In a multiline declaration or literal,
newlines separate fields. Multiline commas are accepted for migration and
`gos fmt` removes them:

```gossamer
struct Point {
    x: i64
    y: i64
}

let p = Point {
    x: 3
    y: 4
}
```

## Field defaults

A field may declare a default after its type. A struct literal may leave such
a field out and takes the default for it, or write the field to override it.
A field without a default is still required in every literal (`GT0035`):

```gossamer
struct Rng { seed: u64 = 7 }

struct Settings {
    name: String
    retries: i64 = 3
    tags: Vec<String> = #[]
    rng: Rng = Rng::default()
}

let s = Settings { name: "svc" }
let t = Settings { name: "batch", retries: 5 }
println(f"{s.retries} {t.retries} {s.tags.len()} {s.rng.seed}")
```

- A default is any expression, calls included, and runs at every
  construction that leaves the field out, so each value gets one of its own:
  two `Settings { name: "a" }` never share a `Vec` or an `Rng`.
- A default means what it means where the struct is declared, whichever
  module the literal is in. It cannot read `self` or another field of its
  struct (`GR0026`), and it is checked against the field's type once, at the
  declaration.
- A struct whose every field has a default builds as `T {}` or
  `T::default()`; `#[derive(Default)]` on it is redundant (`GL0061`).
- `json::decode::<T>`, `yaml`, and `toml` read a missing key as the field's
  default, unless the field carries a `#[default(..)]` of its own.
- Enum struct variants take defaults the same way: see [enum](enum.md).
- Once built, a defaulted field is an ordinary field: printing, equality,
  ordering, and hashing do not see defaults.

A literal that writes a field with exactly its declared default is the
`GL0060` lint, and `gos lint --fix` drops the restated value. `gos fix
--rewriter fields-take-literal-defaults` goes the other way for existing code:
it gives a field the default every literal of its struct writes, and removes
that value from the literals.

## Methods in the type's body

A struct may hold its methods, associated types, and constants in its own body,
after its fields, and list the traits they implement after its name. The body
is the place for the type's primary API and `impl` blocks for its extensions;
see [where methods go](impl.md#where-methods-go) and
[impl](impl.md#methods-in-the-types-body).

## Value semantics: copy and compare with no derive

Structs are value types. Binding or `.clone()`-ing copies the whole value
(heap children retained), and `==` / `!=` / `<` / `<=` / `>` / `>=` are
synthesized automatically - no `#[derive]` needed - whenever every field
is comparable (scalars, `String`, nested comparable types). Ordering is
lexicographic by field declaration order:

```gossamer
struct Point { x: i64, y: i64 }

let a = Point { x: 1, y: 2 }
let b = a.clone()                          // `clone` is a universal builtin
println("{}", a == b)                     // true, no derive
println("{}", a < Point { x: 1, y: 3 })   // true (lexicographic by field)
```

A user `impl` of `eq` / `cmp` overrides the synthesized comparison.

## Derivable traits

`#[derive(...)]` is limited to `Debug`, `Default`, `PartialEq`, `Eq`,
`PartialOrd`, and `Ord`, synthesized as real source so `{:?}`,
`Type::default()`, and the comparisons work on every tier. The derive
only *forces* synthesis where the automatic gate is conservative (generic
or container-typed fields):

```gossamer
#[derive(Debug, Default, PartialEq)]
struct Config { retries: i64, verbose: bool }
```

`Clone`, `Copy`, `Hash`, `Display`, `Serialize`, and `Deserialize` are
**not** derivable (`GT0025`): copying, hashing, and serialization are
already automatic. Conversion / operator traits (`From`, `Add`, ...) are
written `impl Trait for T`, not derived.
