# `lang::impl`

Inherent and trait implementation blocks.

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->

An inherent `impl Type` block adds methods and associated functions; an
`impl Trait for Type` block supplies a trait's methods. A type may also hold
its methods in its own body; [where methods go](#where-methods-go) says when
to use which.

```gossamer
struct Point { x: i64, y: i64 }

impl Point {
    fn origin() -> Point { Point { x: 0, y: 0 } }   // associated fn
    fn norm(&self) -> i64 { self.x * self.x + self.y * self.y }
}

let p = Point::origin()   // qualified path always resolves
println("{}", p.norm())
```

A method takes `self`, `&self`, or `&mut self`; `&self` reads, `&mut self`
writes through to the caller's storage. Qualified-path calls
(`Point::origin()`) always resolve; method-call dispatch is type-directed for
user impls, core collection/String receivers, and typed stdlib receivers.
Prefer the qualified form when several types intentionally share an associated
function name and you want the call target to be explicit.

## Where methods go

Write a type's primary API in its body: constructors, accessors, invariant
checks, and the operations that make the type what it is. Write its extended
API in `impl` blocks: trait implementations, optional or platform-specific
code, and large groups of specialized methods.

Decide by meaning, not length. A long method can be core to a type, and a
short one can be an extension.

Rust keeps every method apart from the fields, so learning a type's basic API
means reading several declarations. Swift and C# declare members inside the
type, and Swift adds protocol conformances in separate `extension` blocks.
Gossamer follows that split. Both forms compile to the same program, so this
is a convention, not a rule.

```gossamer
struct Temperature {
    celsius: f64

    fn from_fahrenheit(f: f64) -> Temperature {
        Temperature { celsius: (f - 32.0) * 5.0 / 9.0 }
    }
    fn fahrenheit(&self) -> f64 { self.celsius * 9.0 / 5.0 + 32.0 }
}

impl Display for Temperature {
    fn fmt(&self) -> String { f"{self.celsius} C" }
}

let boiling = Temperature::from_fahrenheit(212.0)
println(f"{boiling} is {boiling.fahrenheit()} F")
```

## Methods in the type's body

A struct or enum may hold its methods, associated types, and constants in its
own body, after its fields or variants, and list the traits they implement
after its name:

```gossamer
trait Area {
    fn area(&self) -> f64
}

struct Circle: Area {
    r: f64

    fn unit() -> Circle { Circle { r: 1.0 } }        // associated fn
    fn area(&self) -> f64 { 3.0 * self.r * self.r }   // implements Area
    fn grown(&self) -> Circle { Circle { r: self.r + 1.0 } }
}

println(f"{Circle::unit().grown().area()}")
```

This is the same declaration as the type followed by the `impl` blocks its
body stands for; the two spellings mean the same program in every way.

- A body function whose name exactly one listed trait declares implements that
  trait. A name no listed trait declares is an inherent method, even when an
  unlisted trait declares it.
- A name two listed traits declare is `GP0069` (`Display` and `Debug` both
  declare `fmt`): write one of them as a standalone `impl`.
- A function that matches a listed trait's name but not its receiver,
  parameters, or return type is `GT0127` against that trait, never an
  inherent method.
- A listed trait that a standalone `impl` for the same type also implements is
  `GT0073`, and one whose required items the body leaves out is `GT0058`.
- A tuple struct takes a body only in the braced form after its fields
  (`struct Pair(i64, i64): Display { fn fmt(&self) -> String { .. } }`).
- A generic type lists traits over its own parameters; an `impl` that needs
  bounds of its own (`impl<T: Ord> Trait for S<T>`), or a trait on a type
  declared elsewhere, stays a standalone block.

`gos fix --rewriter impl-into-type-body` moves standalone blocks into the
type's body, and `--rewriter type-body-into-impl` moves them back. `gos fmt`
never moves code between the two forms.

## Generic impls

Methods on a generic struct use the `impl<T>` form, and each receiver type
specialises the method (so `-> T` returns the real instantiated type):

```gossamer
struct Wrapper<T> { value: T }

impl<T> Wrapper<T> {
    fn get(&self) -> T { self.value }
}
```

## Operator and conversion impls

Operator overloading (`impl Add for T`, `impl Index for T`, ...) and
conversions (`impl T { fn from(...) }`, `fn try_from(...)`) are ordinary
impls - see [trait](trait.md) for the operator/method table and the
`into` / `try_into` inference rules. The comparison (`eq` / `cmp`) and
`clone` behaviour is synthesized with no impl; write an `eq` / `cmp` impl
only to override the default ordering.
