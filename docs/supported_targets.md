# Supported Targets

The executable matrix in
[`conformance/target_matrix.tsv`](https://github.com/gossamer-lang/gossamer/blob/main/conformance/target_matrix.tsv)
is the release contract. `stable_tier_conformance` checks that it remains
registered and that this page and `SPEC.md` name the same support classes.
The matrix is evidence-based: accepting a triple locally is not support.

## Tier 1

Tier 1 targets execute the pure bytecode VM, the JIT-enabled VM, and LLVM AOT
fixtures on native CI. They are the supported execution contract.

| Target triple | Native CI evidence |
|---|---|
| `x86_64-unknown-linux-gnu` | `ubuntu-latest` |
| `aarch64-unknown-linux-gnu` | `ubuntu-24.04-arm` |
| `aarch64-apple-darwin` | `xcode-27` (macOS 27) |
| `x86_64-pc-windows-msvc` | `windows-latest` |
| `x86_64-unknown-freebsd` | FreeBSD VM on `ubuntu-latest` |

## Tier 2

Tier 2 covers Linux-musl AOT output. CI builds it from the supported hosts,
executes it natively or under QEMU, and compares its output with the pure
bytecode VM. This is supported for release AOT deployment, but not evidence
that every host-side toolchain path has native execution coverage.

| Target triple | Differential evidence |
|---|---|
| `x86_64-unknown-linux-musl` | native/QEMU AOT-versus-VM fixture differential |
| `aarch64-unknown-linux-musl` | QEMU AOT-versus-VM fixture differential |

## Artifact-only

`x86_64-apple-darwin` has a release-artifact build in CI, but that artifact is
not executed by the target matrix. It is distributed for evaluation and is not
a supported execution target until native or emulator-backed all-tier evidence
is added.

## Registered, unsupported

The driver also recognises `riscv64gc-unknown-linux-gnu`,
`wasm32-unknown-unknown`, and `wasm32-wasip1` for targeted compile checks. They
are not supported execution targets: the full runtime/scheduler and all-tier
conformance suite do not run there. In particular, `gos build --target
wasm32-...` is not a supported deployment path.

Targets not listed above are Experimental. A local build, a generated object
file, or a package artifact alone does not promote a target, ABI, allocator,
or standard-library surface to Stable.

## macOS deployment target

Releases ship two macOS toolchains for each architecture. The default
`gos-VERSION-macos-ARCH.zip` runs on macOS 15 and later; the
`gos-VERSION-macos12-ARCH.zip` archive runs on macOS 12 and later.
`scripts/install.sh` picks the macOS 12 archive on macOS 12 to 14.

A toolchain targets, by default, the macOS it was built for: its embedded
runtime, the Rust bindings it builds, and the executables it produces use that
`MACOSX_DEPLOYMENT_TARGET`, so programs built with the macOS 12 toolchain run on
macOS 12. Each release archive is compiled for the oldest CPU its macOS runs
on: `x86-64-v3` (AVX2) on Intel for macOS 15, `x86-64-v2` on Intel for macOS
12, which still runs on the 2013 Mac Pro, and `apple-m1` on Apple Silicon. CI
builds and tests on the current macOS runner (`xcode-27`), and every release
archive is checked to ask for no macOS newer than its own.

`MACOSX_DEPLOYMENT_TARGET` overrides the target per build; export one value
for both a toolchain build and every later `gos build` so the runtime archive,
Rust bindings, and final executable agree. A portable Intel build
(`--reproducible` or `--target`) for a macOS older than 13 uses the `x86-64-v2`
CPU baseline; for 13 and later it uses `x86-64-v3`.

Building the toolchain from source on macOS 11 is a best-effort configuration:
with `MACOSX_DEPLOYMENT_TARGET` unset, it targets the macOS it runs on.
Building requires an installed Xcode or Command Line Tools SDK
that can target the selected macOS version.
