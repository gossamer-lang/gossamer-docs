"""MkDocs build hook.

Highlights ```gossamer fenced blocks with Pygments' Rust lexer, extended
with Gossamer's interpolated strings: an `f"..."` placeholder holds any
expression, which highlights as code, and may hold strings of its own.
Gossamer's surface syntax is otherwise Rust-flavoured, so the Rust lexer
is a close fit. pymdownx imports `get_lexer_by_name` as a module global, so
aliasing it there covers every fenced block the theme renders.

A `mkdocs build` also assembles the landing pages (landing/) at the site
root, the parent of `site_dir`, as the site deploys, and stamps the
version tag on the home page with the workspace version of the Gossamer
checkout the docs are built against (`GOSSAMER_SRC`, else a `gossamer`
directory beside this repository). The page refreshes the tag from
GitHub's latest release; the stamp is what it shows when that is
unreachable.

Finally, strips trailing spaces from generated HTML. Material's
script-tag rendering can emit whitespace-only lines, and checked-in
docs should stay clean under `git diff --check`.
"""

import os
import re
import shutil

from pygments.lexer import include, inherit
from pygments.lexers.rust import RustLexer
from pygments.token import Punctuation, String

# The literal text of an interpolated string, shared by both quote forms.
_INTERPOLATED_TEXT = [
    (r"\{\{|\}\}", String.Escape),
    (r"\\.", String.Escape),
    (r"\{", String.Interpol, "interpolation"),
    (r'[^"{}\\]+', String),
    (r"\}", String),
]


class GossamerLexer(RustLexer):
    """Rust's lexer with Gossamer's `f"..."` and `f\"\"\"...\"\"\"` strings."""

    name = "Gossamer"
    aliases = ["gossamer", "gos"]

    tokens = {
        "base": [
            (r'\bf"""', String, "interpolated-triple"),
            (r'\bf"', String, "interpolated"),
            inherit,
        ],
        "interpolated": [(r'"', String, "#pop"), *_INTERPOLATED_TEXT],
        "interpolated-triple": [
            (r'"""', String, "#pop"),
            (r'"', String),
            *_INTERPOLATED_TEXT,
        ],
        # A placeholder: code up to its own `}`, whose first top-level
        # single `:` starts the format spec.
        "interpolation": [
            (r"\}", String.Interpol, "#pop"),
            (r":(?!:)[^{}\n]*(?=\})", String.Interpol),
            (r"\{", Punctuation, "interpolation-block"),
            include("base"),
        ],
        "interpolation-block": [
            (r"\}", Punctuation, "#pop"),
            (r"\{", Punctuation, "#push"),
            include("base"),
        ],
    }


def _gossamer_checkout(config_file_path: str) -> str:
    """The Gossamer source checkout the docs describe, or "" when none is found."""
    explicit = os.environ.get("GOSSAMER_SRC", "")
    if explicit:
        return explicit
    root = os.path.dirname(os.path.abspath(config_file_path))
    sibling = os.path.join(os.path.dirname(root), "gossamer")
    return sibling if os.path.isfile(os.path.join(sibling, "Cargo.toml")) else ""


def _workspace_version(config_file_path: str) -> str:
    """Read the workspace version from the Gossamer checkout's Cargo.toml."""
    checkout = _gossamer_checkout(config_file_path)
    if not checkout:
        return ""
    cargo = os.path.join(checkout, "Cargo.toml")
    text = open(cargo, encoding="utf-8").read()
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else ""


def _assemble_landing(config_file_path: str, site_root: str) -> None:
    """Copy landing/ to the site root, stamping the version tag in index.html."""
    root = os.path.dirname(os.path.abspath(config_file_path))
    shutil.copytree(os.path.join(root, "landing"), site_root, dirs_exist_ok=True)
    version = _workspace_version(config_file_path)
    if not version:
        return
    page = os.path.join(site_root, "index.html")
    original = open(page, encoding="utf-8").read()
    # The runtime refresh writes the same shape: " · " and the release tag.
    stamped = re.sub(
        r'(<span class="ver-tag">)[^<]*(</span>)',
        rf"\g<1> &middot; v{version}\2",
        original,
    )
    open(page, "w", encoding="utf-8").write(stamped)


def _strip_trailing_html_whitespace(site_dir: str) -> None:
    """Remove trailing spaces and tabs from generated HTML files."""
    for root, _, files in os.walk(site_dir):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(root, name)
            original = open(path, encoding="utf-8").read()
            lines = original.splitlines(keepends=True)
            stripped = "".join(
                line.rstrip(" \t\r\n") + ("\n" if line.endswith(("\n", "\r")) else "")
                for line in lines
            )
            if stripped != original:
                open(path, "w", encoding="utf-8").write(stripped)


def on_config(config):
    import pymdownx.highlight as highlight

    original = highlight.get_lexer_by_name

    def get_lexer_by_name(name, **options):
        if name in ("gossamer", "gos"):
            return GossamerLexer(**options)
        return original(name, **options)

    highlight.get_lexer_by_name = get_lexer_by_name
    return config


_command = ""


def on_startup(command, dirty):
    global _command
    _command = command


def on_post_build(config):
    _strip_trailing_html_whitespace(config["site_dir"])
    # `mkdocs serve` builds into a temporary directory whose parent is no
    # site root, and serves the docs alone.
    if _command == "build":
        site_root = os.path.dirname(os.path.abspath(config["site_dir"]))
        _assemble_landing(config["config_file_path"], site_root)
