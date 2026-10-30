#!/usr/bin/env bash
# Run the Gossamer website locally for browser testing. No commit, no deploy.
#
#   ./run-site.sh                serve the site (home, tour, playground, docs) on :8000
#   ./run-site.sh --port 9000    pick a port
#   ./run-site.sh --wasm         also build the real playground wasm VM from the
#                                Gossamer checkout (needs the wasm32 target and
#                                wasm-bindgen)
#   ./run-site.sh --no-docs      skip the mkdocs build (docs/ links then 404)
#
# GOSSAMER_SRC (default ../gossamer) is the Gossamer checkout the playground
# is built from; GOS (default `gos` on PATH) serves the site. ES modules and
# the esm.sh imports require http(s); opening index.html as a file:// URL
# will not load the editor. Until the wasm VM is built (--wasm or CI), the
# playground falls back to a JS stub that prints placeholder output.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${GOSSAMER_SRC:-$(dirname "$ROOT")/gossamer}"
GOS="${GOS:-gos}"
PORT=8000
BUILD_WASM=0
BUILD_DOCS=1

while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    --wasm) BUILD_WASM=1; shift ;;
    --no-docs) BUILD_DOCS=0; shift ;;
    -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
  esac
done

# The deployed layout: the landing site at the root, the docs under docs/.
# A docs build assembles both; without one, the landing pages are copied as
# they are.
SERVE_DIR="$ROOT/site"
mkdir -p "$SERVE_DIR"
if [ "$BUILD_DOCS" = 1 ] && command -v mkdocs >/dev/null 2>&1; then
  ( cd "$ROOT" && mkdocs build )
else
  [ "$BUILD_DOCS" = 1 ] && echo "note: mkdocs not found; skipping docs (pip install -r requirements.txt)" >&2
  cp -r "$ROOT/landing/." "$SERVE_DIR/"
fi

# --wasm: compile the bytecode VM to wasm and drop the wasm-bindgen module
# into the served playground dir, so the playground runs real Gossamer.
if [ "$BUILD_WASM" = 1 ]; then
  if ( cd "$SRC" && cargo build --release --target wasm32-unknown-unknown -p gossamer-playground ) \
       && command -v wasm-bindgen >/dev/null 2>&1; then
    wasm-bindgen "${CARGO_TARGET_DIR:-$SRC/target}/wasm32-unknown-unknown/release/gossamer_playground.wasm" \
      --out-dir "$SERVE_DIR/playground" --target web
    echo "built the real wasm VM into $SERVE_DIR/playground"
  else
    echo "note: could not build the playground wasm from $SRC (set GOSSAMER_SRC," \
         "or install wasm-bindgen); the playground will use the JS stub" >&2
  fi
fi

if [ -f "$SERVE_DIR/playground/gossamer_playground.js" ]; then
  RUNTIME="real wasm VM"
else
  RUNTIME="JS stub (placeholder output - build with --wasm for the real VM)"
fi

echo
echo "Gossamer site  ->  http://localhost:$PORT/"
echo "  home       http://localhost:$PORT/index.html"
echo "  tour       http://localhost:$PORT/tour/"
echo "  playground http://localhost:$PORT/playground/"
echo "  docs       http://localhost:$PORT/docs/"
echo "  runtime    $RUNTIME"
echo "  Ctrl-C to stop."
echo

# The project's own web stack serves the project's own site: a
# directory resolves to the index.html inside it, so /tour/ and
# /playground/ work exactly as they do deployed.
exec "$GOS" run "$ROOT/tools/serve_site.gos" "$PORT" "$SERVE_DIR"
