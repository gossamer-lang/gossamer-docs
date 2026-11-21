# `lang::static`

Module-level mutable or immutable static slot. A `static mut` is read and written only inside `unsafe { }` (GT0132); state goroutines share lives in a synchronized `static` such as `sync::AtomicI64`.
