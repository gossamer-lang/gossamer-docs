# gossamer-docs

The Gossamer website and documentation, published at
[gossamer-lang.org](https://gossamer-lang.org/): the home page, the tour, the
playground, and the docs, including the Ecosystem pages for the windowing
library, the GUI engine and the GUI library.

## Layout

| Path | Holds |
|---|---|
| `docs/` | The documentation, built with MkDocs and Material into `site/docs/`. |
| `docs/ecosystem/` | The windowing, GUI engine and GUI library documentation. |
| `landing/` | The home page, the tour and the playground component, served at the site root. |
| `mkdocs.yml`, `mkdocs_hooks.py` | The site configuration and Gossamer highlighting; a build also assembles the landing pages at the site root. |
| `tools/check-docs.gos` | Checks every example the site shows against the toolchain. |
| `tools/generated.sh` | Regenerates, or checks, the pages Gossamer's sources generate. |
| `run-site.sh` | Serves the whole site locally the way it deploys. |

## Working on it

Clone [gossamer](https://github.com/gossamer-lang/gossamer) beside this
repository; the tools find it at `../gossamer`, or at `GOSSAMER_SRC`.

```sh
pip install -r requirements.txt
mkdocs serve                 # the docs, reloading on save
./run-site.sh                # the whole site; --wasm builds the real playground VM
tools/generated.sh --check   # generated pages match Gossamer's sources
gos run tools/check-docs.gos # every fence, tour lesson and home-page listing
```

`tools/check-docs.gos` checks the Ecosystem pages against checkouts of
windowing-gos, gui-engine-gos and gui-gos, found beside this repository, in
`../goose-libs`, or at `WINDOWING_GOS`, `GUI_ENGINE_GOS` and `GUI_GOS`.
[Contributing](docs/contributing.md#docs) describes the fence markers.

## Publishing

`.github/workflows/pages.yml` builds the site on every push to `main` and
deploys it to GitHub Pages, with the playground compiled to WebAssembly from
Gossamer's `main`. A `gossamer-updated` repository dispatch rebuilds it when
the toolchain changes. `.github/workflows/ci.yml` runs the strict build, the
generated-page and example checks, and the playground smoke on every push and
pull request.

## License

Apache 2.0.
