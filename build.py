"""Minimal static site generator: docs/*.md -> site/*.html

Usage:
    python build.py            # build into site/
    python build.py --serve    # build, serve on http://localhost:8000 and rebuild on changes

Written with help from Claude Code (Anthropic's AI coding assistant).
"""

from __future__ import annotations

import argparse
import functools
import http.server
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "site"

MD_EXTENSIONS = ["extra", "toc", "sane_lists", "admonition"]
FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Rewrite links to other .md files so they point at the generated .html
MD_LINK = re.compile(r'(href=")(?!https?://|mailto:|#)([^"#]*?)\.md([#"])')

# Add NES.css (https://nostalgic-css.github.io/NES.css/) classes to plain Markdown output.
NES_CLASSES = [
    (re.compile(r"<table>"), '<div class="nes-table-responsive"><table class="nes-table is-bordered">'),
    (re.compile(r"</table>"), "</table></div>"),
    (re.compile(r"<ul>"), '<ul class="nes-list is-disc">'),
    (re.compile(r'<div class="admonition '), '<div class="nes-container with-title admonition '),
    (re.compile(r'<p class="admonition-title">'), '<p class="title admonition-title">'),
]


def add_nes_classes(html: str) -> str:
    for pattern, replacement in NES_CLASSES:
        html = pattern.sub(replacement, html)
    return html


def read_page(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    meta = {}
    if m := FRONT_MATTER.match(text):
        meta = yaml.safe_load(m.group(1)) or {}
        text = text[m.end():]
    return meta, text


def output_path(src: Path) -> str:
    """docs/foo/bar.md -> 'foo/bar.html' (always posix)."""
    return src.relative_to(DOCS).with_suffix(".html").as_posix()


def build() -> None:
    config = yaml.safe_load((ROOT / "config.yml").read_text(encoding="utf-8")) or {}
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=False)
    template = env.get_template("base.html")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    # Collect pages first so the navigation is known when rendering each one.
    pages = []
    for src in sorted(DOCS.rglob("*.md")):
        meta, body = read_page(src)
        url = output_path(src)
        title = meta.get("title") or src.stem.replace("-", " ").replace("_", " ").title()
        pages.append({"src": src, "url": url, "title": title, "meta": meta, "body": body})

    nav = sorted(
        (p for p in pages if not p["meta"].get("hidden")),
        key=lambda p: (p["meta"].get("nav_order", 0 if p["url"] == "index.html" else 100), p["title"]),
    )

    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    for page in pages:
        md.reset()
        content = add_nes_classes(MD_LINK.sub(r"\1\2.html\3", md.convert(page["body"])))
        depth = page["url"].count("/")
        root = "../" * depth or "./"
        html = template.render(
            site=config,
            page=page,
            content=content,
            toc=md.toc,
            nav=nav,
            root=root,
            current=page["url"],
        )
        dest = OUT / page["url"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")

    # Copy static assets and any non-markdown files from docs/ (images, PDFs, ...)
    if STATIC.exists():
        shutil.copytree(STATIC, OUT / "static")
    for f in DOCS.rglob("*"):
        if f.is_file() and f.suffix != ".md":
            dest = OUT / f.relative_to(DOCS)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)

    (OUT / ".nojekyll").touch()  # tell GitHub Pages not to run Jekyll
    print(f"Built {len(pages)} page(s) into {OUT.relative_to(ROOT)}/")


def snapshot() -> dict[Path, float]:
    files = {}
    for d in (DOCS, TEMPLATES, STATIC):
        if d.exists():
            files.update({f: f.stat().st_mtime for f in d.rglob("*") if f.is_file()})
    for f in (ROOT / "config.yml", Path(__file__)):
        files[f] = f.stat().st_mtime
    return files


def serve(port: int) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Serving on http://localhost:{port}  (Ctrl+C to stop, rebuilding on changes)")

    last = snapshot()
    try:
        while True:
            time.sleep(1)
            now = snapshot()
            if now != last:
                last = now
                # Rebuild in a fresh process so edits to build.py itself are picked up;
                # a failed build is reported but keeps the server running.
                subprocess.run([sys.executable, __file__])
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serve", action="store_true", help="serve the site and rebuild on changes")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    build()
    if args.serve:
        serve(args.port)
