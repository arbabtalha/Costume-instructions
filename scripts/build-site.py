#!/usr/bin/env python3
"""Build the static documentation site and searchable repository file index.

The curated docs stay in a self-contained HTML file. A generated JSON sidecar
holds committed text files and is loaded only when a user searches or previews
one. No third-party dependencies, CDN, or remote fonts are required.

Usage:
    python3 scripts/build-site.py [--out index.html] [--files-out repository-files.json] [--check]
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parent.parent
MAX_INDEXED_FILE_BYTES = 2_000_000
SITE_FILE = "index.html"
REPOSITORY_INDEX_NAME = "repository-files.json"

# id, title, group, source file
DOCS: list[tuple[str, str, str, str]] = [
    ("rules", "Rules (AGENTS.md)", "Start here", "AGENTS.md"),
    ("core", "00 - Core voice and rules", "Instructions", "instructions/00-core.md"),
    ("webapp", "10 - Webapp build protocol", "Instructions", "instructions/10-webapp-generation.md"),
    ("uiux", "20 - UI/UX rules", "Instructions", "instructions/20-ui-ux-rules.md"),
    ("stacks", "30 - Stack playbooks", "Instructions", "instructions/30-stack-playbooks.md"),
    ("quality", "40 - Quality gates", "Instructions", "instructions/40-quality-gates.md"),
    ("recipes", "50 - Prompt recipes", "Instructions", "instructions/50-prompt-recipes.md"),
    ("tools", "60 - Using the skill and MCP", "Instructions", "instructions/60-mcp-and-skill-usage.md"),
    ("skills", "Skills reference", "Assets", "skills/README.md"),
    ("mcp", "21st.dev MCP setup", "Assets", "mcp/21st-mcp.md"),
    ("starters", "Starters", "Assets", "starters/README.md"),
]

SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, used: set[str]) -> str:
    slug = SLUG_RE.sub("-", text.lower()).strip("-") or "section"
    candidate, n = slug, 2
    while candidate in used:
        candidate = f"{slug}-{n}"
        n += 1
    used.add(candidate)
    return candidate


def inline(text: str) -> str:
    """Render the supported inline markdown without trusting source HTML or URLs."""
    fragments: list[str] = []

    def stash(fragment: str) -> str:
        fragments.append(fragment)
        return f"\x00{len(fragments) - 1}\x00"

    def code_span(match: re.Match[str]) -> str:
        return stash(f"<code>{html.escape(match.group(1), quote=False)}</code>")

    def markdown_link(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2).strip()
        if any(ord(char) < 0x20 for char in target):
            return html.escape(label, quote=False)
        try:
            parsed = urlsplit(target)
        except ValueError:
            return html.escape(label, quote=False)
        scheme = parsed.scheme.lower()
        safe_scheme = scheme in {"", "http", "https", "mailto"}
        safe_network_url = scheme not in {"http", "https"} or bool(parsed.netloc)
        safe_relative = bool(scheme or not parsed.netloc or target.startswith("//"))
        if (
            not safe_scheme
            or not safe_network_url
            or not safe_relative
        ):
            return html.escape(label, quote=False)
        escaped_target = html.escape(target, quote=True)
        escaped_label = html.escape(label, quote=False)
        return stash(f'<a href="{escaped_target}" target="_blank" rel="noopener noreferrer">{escaped_label}</a>')

    text = re.sub(r"`([^`]+)`", code_span, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", markdown_link, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda match: fragments[int(match.group(1))], text)
    return text


LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|[\s:\-|]+\|\s*$")


def render_list(lines: list[str], start: int) -> tuple[str, int]:
    """Render one Markdown list, keeping nested lists inside their parent <li>."""
    first = LIST_RE.match(lines[start])
    if first is None:
        return "", start

    base_indent = len(first.group(1).expandtabs(2))
    list_kind = "ol" if first.group(2)[0].isdigit() else "ul"
    start_number = int(first.group(2)[:-1]) if list_kind == "ol" else 1
    start_attr = f' start="{start_number}"' if list_kind == "ol" and start_number != 1 else ""
    out = [f"<{list_kind}{start_attr}>"]
    item_open = False
    i = start

    while i < len(lines):
        item = LIST_RE.match(lines[i])
        if item is not None:
            indent = len(item.group(1).expandtabs(2))
            if indent < base_indent:
                break
            if indent > base_indent:
                if not item_open:
                    break
                nested, i = render_list(lines, i)
                out.append(nested)
                continue

            kind = "ol" if item.group(2)[0].isdigit() else "ul"
            if kind != list_kind:
                break
            if item_open:
                out.append("</li>")

            checkbox = re.match(r"^\[( |x|X)\]\s*(.*)$", item.group(3))
            if checkbox:
                checked = " checked" if checkbox.group(1).lower() == "x" else ""
                accessible_name = html.escape(plain_markdown(checkbox.group(2)), quote=True)
                out.append(f'<li class="task"><input type="checkbox" aria-label="{accessible_name}" disabled{checked}> ')
                out.append(inline(checkbox.group(2)))
            else:
                out.append(f"<li>{inline(item.group(3))}")
            item_open = True
            i += 1
            continue

        if not lines[i].strip():
            next_i = i + 1
            while next_i < len(lines) and not lines[next_i].strip():
                next_i += 1
            next_item = LIST_RE.match(lines[next_i]) if next_i < len(lines) else None
            if next_item is not None and len(next_item.group(1).expandtabs(2)) >= base_indent:
                i = next_i
                continue
            break

        if lines[i][0].isspace() and item_open:
            out.append(" " + inline(lines[i].strip()))
            i += 1
            continue
        break

    if item_open:
        out.append("</li>")
    out.append(f"</{list_kind}>")
    return "".join(out), i


def md_to_html(md: str, used_slugs: set[str]) -> tuple[str, list[dict[str, str]]]:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    headings: list[dict[str, str]] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # fenced code
        fence = re.match(r"^\s*(```|~~~)\s*([\w.+-]*)\s*$", line)
        if fence:
            marker, lang = fence.group(1), fence.group(2)
            i += 1
            code: list[str] = []
            while i < len(lines) and not re.match(rf"^\s*{marker}\s*$", lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        # horizontal rule
        if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # heading
        heading = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if heading:
            level = min(len(heading.group(1)) + 1, 6)  # h1 -> h2 on the page
            text = heading.group(2)
            slug = slugify(re.sub(r"[`*]", "", text), used_slugs)
            plain = re.sub(r"[`*]", "", text)
            if level <= 4:
                headings.append({"id": slug, "text": plain, "level": str(level)})
            out.append(f'<h{level} id="{slug}">{inline(text)}</h{level}>')
            i += 1
            continue

        # table
        if line.strip().startswith("|") and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1]):
            header_cells = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            thead = "".join(f"<th>{inline(c)}</th>" for c in header_cells)
            tbody = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in rows
            )
            out.append(f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>')
            continue

        # blockquote
        if line.lstrip().startswith(">"):
            quote: list[str] = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(quote))}</p></blockquote>")
            continue

        # list (including nested and ordered lists)
        if LIST_RE.match(line):
            list_html, i = render_list(lines, i)
            out.append(list_html)
            continue

        # blank
        if not line.strip():
            i += 1
            continue

        # paragraph
        para: list[str] = []
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^\s*(#{1,6}\s|```|~~~|>|\||-{3,}|\*{3,}|_{3,})", lines[i]
        ) and not LIST_RE.match(lines[i]):
            para.append(lines[i].strip())
            i += 1
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
        else:  # safety net, never loop forever
            i += 1

    return "\n".join(out), headings


def tracked_file_paths() -> list[str]:
    """Return committed paths only, so local secrets and scratch files stay private."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )
    except OSError as error:
        raise RuntimeError("Git is required to build the public file index safely.") from error
    if result.returncode != 0:
        raise RuntimeError("Run the site builder inside a Git checkout to avoid publishing untracked files.")
    paths = [os.fsdecode(name) for name in result.stdout.split(b"\0") if name]
    return sorted(
        path for path in paths
        if path not in {REPOSITORY_INDEX_NAME, ".git"} and not path.startswith(".git/")
    )


