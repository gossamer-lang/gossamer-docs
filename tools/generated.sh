#!/bin/sh
# Regenerates the pages Gossamer's sources generate, or with --check fails
# when any of them differs from what the sources would write:
#   - stdlib/ and language/ reference pages (`gos doc --emit-stdlib`)
#   - stdlib.md, stdlib_coverage.md, toolchain/lints.md,
#     toolchain/diagnostics.md and api/*.json (`cargo xtask docs-all`)
#   - every feature `gos feature-status` reports has its page
#
# GOSSAMER_SRC (default ../gossamer) is the Gossamer checkout to generate
# from; GOS (default: that checkout's target/debug/gos, built when missing)
# is the binary that emits the reference pages.
set -eu
docs=$(cd "$(dirname "$0")/.." && pwd)/docs
src=${GOSSAMER_SRC:-$(cd "$(dirname "$0")/../.." && pwd)/gossamer}
[ -f "$src/Cargo.toml" ] || { echo "generated: no Gossamer checkout at $src (set GOSSAMER_SRC)" >&2; exit 1; }
check=
[ "${1:-}" = --check ] && check=--check

gos=${GOS:-$src/target/debug/gos}
if [ -z "${GOS:-}" ]; then
    (cd "$src" && cargo build --quiet --bin gos)
fi

(cd "$src" && cargo xtask docs-all --docs "$docs" $check)
"$gos" doc --emit-stdlib "$docs/stdlib" $check
"$gos" feature-status --check --docs-root "$docs"
