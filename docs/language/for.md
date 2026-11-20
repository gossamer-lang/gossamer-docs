# `lang::for`

Iterator-driven loop.

<!-- hand-maintained from here: preserved by `gos doc --emit-stdlib` -->

`for x in xs` walks any collection, a range, or an iterator, binding each
element in turn. A loop over a collection walks the value it held when the
loop began, as a `let` copy of it would, so a body that changes the
collection changes it afterwards rather than changing which elements the loop
visits:

```gossamer
fn main() {
    let mut xs = #[1, 2, 2, 3]
    for x in xs {
        if x == 2 {
            let at = xs.iter().position(|y| y == x).unwrap()
            xs.remove(at).unwrap()
        }
    }
    println(xs)  // #[1, 3]
}
```