def classify_file(path: str, is_binary: bool) -> str:
    name = Path(path).name.lower()
    suffix = Path(path).suffix.lower()
    if path == SITE_FILE:
        return "Website"
    if is_binary:
        return "Asset"
    if suffix in {".md", ".mdc", ".txt", ".rst"}:
        return "Documentation"
    if suffix in {".csv", ".json", ".jsonc", ".jsonl", ".toml", ".yaml", ".yml"}:
        return "Data & config"
    if suffix in {".py", ".sh", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".html", ".css"}:
        return "Source code"
    if name.startswith(".") or suffix in {".xml", ".svg", ".ini", ".cfg"}:
        return "Config & metadata"
    return "Text file"


def build_repository_file_data() -> tuple[list[dict[str, object]], dict[str, object]]:
    """Build a public manifest and searchable text index from committed files."""
    manifest: list[dict[str, object]] = []
    indexed_text: list[dict[str, str]] = []

    for rel in tracked_file_paths():
        path = REPO / rel
        if not path.is_file():
            continue
        data = path.read_bytes()
        is_site = rel == SITE_FILE
        decoded: str | None = None
        if not is_site and b"\0" not in data:
            try:
                decoded = data.decode("utf-8")
            except UnicodeDecodeError:
                decoded = None
        content = decoded if decoded is not None and len(data) <= MAX_INDEXED_FILE_BYTES else None
        is_binary = decoded is None and not is_site
        manifest.append(
            {
                "path": rel,
                "size": None if is_site else len(data),
                "kind": classify_file(rel, is_binary),
                "isText": decoded is not None or is_site,
                "searchable": content is not None,
                "currentSite": is_site,
            }
        )
        if content is not None:
            indexed_text.append({"path": rel, "content": content})

    return manifest, {"version": 1, "files": indexed_text}


