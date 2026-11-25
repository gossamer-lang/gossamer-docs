# `lang::enum`

Sum type declaration with payload-carrying variants.

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->

Variants carry tuple payloads (`Line(i64)`, `Rect(i64, i64)`), struct
payloads (`Named { id: i64 }`), or nothing (`Dot`). Recursive payloads
work directly with no wrapper - `enum List { Cons(i64, List), Nil }` -
because every variant payload is already heap-shared. There are no pointer
wrappers: `Box<List>`, `Rc<List>`, or `Arc<List>` is `GT0079`, naming the
type to write instead. Match exhaustively.

## Field defaults and methods in the body

A struct variant's fields take defaults as a struct's do, and an enum may hold
its methods in its own body after its variants, listing the traits they
implement after its name:

```gossamer
trait Area {
    fn area(&self) -> f64
}

enum Shape: Area {
    Circle { r: f64 = 1.0 }
    Rect { w: f64, h: f64 = 2.0 }

    fn area(&self) -> f64 {
        match self {
            Shape::Circle { r } => 3.0 * r * r,
            Shape::Rect { w, h } => w * h,
        }
    }
}

println(f"{Shape::Circle {}.area()} {Shape::Rect { w: 3.0 }.area()}")
```

After an enum's name, an unsigned width (`enum Level: u16`) sets the
discriminant's width, as [below](#how-wide-the-discriminant-is); any other
name lists a trait. See [struct](struct.md#field-defaults) for the default
rules and [impl](impl.md#methods-in-the-types-body) for the body rules.

## Variant names

A variant belongs to its enum, so two enums may declare variants of the
same name, in one module or in different ones:

```gossamer
enum Conn { Ready, Closed }
enum Job { Ready, Pending }

fn describe(c: Conn) -> String {
    match c {
        Conn::Ready => "ready",
        Conn::Closed => "closed",
    }
}

fn main() {
    println(describe(Conn::Ready))
    let j = Job::Ready
    println("{}", j == Job::Ready)
}
```

A bare variant name resolves to the enum the current module declares, or
to the one enum in the program that declares it. A bare name two enums in
the current module share is ambiguous and reported with the qualified
spelling (`GR0009`); an enum in another module never makes a bare name in
this one ambiguous.

## Compare by value, order by declaration

Enums are value types, so `==` and `!=` are synthesized automatically - no
`#[derive]` needed - whenever every payload is comparable. An order is a
choice the enum declares: with `#[derive(PartialOrd, Ord)]`, `<` / `<=` /
`>` / `>=` order by **variant rank first** (declaration order), then
payload lexicographically. Ordering an enum that declares no order is
`GT0143`, and `gos check --fix` adds the derive:

```gossamer
#[derive(PartialOrd, Ord)]
enum Shape { Dot, Line(i64), Box(i64, i64) }

println("{}", Shape::Dot < Shape::Line(0))     // true: Dot ranks before Line
println("{}", Shape::Line(1) < Shape::Line(2)) // true: same rank, payload compared
println("{}", Shape::Box(1, 2) == Shape::Box(1, 2))
```

A user `impl` of `eq` / `cmp` overrides the synthesized one for custom
ordering.

## Derivable traits

`#[derive(...)]` covers `Debug`, `Default`, `PartialEq`, `Eq`,
`PartialOrd`, and `Ord` for tuple, unit, and struct-payload variants;
`#[default]` marks the `Default` variant. The derive only *forces*
synthesis where the automatic gate is conservative (generic or
container-typed payloads).

```gossamer
#[derive(Debug, Default, PartialEq)]
enum Move {
    #[default]
    Stay,
    Step(i64),
}
```

`Clone`, `Copy`, `Hash`, `Display`, `Serialize`, and `Deserialize` are
**not** derivable (`GT0025`) - copying, hashing, and serialization are
automatic. The enum cap is 256 variants (`GT0012`).

## How wide the discriminant is

A plain `enum` stores its discriminant in the smallest byte-aligned
width that holds every variant. `packed` asks for the smallest number of
bits instead, and a `: uN` names a width outright - any unsigned width
from `u1` to `u64`:

```gossamer
enum Level: u16 { Debug, Warn, Error }   // 16 bits, as asked
packed enum Direction { North, East, South, West }  // 2 bits
packed enum Bit: u1 { Off, On }          // exactly 1 bit
```

A width too narrow for the variants reports `GT0081` with the width they
need; a representation that is not an unsigned width reports `GP0050`.
Variants number from zero in declaration order.

The choice is about storage only. Matching, `==`, ordering, `{}` and
`{:?}`, serialization, `Map` keys, arrays, and tuples all behave
identically at every width, on the VM and both compiled tiers.

`packed` is a keyword only directly before `enum`, so a value or a
function may still be named `packed`.