def plain_markdown(text: str) -> str:
    """Remove Markdown structure while keeping words, paths, and code searchable."""
    text = re.sub(r"(?m)^\s*`{3,}[^\n]*$|^\s*`{3,}\s*$", " ", text)
    text = re.sub(r"(?m)^\s*\|?[-:| ]+\|?\s*$", " ", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 \2", text)
    text = re.sub(r"(?m)^\s*#{1,6}\s+", "", text)
    text = re.sub(r"(?m)^\s*(?:[-*+]|\d+\.)\s+", "", text)
    text = re.sub(r"[|`*#>]", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def search_entries_for_document(
    doc_id: str,
    title: str,
    markdown: str,
    headings: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Split a document into searchable blocks with anchors matching rendered headings."""
    anchors_by_heading: dict[str, list[str]] = {}
    for heading in headings:
        key = re.sub(r"[`*]", "", heading["text"]).lower()
        anchors_by_heading.setdefault(key, []).append(heading["id"])
    heading_uses: dict[str, int] = {}
    chunks = re.split(r"\n\s*\n", markdown)
    current_heading = title
    current_anchor = headings[0]["id"] if headings else ""
    search: list[dict[str, str]] = []
    for chunk in chunks:
        stripped = chunk.strip()
        if not stripped:
            continue
        head = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", stripped)
        if head:
            current_heading = re.sub(r"[`*]", "", head.group(2))
            key = current_heading.lower()
            anchor_ids = anchors_by_heading.get(key, [])
            position = heading_uses.get(key, 0)
            if position < len(anchor_ids):
                current_anchor = anchor_ids[position]
                heading_uses[key] = position + 1
            continue
        text = plain_markdown(stripped)
        if len(text) < 12:
            continue
        search.append(
            {
                "doc": doc_id,
                "docTitle": title,
                "anchor": current_anchor,
                "heading": current_heading,
                "text": text,
            }
        )
    return search


SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Costume Webapp Kit - instructions, design intelligence, MCP for AI webapp generation</title>
<meta name="description" content="One repo that makes any AI coding agent build production web apps: a 25-rule build protocol, offline UI/UX design intelligence, the 21st.dev MCP server, agents, commands and installers.">
<meta property="og:title" content="Costume Webapp Kit">
<meta property="og:description" content="Instructions + design intelligence + MCP for AI webapp generation.">
<meta property="og:type" content="website">
<meta name="theme-color" content="#fbfaf7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#101014" media="(prefers-color-scheme: dark)">
<style>
  :root {
    --bg: #fbfaf7; --surface: #fff; --surface-alt: #f2efe8; --border: #e4dfd3;
    --text: #16151a; --muted: #625f6b; --accent: #2f6f4f; --accent-soft: #e3f0e8;
    --on-accent: #fff; --highlight: #9a5b12; --code-bg: #f4f2ee; --focus: #2f6f4f;
    --radius: .75rem; --radius-lg: 1.1rem; --sidebar: 17rem; --container: 78rem;
    --font: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #101014; --surface: #17171c; --surface-alt: #1e1e24; --border: #2e2e36;
      --text: #f2f1f5; --muted: #a6a3b0; --accent: #78cf9f; --accent-soft: #1b2d24;
      --on-accent: #0d120f; --highlight: #e0aa63; --code-bg: #1b1b21; --focus: #78cf9f;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text); font-family: var(--font);
    line-height: 1.65; -webkit-font-smoothing: antialiased; font-size: 16px;
  }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  :focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; border-radius: 4px; }
  code, pre { font-family: var(--mono); font-size: .875em; }
  code { background: var(--code-bg); border: 1px solid var(--border); border-radius: 5px; padding: .1em .35em; }
  pre { background: var(--code-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.1rem; overflow-x: auto; position: relative; }
  pre code { background: none; border: 0; padding: 0; }
  hr { border: 0; border-top: 1px solid var(--border); margin: 2.5rem 0; }
  .skip { position: absolute; left: 1rem; top: -3rem; background: var(--text); color: var(--bg); padding: .4rem .8rem; border-radius: 6px; z-index: 50; }
  .skip:focus { top: 1rem; }

  header.top {
    position: sticky; top: 0; z-index: 40; background: color-mix(in srgb, var(--bg) 90%, transparent);
    backdrop-filter: blur(10px); border-bottom: 1px solid var(--border);
  }
  .top-inner { max-width: var(--container); margin: 0 auto; padding: .7rem 1.25rem; display: flex; align-items: center; gap: 1rem; }
  .logo { display: flex; align-items: center; gap: .55rem; font-weight: 700; letter-spacing: -.02em; color: var(--text); font-size: 1rem; }
  .logo svg { width: 1.35rem; height: 1.35rem; color: var(--accent); }
  .top nav { margin-left: auto; display: none; gap: 1.1rem; font-size: .9rem; }
  @media (min-width: 60rem) { .top nav { display: flex; } }
  .top nav a { min-height: 2.75rem; display: inline-flex; align-items: center; color: var(--muted); }
  .top nav a:hover { color: var(--text); }
  .search { position: relative; flex: 1; min-width: 0; max-width: 20rem; margin-left: auto; }
  .search input {
    width: 100%; min-width: 0; min-height: 2.75rem; font: inherit; font-size: .875rem; padding: .5rem .8rem; color: var(--text);
    background: var(--surface); border: 1px solid var(--border); border-radius: 999px;
  }
  .search input::placeholder { color: var(--muted); }
  .results {
    position: absolute; top: calc(100% + .4rem); left: 0; right: 0; background: var(--surface);
    border: 1px solid var(--border); border-radius: var(--radius); box-shadow: 0 24px 48px -24px rgba(0,0,0,.35);
    max-height: 22rem; overflow-y: auto; display: none; z-index: 30;
  }
  .results[data-open="true"] { display: block; }
  .results button {
    display: block; width: 100%; min-height: 2.75rem; text-align: left; font: inherit; font-size: .85rem; padding: .6rem .8rem;
    background: none; border: 0; border-bottom: 1px solid var(--border); color: var(--text); cursor: pointer;
  }
  .results button:hover, .results button:focus-visible { background: var(--surface-alt); }
  .results button span { display: block; color: var(--muted); font-size: .78rem; overflow-wrap: anywhere; }
  .results button em { font-style: normal; color: var(--muted); }
  .results .empty { padding: .8rem; color: var(--muted); font-size: .85rem; }
  .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }

  .layout { max-width: var(--container); margin: 0 auto; padding: 1.5rem 1.25rem 4rem; display: grid; gap: 2.5rem; }
  @media (min-width: 60rem) { .layout { grid-template-columns: var(--sidebar) minmax(0, 1fr); gap: 3rem; } }
  aside { font-size: .875rem; }
  @media (min-width: 60rem) { aside { position: sticky; top: 4.5rem; align-self: start; max-height: calc(100vh - 6rem); overflow-y: auto; } }
  aside h2 { font-size: .7rem; text-transform: uppercase; letter-spacing: .14em; color: var(--muted); margin: 1.4rem 0 .5rem; }
  aside ul { list-style: none; margin: 0; padding: 0; display: grid; gap: .1rem; }
  aside button {
    width: 100%; min-height: 2.75rem; text-align: left; font: inherit; font-size: .875rem; padding: .45rem .6rem; border-radius: 7px;
    border: 0; background: none; color: var(--muted); cursor: pointer;
  }
  aside button:hover { background: var(--surface-alt); color: var(--text); }
  aside button[aria-current="true"] { background: var(--accent-soft); color: var(--text); font-weight: 600; }

  main { min-width: 0; }
  .doc-head { margin-bottom: 1.5rem; display: flex; flex-wrap: wrap; gap: .75rem; align-items: center; justify-content: space-between; }
  .doc-head h1 { font-size: 1.9rem; margin: 0; letter-spacing: -.025em; }
  .doc-actions { display: flex; gap: .5rem; flex-wrap: wrap; }
  .btn {
    min-height: 2.75rem; display: inline-flex; align-items: center; justify-content: center;
    font: inherit; font-size: .8rem; font-weight: 600; cursor: pointer; padding: .45rem .85rem;
    border-radius: 999px; border: 1px solid var(--border); background: var(--surface); color: var(--text);
    transition: background 150ms ease, border-color 150ms ease;
  }
  .btn:hover { background: var(--surface-alt); }
  .btn-primary { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
  .btn-primary:hover { filter: brightness(1.08); background: var(--accent); }

  .content h2 { font-size: 1.45rem; margin: 2.5rem 0 .75rem; letter-spacing: -.02em; scroll-margin-top: 5rem; }
  .content h2:first-child { margin-top: 0; }
  .content h3 { font-size: 1.1rem; margin: 1.75rem 0 .5rem; scroll-margin-top: 5rem; }
  .content h4 { font-size: .95rem; margin: 1.25rem 0 .4rem; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
  .content p, .content li { color: var(--text); }
  .content ul, .content ol { padding-left: 1.35rem; }
  .content li { margin: .3rem 0; }
  .content li.task { list-style: none; margin-left: -1.1rem; }
  .content blockquote { margin: 1.25rem 0; padding: .6rem 1rem; border-left: 3px solid var(--accent); background: var(--surface-alt); border-radius: 0 var(--radius) var(--radius) 0; }
  .content blockquote p { margin: 0; color: var(--muted); }
  .table-wrap { overflow-x: auto; margin: 1.25rem 0; }
  table { width: 100%; border-collapse: collapse; font-size: .875rem; }
  th, td { text-align: left; padding: .55rem .7rem; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { background: var(--surface-alt); font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
  .copy-code {
    position: absolute; top: .5rem; right: .5rem; min-height: 2.75rem; font: inherit; font-size: .72rem; padding: .35rem .7rem;
    border-radius: 6px; border: 1px solid var(--border); background: var(--surface); color: var(--muted); cursor: pointer; opacity: 0;
    transition: opacity 150ms ease;
  }
  pre:hover .copy-code, .copy-code:focus-visible { opacity: 1; }

  .hero { padding: 1rem 0 2rem; }
  .hero h1 { font-size: clamp(1.9rem, 4.2vw, 2.9rem); letter-spacing: -.03em; margin: 0 0 .75rem; line-height: 1.1; }
  .hero p.lede { font-size: 1.1rem; color: var(--muted); max-width: 46rem; }
  .pill { display: inline-block; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; color: var(--highlight); font-weight: 700; margin-bottom: .6rem; }
  .grid { display: grid; gap: 1rem; grid-template-columns: 1fr; margin: 1.5rem 0; }
  @media (min-width: 46rem) { .grid.two { grid-template-columns: repeat(2, 1fr); } .grid.three { grid-template-columns: repeat(3, 1fr); } }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.25rem; }
  .card h3 { margin: 0 0 .4rem; font-size: 1rem; }
  .card p { margin: 0; color: var(--muted); font-size: .9rem; }
  .card .n { font-family: var(--mono); font-size: .8rem; color: var(--highlight); }
  .steps { counter-reset: s; list-style: none; padding: 0; display: grid; gap: .9rem; }
  .steps li { position: relative; padding-left: 2.2rem; counter-increment: s; }
  .steps li::before {
    content: counter(s); position: absolute; left: 0; top: .1rem; width: 1.6rem; height: 1.6rem;
    display: grid; place-items: center; border-radius: 999px; background: var(--accent-soft); color: var(--accent);
    font-size: .8rem; font-weight: 700;
  }
  .note { font-size: .85rem; color: var(--muted); border-top: 1px solid var(--border); margin-top: 2rem; padding-top: 1rem; }
  .file-toolbar { display: flex; flex-wrap: wrap; gap: .6rem; margin: 1.25rem 0; }
  .file-toolbar input, .file-toolbar select {
    min-height: 2.75rem; font: inherit; font-size: .9rem; color: var(--text); background: var(--surface);
    border: 1px solid var(--border); border-radius: var(--radius); padding: .55rem .75rem;
  }
  .file-toolbar input { flex: 1 1 16rem; min-width: 0; }
  .file-toolbar select { flex: 0 1 12rem; }
  .file-count { color: var(--muted); font-size: .85rem; margin: .5rem 0 1rem; }
  .repo-file-list { list-style: none; padding: 0; margin: 0; display: grid; gap: .55rem; }
  .repo-file-row { display: flex; align-items: center; justify-content: space-between; gap: .8rem; padding: .55rem .7rem; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
  .file-open { flex: 1; min-width: 0; min-height: 2.75rem; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: .15rem; border: 0; background: none; color: var(--text); text-align: left; cursor: pointer; font: inherit; }
  .file-open:hover strong { color: var(--accent); text-decoration: underline; }
  .file-open strong { overflow-wrap: anywhere; }
  .file-meta { color: var(--muted); font-size: .76rem; }
  .file-row-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: .35rem; }
  .file-action { display: inline-flex; align-items: center; justify-content: center; min-height: 2.75rem; padding: .35rem .65rem; border: 1px solid var(--border); border-radius: 999px; background: var(--surface); color: var(--text); font-size: .78rem; font-weight: 600; white-space: nowrap; }
  .file-action:hover { background: var(--surface-alt); text-decoration: none; }
  .file-preview { min-width: 0; }
  .file-preview pre { max-height: 72vh; overflow: auto; white-space: pre; }
  .file-preview pre code { overflow-wrap: normal; }
  .file-path { color: var(--muted); font-family: var(--mono); font-size: .85rem; overflow-wrap: anywhere; }
  .file-alert { padding: .8rem 1rem; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface-alt); color: var(--muted); }
  .file-empty { padding: 1rem; border: 1px dashed var(--border); border-radius: var(--radius); color: var(--muted); }
  @media (max-width: 42rem) {
    .repo-file-row { align-items: flex-start; flex-direction: column; }
    .file-row-actions { width: 100%; justify-content: flex-start; }
    .file-toolbar select { flex: 1 1 auto; }
  }
  @media (prefers-reduced-motion: reduce) { * { transition-duration: .01ms !important; } html { scroll-behavior: auto; } }
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="top">
  <div class="top-inner">
    <a class="logo" href="#home" aria-label="Costume Webapp Kit home">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 7h16M4 12h10M4 17h7"/></svg>
      Costume Webapp Kit
    </a>
    <nav aria-label="Quick links">
      <a href="https://github.com/arbabtalha/Costume-instructions">GitHub</a>
      <a href="#skills">Skills</a>
      <a href="#mcp">MCP</a>
      <a href="#/files">Files</a>
    </nav>
    <div class="search">
      <label class="sr-only" for="q">Search all project docs and files</label>
      <input id="q" type="search" placeholder="Search docs and files..." autocomplete="off" aria-controls="results" aria-expanded="false">
      <div class="results" id="results" role="region" aria-label="Search results" data-open="false"></div>
      <p class="sr-only" id="search-status" aria-live="polite"></p>
    </div>
  </div>
</header>

<div class="layout">
  <aside>
    <h2>Start here</h2>
    <ul id="nav-start"></ul>
    <h2>Instructions</h2>
    <ul id="nav-instructions"></ul>
    <h2>Assets</h2>
    <ul id="nav-assets"></ul>
    <h2>Repository</h2>
    <ul id="nav-repository"></ul>
  </aside>
  <main id="main"></main>
</div>

<script>
const DOCS = __DOCS__;
const SEARCH = __SEARCH__;
const FILES = __FILES__;
const REPOSITORY_INDEX_URL = __REPOSITORY_INDEX_URL__;
const REPOSITORY_URL = 'https://github.com/arbabtalha/Costume-instructions';

const HOME = `
<section class="hero">
  <p class="pill">Instructions &middot; design intelligence &middot; MCP</p>
  <h1>Make any AI coding agent build web apps like a senior team.</h1>
  <p class="lede">One repository with the rules, the design database, the component source, and the installers.
  Clone it or install it into a project in one command, then any agent stops producing demo-grade UI.</p>
</section>
<div class="doc-actions" style="margin-bottom:1.25rem">
  <button class="btn btn-primary" data-copy="git clone https://github.com/arbabtalha/Costume-instructions && cd Costume-instructions && ./scripts/setup.sh --target . --client all">Copy install command</button>
  <button class="btn" data-goto="rules">Read the rules</button>
  <button class="btn" data-goto="mcp">Set up the MCP</button>
  <button class="btn" data-goto="skills">Design skill</button>
  <button class="btn" data-goto="files">Browse all files</button>
</div>

<div class="grid two">
  <article class="card">
    <h3>Instructions that are actually enforced</h3>
    <p>Seven files: voice and accuracy, the build protocol with 25 numbered rules, the UI/UX priority order,
    stack playbooks for six stacks, quality gates you can run, prompt recipes, and tool usage rules.
    Every agent reads them at the start of a task.</p>
  </article>
  <article class="card">
    <h3>Design intelligence, offline</h3>
    <p>UI/UX Pro Max: 79 styles, 192 palettes with reasoning, 74 font pairings, 119 UX guidelines,
    25 chart types, 22 stacks. A local Python script answers in milliseconds, with no API key.</p>
  </article>
  <article class="card">
    <h3>21st.dev MCP wired in</h3>
    <p>The component catalog and hosted UI generation as MCP tools (search, get_component, search_logo, generate),
    with configs for Claude Code, Cursor, VS Code, Codex, Windsurf and Gemini.</p>
  </article>
  <article class="card">
    <h3>Agents, commands, starter</h3>
    <p>Four subagents (architect, ui-ux-designer, implementer, qa-reviewer), five slash commands,
    and a dependency-free landing page that demonstrates every rule at once.</p>
  </article>
</div>

<h2 id="home-install">Install it in one command</h2>
<p>The installer sets up whichever editors you use: it copies the skills into the right directory,
writes the instruction files, adds <code>AGENTS.md</code>, and merges the MCP config into your client
without clobbering existing settings.</p>
<pre><code>git clone https://github.com/arbabtalha/Costume-instructions
cd Costume-instructions

# into the current project, every client
./scripts/setup.sh --client all

# or into another project, one client
./scripts/setup.sh --target ~/code/my-app --client claude

# MCP only, or a dry run first
./scripts/install-mcp.sh --client cursor
./scripts/setup.sh --client all --dry-run</code></pre>
<p>Then set your key, restart the editor, and check the connection:</p>
<pre><code>export API_KEY_21ST="paste-key-from-21st.dev/mcp"   # free, instant
/mcp                                                # Claude Code: should list "21st"</code></pre>

<h2 id="home-client">What lands where</h2>
<div class="table-wrap"><table>
<thead><tr><th>Client</th><th>Instruction file</th><th>Skills directory</th><th>MCP config</th></tr></thead>
<tbody>
<tr><td>Claude Code</td><td>CLAUDE.md + AGENTS.md</td><td>.claude/skills/</td><td>.mcp.json</td></tr>
<tr><td>Cursor</td><td>.cursor/rules/*.mdc + AGENTS.md</td><td>.cursor/skills/</td><td>.cursor/mcp.json</td></tr>
<tr><td>VS Code / Copilot</td><td>.github/copilot-instructions.md</td><td>.github/prompts/</td><td>.vscode/mcp.json</td></tr>
<tr><td>Codex CLI</td><td>AGENTS.md</td><td>.agents/skills/</td><td>~/.codex/config.toml</td></tr>
<tr><td>Gemini CLI</td><td>GEMINI.md + AGENTS.md</td><td>.gemini/skills/</td><td>~/.gemini/settings.json</td></tr>
<tr><td>Windsurf</td><td>.windsurf/rules/costume.md</td><td>.windsurf/skills/</td><td>~/.codeium/windsurf/mcp_config.json</td></tr>
</tbody></table></div>

<h2 id="home-use">The loop an agent follows</h2>
<ol class="steps">
  <li><strong>Intake</strong> - product, primary action, stack, constraints, definition of done. Questions only when the answer changes the architecture.</li>
  <li><strong>Design system</strong> - run the local search, persist <code>MASTER.md</code>, write the tokens.</li>
  <li><strong>Build</strong> - shell, primitives, sections, then every loading, empty, error and success state.</li>
  <li><strong>Polish</strong> - motion that means something, SEO metadata, image and font budgets.</li>
  <li><strong>Verify</strong> - typecheck, lint, build, keyboard pass, contrast, four widths, reduced motion.</li>
  <li><strong>Report</strong> - what was built, what ran, what was checked, what is unfinished.</li>
</ol>

<p class="note">Documentation is generated from the repository's markdown. The file library is generated from committed repository files. Run <code>make site</code> after editing sources; do not edit the generated outputs by hand.</p>
`;

const main = document.getElementById('main');
const navs = {
  'Start here': document.getElementById('nav-start'),
  Instructions: document.getElementById('nav-instructions'),
  Assets: document.getElementById('nav-assets'),
  Repository: document.getElementById('nav-repository')
};

function docById(id) { return DOCS.find(d => d.id === id); }
function fileByPath(path) { return FILES.find(file => file.path === path); }
function safeText(tag, text, className) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}
function fileUrl(path) {
  return path.split('/').map(part => encodeURIComponent(part)).join('/');
}
function githubBlobUrl(path) {
  return `${REPOSITORY_URL}/blob/main/${fileUrl(path)}`;
}
function setCurrentNav(id) {
  for (const button of document.querySelectorAll('aside button')) {
    button.setAttribute('aria-current', String(button.dataset.id === id));
  }
}

function render(id, anchor) {
  const doc = docById(id);
  if (!doc) { renderHome(); return; }
  main.innerHTML = `<div class="doc-head"><h1>${doc.title}</h1>
    <div class="doc-actions">
      <button class="btn" data-copy-doc="${doc.id}">Copy markdown</button>
      <button class="btn" data-download-doc="${doc.id}">Download .md</button>
      <a class="btn" href="${githubBlobUrl(doc.source)}" target="_blank" rel="noopener noreferrer">View source</a>
      <button class="btn" data-goto="files">All files</button>
    </div></div><div class="content">${doc.html}</div>`;
  setCurrentNav(id);
  if (anchor) {
    const el = document.getElementById(anchor);
    if (el) { el.scrollIntoView(); return; }
  }
  window.scrollTo({ top: 0 });
}

function renderHome() {
  main.innerHTML = HOME;
  setCurrentNav('home');
  window.scrollTo({ top: 0 });
}

let repositoryContent = null;
let repositoryIndexPromise = null;
const normalizedFileContents = new Map();

async function loadRepositoryIndex() {
  if (repositoryContent) return repositoryContent;
  if (!repositoryIndexPromise) {
    const indexUrl = new URL(REPOSITORY_INDEX_URL, document.baseURI);
    repositoryIndexPromise = fetch(indexUrl.href, { cache: 'force-cache' })
      .then(response => {
        if (!response.ok) throw new Error(`File index request failed (${response.status}).`);
        return response.json();
      })
      .then(data => {
        if (data.version !== 1 || !Array.isArray(data.files)) throw new Error('File index has an unsupported format.');
        repositoryContent = new Map(data.files.map(file => [file.path, file.content]));
        return repositoryContent;
      })
      .catch(error => {
        repositoryIndexPromise = null;
        throw error;
      });
  }
  return repositoryIndexPromise;
}

async function loadFileText(path) {
  let indexErrorMessage = '';
  try {
    const contents = await loadRepositoryIndex();
    if (contents.has(path)) return contents.get(path);
  } catch (error) {
    indexErrorMessage = error.message;
  }
  const response = await fetch(fileUrl(path));
  if (!response.ok) {
    const detail = indexErrorMessage ? ` Search-index error: ${indexErrorMessage}` : '';
    throw new Error(`Unable to fetch the file (${response.status}).${detail}`);
  }
  return response.text();
}

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return 'generated site';
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB'];
  let value = bytes / 1024;
  let unit = units[0];
  for (let i = 1; value >= 1024 && i < units.length; i += 1) {
    value /= 1024;
    unit = units[i];
  }
  return `${value.toFixed(value < 10 ? 1 : 0)} ${unit}`;
}

function renderFileCatalog() {
  main.replaceChildren();
  setCurrentNav('files');

  const heading = safeText('h1', 'Repository files');
  const intro = safeText('p', `Browse, preview, copy, or download the ${FILES.length} tracked source and asset files. Indexed text files support full-text search; binary assets have direct download links.`);
  const fileHeader = document.createElement('div');
  fileHeader.className = 'doc-head';
  fileHeader.appendChild(heading);
  const actions = document.createElement('div');
  actions.className = 'doc-actions';
  const overview = safeText('a', 'Overview', 'btn');
  overview.href = '#home';
  actions.appendChild(overview);
  const github = safeText('a', 'GitHub repository', 'btn');
  github.href = REPOSITORY_URL;
  github.target = '_blank';
  github.rel = 'noopener noreferrer';
  actions.appendChild(github);
  fileHeader.appendChild(actions);
  main.append(fileHeader, intro);

  const toolbar = document.createElement('div');
  toolbar.className = 'file-toolbar';
  const filterLabel = safeText('label', 'Filter files by name or folder');
  filterLabel.htmlFor = 'file-filter';
  filterLabel.className = 'sr-only';
  const filterInput = document.createElement('input');
  filterInput.id = 'file-filter';
  filterInput.type = 'search';
  filterInput.placeholder = 'Filter files by name or folder...';
  filterInput.autocomplete = 'off';
  filterInput.setAttribute('aria-controls', 'file-list');
  const kindLabel = safeText('label', 'File type');
  kindLabel.htmlFor = 'file-kind-filter';
  kindLabel.className = 'sr-only';
  const kindFilter = document.createElement('select');
  kindFilter.id = 'file-kind-filter';
  kindFilter.setAttribute('aria-label', 'Filter by file type');
  const allOption = safeText('option', 'All file types');
  allOption.value = 'all';
  kindFilter.appendChild(allOption);
  for (const kind of [...new Set(FILES.map(file => file.kind))].sort()) {
    const option = safeText('option', kind);
    option.value = kind;
    kindFilter.appendChild(option);
  }
  toolbar.append(filterLabel, filterInput, kindLabel, kindFilter);
  main.appendChild(toolbar);

  const count = safeText('p', '', 'file-count');
  count.setAttribute('aria-live', 'polite');
  const list = document.createElement('ul');
  list.id = 'file-list';
  list.className = 'repo-file-list';
  main.append(count, list);

  function updateList() {
    const query = filterInput.value.trim().toLowerCase();
    const kind = kindFilter.value;
    const matches = FILES.filter(file => {
      const nameMatches = !query || file.path.toLowerCase().includes(query);
      const kindMatches = kind === 'all' || file.kind === kind;
      return nameMatches && kindMatches;
    });
    count.textContent = `Showing ${matches.length} of ${FILES.length} files`;
    list.replaceChildren();
    if (matches.length === 0) {
      list.appendChild(safeText('li', 'No files match that filter.', 'file-empty'));
      return;
    }
    for (const file of matches) {
      const row = document.createElement('li');
      row.className = 'repo-file-row';
      const open = document.createElement('button');
      open.type = 'button';
      open.className = 'file-open';
      open.setAttribute('aria-label', `Preview ${file.path}`);
      open.append(safeText('strong', file.path), safeText('span', `${file.kind} · ${formatBytes(file.size)}${file.searchable ? ' · full-text searchable' : ''}`, 'file-meta'));
      open.addEventListener('click', () => { location.hash = '#/file/' + encodeURIComponent(file.path); });
      const rowActions = document.createElement('div');
      rowActions.className = 'file-row-actions';
      const downloadLink = safeText('a', 'Download', 'file-action');
      downloadLink.href = fileUrl(file.path);
      downloadLink.setAttribute('download', file.path.split('/').pop());
      downloadLink.setAttribute('aria-label', `Download ${file.path}`);
      const githubLink = safeText('a', 'GitHub', 'file-action');
      githubLink.href = githubBlobUrl(file.path);
      githubLink.target = '_blank';
      githubLink.rel = 'noopener noreferrer';
      githubLink.setAttribute('aria-label', `View ${file.path} on GitHub`);
      rowActions.append(downloadLink, githubLink);
      row.append(open, rowActions);
      list.appendChild(row);
    }
  }

  filterInput.addEventListener('input', updateList);
  kindFilter.addEventListener('change', updateList);
  updateList();
  window.scrollTo({ top: 0 });
}

function renderRepositoryFile(path) {
  const file = fileByPath(path);
  main.replaceChildren();
  setCurrentNav('files');
  if (!file) {
    const message = safeText('p', `No repository file found at “${path}”.`);
    const back = safeText('a', 'Browse all files', 'btn');
    back.href = '#/files';
    main.append(safeText('h1', 'File not found'), message, back);
    window.scrollTo({ top: 0 });
    return;
  }

  const header = document.createElement('div');
  header.className = 'doc-head';
  const titleGroup = document.createElement('div');
  titleGroup.append(safeText('h1', file.path.split('/').pop()), safeText('p', file.path, 'file-path'));
  const actions = document.createElement('div');
  actions.className = 'doc-actions';
  if (file.isText) {
    const copyButton = safeText('button', 'Copy source', 'btn');
    copyButton.type = 'button';
    copyButton.dataset.copyFile = file.path;
    actions.appendChild(copyButton);
  }
  const downloadLink = safeText('a', 'Download original', 'btn');
  downloadLink.href = fileUrl(file.path);
  downloadLink.setAttribute('download', file.path.split('/').pop());
  actions.appendChild(downloadLink);
  const githubLink = safeText('a', 'View on GitHub', 'btn');
  githubLink.href = githubBlobUrl(file.path);
  githubLink.target = '_blank';
  githubLink.rel = 'noopener noreferrer';
  actions.append(githubLink);
  const back = safeText('a', 'All files', 'btn');
  back.href = '#/files';
  actions.append(back);
  header.append(titleGroup, actions);
  main.appendChild(header);

  const preview = document.createElement('section');
  preview.className = 'file-preview';
  if (file.currentSite) {
    preview.appendChild(safeText('p', 'This is the generated documentation site itself. Its source is rebuilt from the repository files.'));
    const openSite = safeText('a', 'Open documentation site', 'btn btn-primary');
    openSite.href = './index.html';
    preview.appendChild(openSite);
  } else if (file.isText) {
    const status = safeText('p', 'Loading file contents…', 'file-alert');
    status.setAttribute('role', 'status');
    preview.appendChild(status);
    loadFileText(file.path).then(content => {
      if (!preview.isConnected) return;
      status.remove();
      const code = document.createElement('code');
      const pre = document.createElement('pre');
      pre.appendChild(code);
      const previewLimit = 160_000;
      const showFull = content.length > previewLimit;
      code.textContent = showFull ? content.slice(0, previewLimit) : content;
      preview.appendChild(pre);
      if (showFull) {
        const note = safeText('p', `Showing the first ${formatBytes(previewLimit)} of this large file. Download the original for the complete file.`, 'file-alert');
        const expand = safeText('button', 'Show full file', 'btn');
        expand.type = 'button';
        expand.addEventListener('click', () => {
          code.textContent = content;
          note.textContent = 'Showing the complete file.';
          expand.remove();
        });
        preview.prepend(note, expand);
      }
    }).catch(error => {
      if (!preview.isConnected) return;
      status.textContent = `Could not load this file in the browser. ${error.message} Use the GitHub or download link above, or serve this repository over HTTP.`;
      const retry = safeText('button', 'Retry', 'btn');
      retry.type = 'button';
      retry.addEventListener('click', () => renderRepositoryFile(file.path));
      preview.appendChild(retry);
    });
  } else {
    preview.appendChild(safeText('p', `This ${file.kind.toLowerCase()} is not plain text, so it is available as a direct download.`));
    preview.appendChild(safeText('p', `${formatBytes(file.size)} · ${file.kind}`, 'file-alert'));
  }
  main.appendChild(preview);
  window.scrollTo({ top: 0 });
}

// ---------- navigation ----------
for (const doc of DOCS) {
  const li = document.createElement('li');
  const btn = document.createElement('button');
  btn.textContent = doc.title;
  btn.dataset.id = doc.id;
  btn.addEventListener('click', () => { location.hash = '#/' + doc.id; });
  li.appendChild(btn);
  (navs[doc.group] || navs.Instructions).appendChild(li);
}
const homeLi = document.createElement('li');
const homeBtn = document.createElement('button');
homeBtn.textContent = 'Overview';
homeBtn.dataset.id = 'home';
homeBtn.addEventListener('click', () => { location.hash = '#home'; });
homeLi.appendChild(homeBtn);
navs['Start here'].appendChild(homeLi);

const filesLi = document.createElement('li');
const filesBtn = document.createElement('button');
filesBtn.textContent = 'Browse all files';
filesBtn.dataset.id = 'files';
filesBtn.addEventListener('click', () => { location.hash = '#/files'; });
filesLi.appendChild(filesBtn);
navs.Repository.appendChild(filesLi);

function route() {
  const hash = location.hash.replace(/^#/, '');
  if (!hash || hash === 'home' || hash === '/home') { renderHome(); return; }
  if (hash === 'files' || hash === '/files') { renderFileCatalog(); return; }
  if (hash.startsWith('/file/')) {
    let path;
    try { path = decodeURIComponent(hash.slice('/file/'.length)); }
    catch { renderHome(); return; }
    renderRepositoryFile(path);
    return;
  }
  if (hash.startsWith('/')) {
    const [id, anchor] = hash.slice(1).split('@');
    render(id, anchor);
    return;
  }
  // Plain anchors (for example #skills) still navigate to their matching document.
  const doc = docById(hash);
  if (doc) { location.hash = '#/' + doc.id; return; }
  const el = document.getElementById(hash);
  if (el) el.scrollIntoView(); else renderHome();
}
window.addEventListener('hashchange', route);

// ---------- copy + download ----------
document.addEventListener('click', async (event) => {
  const target = event.target instanceof Element ? event.target : null;
  if (!target) return;
  const goto = target.closest('[data-goto]');
  if (goto) { location.hash = '#/' + goto.dataset.goto; return; }

  const code = target.closest('[data-copy]');
  if (code) {
    const copied = await copyText(code.dataset.copy);
    code.textContent = copied ? 'Copied' : 'Copy failed';
    setTimeout(() => { code.textContent = 'Copy install command'; }, 1600);
    return;
  }
  const copyBtn = target.closest('.copy-code');
  if (copyBtn) {
    const source = copyBtn.parentElement.querySelector('code');
    const copied = source ? await copyText(source.innerText) : false;
    copyBtn.textContent = copied ? 'Copied' : 'Copy failed';
    setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1400);
    return;
  }
  const docCopy = target.closest('[data-copy-doc]');
  if (docCopy) {
    const doc = docById(docCopy.dataset.copyDoc);
    const copied = doc ? await copyText(doc.md) : false;
    docCopy.textContent = copied ? 'Copied' : 'Copy failed';
    setTimeout(() => { docCopy.textContent = 'Copy markdown'; }, 1400);
    return;
  }
  const fileCopy = target.closest('[data-copy-file]');
  if (fileCopy) {
    try {
      const source = await loadFileText(fileCopy.dataset.copyFile);
      const copied = await copyText(source);
      fileCopy.textContent = copied ? 'Copied' : 'Copy failed';
    } catch {
      fileCopy.textContent = 'Copy unavailable';
    }
    setTimeout(() => { fileCopy.textContent = 'Copy source'; }, 1400);
    return;
  }
  const docDl = target.closest('[data-download-doc]');
  if (docDl) {
    const doc = docById(docDl.dataset.downloadDoc);
    if (doc) download(doc.source.split('/').pop(), doc.md, 'text/markdown;charset=utf-8');
  }
});

async function copyText(text) {
  try {
    if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard API unavailable.');
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      const copied = document.execCommand('copy');
      textarea.remove();
      return copied;
    } catch {
      textarea.remove();
      return false;
    }
  }
}
function download(name, text, type = 'text/plain;charset=utf-8') {
  const blob = new Blob([text], { type });
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}

function addCodeButtons() {
  for (const pre of document.querySelectorAll('pre')) {
    const btn = document.createElement('button');
    btn.className = 'copy-code';
    btn.type = 'button';
    btn.textContent = 'Copy';
    pre.appendChild(btn);
  }
}
const baseRender = render;
render = function (id, anchor) { baseRender(id, anchor); addCodeButtons(); };
const baseHome = renderHome;
renderHome = function () { baseHome(); addCodeButtons(); };

// ---------- full-text search ----------
const input = document.getElementById('q');
const results = document.getElementById('results');
const searchStatus = document.getElementById('search-status');
let searchTimer = 0;

function setSearchOpen(open) {
  results.dataset.open = String(open);
  input.setAttribute('aria-expanded', String(open));
}
function queryWords(query) {
  return [...new Set(query.trim().toLowerCase().split(/\s+/).filter(Boolean))];
}
function makeSnippet(text, query, terms) {
  const lower = text.toLowerCase();
  let at = lower.indexOf(query);
  if (at < 0) {
    const positions = terms.map(term => lower.indexOf(term)).filter(position => position >= 0);
    at = positions.length ? Math.min(...positions) : 0;
  }
  const start = Math.max(0, at - 45);
  const end = Math.min(text.length, start + 145);
  return `${start > 0 ? '…' : ''}${text.slice(start, end).replace(/\s+/g, ' ').trim()}${end < text.length ? '…' : ''}`;
}
function searchDocuments(query, terms) {
  const bestByLocation = new Map();
  for (const entry of SEARCH) {
    const hay = `${entry.text} ${entry.docTitle} ${entry.heading}`.toLowerCase();
    if (!terms.every(term => hay.includes(term))) continue;
    const key = `${entry.doc}@${entry.anchor}`;
    const score = (hay.includes(query) ? 60 : 0) + (entry.heading.toLowerCase().includes(query) ? 45 : 0);
    const hit = { type: 'doc', doc: entry.doc, anchor: entry.anchor, heading: entry.heading, docTitle: entry.docTitle, snippet: makeSnippet(entry.text, query, terms), score };
    if (!bestByLocation.has(key) || bestByLocation.get(key).score < score) bestByLocation.set(key, hit);
  }
  return [...bestByLocation.values()];
}
function searchFileNames(query, terms) {
  return FILES.flatMap(file => {
    const path = file.path.toLowerCase();
    if (!terms.every(term => path.includes(term))) return [];
    return [{
      type: 'file', path: file.path, kind: file.kind, snippet: `${file.kind} · ${formatBytes(file.size)}`,
      score: 80 + (path.includes(query) ? 70 : 0)
    }];
  });
}
function searchFileContents(query, terms, contents) {
  const hits = [];
  for (const [path, text] of contents) {
    const pathLower = path.toLowerCase();
    let lower = normalizedFileContents.get(path);
    if (lower === undefined) {
      lower = text.toLowerCase();
      normalizedFileContents.set(path, lower);
    }
    const pathMatch = terms.every(term => pathLower.includes(term));
    const contentMatch = terms.every(term => lower.includes(term));
    if (!pathMatch && !contentMatch) continue;
    const metadata = fileByPath(path);
    const score = (lower.includes(query) ? 55 : 0) + (pathLower.includes(query) ? 80 : 0) + (pathMatch ? 30 : 0);
    hits.push({ type: 'file', path, kind: metadata ? metadata.kind : 'Text file', snippet: makeSnippet(text, query, terms), score });
  }
  return hits;
}
function renderSearchResults(hits, loading, error) {
  const uniqueHits = new Map();
  for (const hit of hits) {
    const key = hit.type === 'file' ? `file:${hit.path}` : `doc:${hit.doc}@${hit.anchor}`;
    const previous = uniqueHits.get(key);
    if (!previous || previous.score < hit.score) uniqueHits.set(key, hit);
  }
  const ranked = [...uniqueHits.values()].sort((a, b) => b.score - a.score);
  const visible = ranked.slice(0, 25);
  results.replaceChildren();
  if (visible.length === 0) {
    const message = error
      ? 'File-content search could not load. File names and the GitHub repository are still available.'
      : loading ? 'Searching file contents…' : 'No matches. Try a file name, command, skill, or a shorter phrase.';
    results.appendChild(safeText('div', message, 'empty'));
  } else {
    for (const hit of visible) {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.searchType = hit.type;
      if (hit.type === 'doc') {
        button.dataset.doc = hit.doc;
        button.dataset.anchor = hit.anchor;
        button.append(safeText('strong', hit.heading), safeText('em', `Documentation · ${hit.docTitle}`), safeText('span', hit.snippet));
      } else {
        button.dataset.filePath = hit.path;
        button.append(safeText('strong', hit.path), safeText('em', `${hit.kind} · repository file`), safeText('span', hit.snippet));
      }
      results.appendChild(button);
    }
  }
  setSearchOpen(true);
  const resultCount = ranked.length > visible.length ? `${visible.length} of ${ranked.length}` : `${visible.length}`;
  searchStatus.textContent = loading
    ? `Searching documentation and repository files. ${resultCount} matches found so far.`
    : `${resultCount} search results${error ? '. File-content search is unavailable.' : '.'}`;
}
function closeSearch() {
  setSearchOpen(false);
  results.replaceChildren();
  searchStatus.textContent = '';
}
function clearSearch() {
  window.clearTimeout(searchTimer);
  input.value = '';
  closeSearch();
}

async function runSearch(query) {
  const normalized = query.trim().toLowerCase().replace(/\s+/g, ' ');
  if (normalized.length < 2) { closeSearch(); return; }
  const terms = queryWords(normalized);
  const initialHits = [...searchDocuments(normalized, terms), ...searchFileNames(normalized, terms)];
  renderSearchResults(initialHits, true, null);
  try {
    const contents = await loadRepositoryIndex();
    if (input.value.trim().toLowerCase().replace(/\s+/g, ' ') !== normalized) return;
    renderSearchResults([...initialHits, ...searchFileContents(normalized, terms, contents)], false, null);
  } catch (error) {
    if (input.value.trim().toLowerCase().replace(/\s+/g, ' ') !== normalized) return;
    renderSearchResults(initialHits, false, error);
  }
}
input.addEventListener('input', () => {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => { void runSearch(input.value); }, 120);
});
input.addEventListener('focus', () => {
  if (input.value.trim().length >= 2 && results.dataset.open !== 'true') void runSearch(input.value);
});
input.addEventListener('keydown', event => {
  if (event.key === 'ArrowDown' && results.dataset.open === 'true') {
    const first = results.querySelector('button');
    if (first) { event.preventDefault(); first.focus(); }
  }
  if (event.key === 'Escape') clearSearch();
});
results.addEventListener('keydown', event => {
  const buttons = [...results.querySelectorAll('button')];
  const index = buttons.indexOf(document.activeElement);
  if (event.key === 'ArrowDown' && index >= 0) {
    event.preventDefault();
    (buttons[index + 1] || buttons[0]).focus();
  } else if (event.key === 'ArrowUp' && index >= 0) {
    event.preventDefault();
    if (index === 0) input.focus(); else buttons[index - 1].focus();
  } else if (event.key === 'Escape') {
    event.preventDefault();
    clearSearch();
    input.focus();
  }
});
results.addEventListener('click', event => {
  const target = event.target instanceof Element ? event.target : null;
  const button = target && target.closest('button[data-search-type]');
  if (!button) return;
  if (button.dataset.searchType === 'doc') {
    location.hash = '#/' + button.dataset.doc + '@' + button.dataset.anchor;
  } else {
    location.hash = '#/file/' + encodeURIComponent(button.dataset.filePath);
  }
  input.value = '';
  closeSearch();
});
document.addEventListener('click', event => {
  const target = event.target instanceof Element ? event.target : null;
  if (target && !target.closest('.search')) closeSearch();
});

route();
</script>
</body>
</html>
"""


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def build(
    out_path: Path,
    check_only: bool = False,
    files_index_path: Path | None = None,
) -> int:
    if files_index_path is None:
        files_index_path = out_path.parent / REPOSITORY_INDEX_NAME

    docs_json: list[dict[str, object]] = []
    search: list[dict[str, str]] = []
    problems: list[str] = []

    for doc_id, title, group, rel in DOCS:
        path = REPO / rel
        if not path.is_file():
            problems.append(f"missing source: {rel}")
            continue
        md = path.read_text(encoding="utf-8")
        used: set[str] = set()
        html_body, headings = md_to_html(md, used)
        docs_json.append(
            {
                "id": doc_id,
                "title": title,
                "group": group,
                "source": rel,
                "html": html_body,
                "md": md,
                "headings": headings,
            }
        )

        search.extend(search_entries_for_document(doc_id, title, md, headings))

    file_manifest, repository_index = build_repository_file_data()
    shell = (
        SHELL.replace(
            "__DOCS__",
            json.dumps(docs_json, ensure_ascii=True).replace("<", "\\u003c"),
        )
        .replace(
            "__SEARCH__",
            json.dumps(search, ensure_ascii=True).replace("<", "\\u003c"),
        )
        .replace(
            "__FILES__",
            json.dumps(file_manifest, ensure_ascii=True).replace("<", "\\u003c"),
        )
        .replace(
            "__REPOSITORY_INDEX_URL__",
            json.dumps(os.path.relpath(files_index_path, out_path.parent).replace(os.sep, "/")),
        )
    )

    if check_only:
        if problems:
            for problem in problems:
                print(f"ERROR: {problem}", file=sys.stderr)
            return 1
        searchable_count = sum(bool(file["searchable"]) for file in file_manifest)
        print(
            f"ok: {len(docs_json)} documents, {len(search)} search entries, "
            f"{len(file_manifest)} repository files ({searchable_count} searchable), no missing sources"
        )
        return 0

    if problems:
        for problem in problems:
            print(f"WARNING: {problem}", file=sys.stderr)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    files_index_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(shell, encoding="utf-8")
    files_index_path.write_text(
        json.dumps(repository_index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"wrote {display_path(out_path)}")
    print(f"  {len(docs_json)} docs, {len(search)} search entries, {len(shell) // 1024} KB")
    print(
        f"wrote {display_path(files_index_path)}"
    )
    print(f"  {len(file_manifest)} files listed, {len(repository_index['files'])} text files indexed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the kit's single-file documentation site")
    parser.add_argument("--out", default="index.html", help="output path (default: index.html)")
    parser.add_argument("--files-out", help="repository search data path (defaults beside --out)")
    parser.add_argument("--check", action="store_true", help="verify sources exist, write nothing")
    args = parser.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    files_out = Path(args.files_out) if args.files_out else out.parent / REPOSITORY_INDEX_NAME
    if not files_out.is_absolute():
        files_out = REPO / files_out
    return build(out, check_only=args.check, files_index_path=files_out)


if __name__ == "__main__":
    raise SystemExit(main())
