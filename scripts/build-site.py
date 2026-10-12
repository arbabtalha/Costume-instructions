#!/usr/bin/env python3
"""Build the single-file documentation site (index.html) for the Costume Webapp Kit.

No third-party dependencies. The output is one self-contained HTML file:
no CDN, no fonts to download, works offline and on GitHub Pages.

Usage:
    python3 scripts/build-site.py [--out index.html] [--check]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

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
    """Escape, then apply inline markdown. Code spans are protected first."""
    codes: list[str] = []

    def stash(match: re.Match[str]) -> str:
        codes.append(match.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", stash, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)
    return text


LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|[\s:\-|]+\|\s*$")


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

        # list (with nesting)
        first = LIST_RE.match(line)
        if first:
            level_stack: list[str] = []  # 'ul' | 'ol' per indent depth
            base_indent = len(first.group(1).expandtabs(2))
            out.append("<ul>")
            level_stack.append("ul")
            current_indent = base_indent
            while i < len(lines):
                item = LIST_RE.match(lines[i])
                if not item:
                    # continuation line inside an item
                    if lines[i].strip() and not lines[i].startswith((" ", "\t")):
                        break
                    if lines[i].strip() and out and out[-1].endswith("</li>"):
                        out[-1] = out[-1][: -len("</li>")] + " " + inline(lines[i].strip()) + "</li>"
                        i += 1
                        continue
                    break
                indent = len(item.group(1).expandtabs(2))
                marker, text = item.group(2), item.group(3)
                kind = "ol" if marker[0].isdigit() else "ul"

                if indent > current_indent:
                    out.append(f"<{kind}>")
                    level_stack.append(kind)
                    current_indent = indent
                elif indent < current_indent:
                    while len(level_stack) > 1 and indent < current_indent:
                        out.append(f"</{level_stack.pop()}>")
                        current_indent -= 2
                    if indent != current_indent:
                        current_indent = indent
                else:
                    if kind != level_stack[-1] and kind == "ol" and level_stack[-1] == "ul":
                        out.append("</ul><ol>")
                        level_stack[-1] = "ol"

                checkbox = re.match(r"^\[( |x|X)\]\s*(.*)$", text)
                if checkbox:
                    tick = "checked" if checkbox.group(1).lower() == "x" else ""
                    out.append(f'<li class="task"><input type="checkbox" disabled {tick}> {inline(checkbox.group(2))}</li>')
                else:
                    out.append(f"<li>{inline(text)}</li>")
                i += 1
            while level_stack:
                out.append(f"</{level_stack.pop()}>")
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


SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Costume Webapp Kit - instructions, design intelligence, MCP for AI webapp generation</title>
<meta name="description" content="One repo that makes any AI coding agent build production web apps: a 60-rule build protocol, offline UI/UX design intelligence, the 21st.dev MCP server, agents, commands and installers.">
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
  .top nav a { color: var(--muted); }
  .top nav a:hover { color: var(--text); }
  .search { position: relative; flex: 1; max-width: 20rem; margin-left: auto; }
  .search input {
    width: 100%; font: inherit; font-size: .875rem; padding: .5rem .8rem; color: var(--text);
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
    display: block; width: 100%; text-align: left; font: inherit; font-size: .85rem; padding: .55rem .8rem;
    background: none; border: 0; border-bottom: 1px solid var(--border); color: var(--text); cursor: pointer;
  }
  .results button:hover { background: var(--surface-alt); }
  .results button span { display: block; color: var(--muted); font-size: .78rem; }
  .results .empty { padding: .8rem; color: var(--muted); font-size: .85rem; }

  .layout { max-width: var(--container); margin: 0 auto; padding: 1.5rem 1.25rem 4rem; display: grid; gap: 2.5rem; }
  @media (min-width: 60rem) { .layout { grid-template-columns: var(--sidebar) minmax(0, 1fr); gap: 3rem; } }
  aside { font-size: .875rem; }
  @media (min-width: 60rem) { aside { position: sticky; top: 4.5rem; align-self: start; max-height: calc(100vh - 6rem); overflow-y: auto; } }
  aside h2 { font-size: .7rem; text-transform: uppercase; letter-spacing: .14em; color: var(--muted); margin: 1.4rem 0 .5rem; }
  aside ul { list-style: none; margin: 0; padding: 0; display: grid; gap: .1rem; }
  aside button {
    width: 100%; text-align: left; font: inherit; font-size: .875rem; padding: .35rem .6rem; border-radius: 7px;
    border: 0; background: none; color: var(--muted); cursor: pointer;
  }
  aside button:hover { background: var(--surface-alt); color: var(--text); }
  aside button[aria-current="true"] { background: var(--accent-soft); color: var(--text); font-weight: 600; }

  main { min-width: 0; }
  .doc-head { margin-bottom: 1.5rem; display: flex; flex-wrap: wrap; gap: .75rem; align-items: center; justify-content: space-between; }
  .doc-head h1 { font-size: 1.9rem; margin: 0; letter-spacing: -.025em; }
  .doc-actions { display: flex; gap: .5rem; flex-wrap: wrap; }
  .btn {
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
    position: absolute; top: .5rem; right: .5rem; font: inherit; font-size: .72rem; padding: .2rem .55rem;
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
      <a href="#rules">Rules</a>
    </nav>
    <div class="search">
      <label class="sr-only" for="q" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">Search the docs</label>
      <input id="q" type="search" placeholder="Search rules, gates, stacks..." autocomplete="off">
      <div class="results" id="results" role="listbox" aria-label="Search results"></div>
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
  </aside>
  <main id="main"></main>
</div>

<script>
const DOCS = __DOCS__;
const SEARCH = __SEARCH__;

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

<p class="note">Everything on this page is generated from the repository's markdown by
<code>scripts/build-site.py</code>. Edit the markdown, not the HTML.</p>
`;

const main = document.getElementById('main');
const navs = { start: document.getElementById('nav-start'), Instructions: document.getElementById('nav-instructions'), Assets: document.getElementById('nav-assets') };

function docById(id) { return DOCS.find(d => d.id === id); }

function render(id, anchor) {
  const doc = docById(id);
  if (!doc) { renderHome(); return; }
  main.innerHTML = `<div class="doc-head"><h1>${doc.title}</h1>
    <div class="doc-actions">
      <button class="btn" data-copy-doc="${doc.id}">Copy markdown</button>
      <button class="btn" data-download-doc="${doc.id}">Download .md</button>
      <button class="btn" data-goto="home">Home</button>
    </div></div><div class="content">${doc.html}</div>`;
  for (const b of document.querySelectorAll('aside button')) {
    b.setAttribute('aria-current', String(b.dataset.id === id));
  }
  if (anchor) {
    const el = document.getElementById(anchor);
    if (el) { el.scrollIntoView(); return; }
  }
  window.scrollTo({ top: 0 });
}

function renderHome() {
  main.innerHTML = HOME;
  for (const b of document.querySelectorAll('aside button')) b.setAttribute('aria-current', String(b.dataset.id === 'home'));
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
navs.start.appendChild(homeLi);

function route() {
  const hash = location.hash.replace(/^#/, '');
  if (!hash || hash === 'home') { renderHome(); return; }
  if (hash.startsWith('/')) {
    const [id, anchor] = hash.slice(1).split('@');
    render(id, anchor);
    return;
  }
  // plain anchors on the home page (e.g. #skills) go to the matching doc when one exists
  const doc = docById(hash);
  if (doc) { location.hash = '#/' + doc.id; return; }
  const el = document.getElementById(hash);
  if (el) el.scrollIntoView(); else renderHome();
}
window.addEventListener('hashchange', route);

// ---------- copy + download ----------
document.addEventListener('click', async (event) => {
  const goto = event.target.closest('[data-goto]');
  if (goto) { location.hash = '#/' + goto.dataset.goto; return; }

  const code = event.target.closest('[data-copy]');
  if (code) {
    await copyText(code.dataset.copy);
    code.textContent = 'Copied';
    setTimeout(() => { code.textContent = 'Copy install command'; }, 1600);
    return;
  }
  const copyBtn = event.target.closest('.copy-code');
  if (copyBtn) {
    await copyText(copyBtn.parentElement.querySelector('code').innerText);
    copyBtn.textContent = 'Copied';
    setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1400);
    return;
  }
  const docCopy = event.target.closest('[data-copy-doc]');
  if (docCopy) {
    const doc = docById(docCopy.dataset.copyDoc);
    await copyText(doc.md);
    docCopy.textContent = 'Copied';
    setTimeout(() => { docCopy.textContent = 'Copy markdown'; }, 1400);
    return;
  }
  const docDl = event.target.closest('[data-download-doc]');
  if (docDl) {
    const doc = docById(docDl.dataset.downloadDoc);
    download(doc.id + '.md', doc.md);
  }
});

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); }
  catch (err) { /* clipboard blocked: selection fallback */
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta); ta.select();
    document.execCommand('copy'); ta.remove();
  }
}
function download(name, text) {
  const blob = new Blob([text], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
  URL.revokeObjectURL(a.href);
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

// ---------- search ----------
const input = document.getElementById('q');
const results = document.getElementById('results');

function runSearch(query) {
  const q = query.trim().toLowerCase();
  if (q.length < 2) { results.dataset.open = 'false'; results.innerHTML = ''; return; }
  const hits = [];
  for (const entry of SEARCH) {
    const hay = (entry.text + ' ' + entry.docTitle + ' ' + entry.heading).toLowerCase();
    const at = hay.indexOf(q);
    if (at === -1) continue;
    const start = Math.max(0, at - 40);
    hits.push({
      doc: entry.doc, anchor: entry.anchor, heading: entry.heading, docTitle: entry.docTitle,
      snippet: (at > 40 ? '...' : '') + entry.text.slice(start, start + 110).trim() + '...'
    });
    if (hits.length >= 25) break;
  }
  results.innerHTML = hits.length
    ? hits.map(h => `<button data-doc="${h.doc}" data-anchor="${h.anchor}"><strong>${h.heading}</strong> <em style="font-style:normal;color:var(--muted)">- ${h.docTitle}</em><span>${h.snippet.replace(/</g, '&lt;')}</span></button>`).join('')
    : '<div class="empty">No match. Try "contrast", "contrast gate", "pricing", "suspense", "zod".</div>';
  results.dataset.open = 'true';
}
input.addEventListener('input', (e) => runSearch(e.target.value));
results.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-doc]');
  if (!btn) return;
  location.hash = '#/' + btn.dataset.doc + '@' + btn.dataset.anchor;
  results.dataset.open = 'false';
  input.value = '';
});
document.addEventListener('click', (e) => {
  if (!e.target.closest('.search')) results.dataset.open = 'false';
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') { results.dataset.open = 'false'; input.blur(); }
});

route();
</script>
</body>
</html>
"""


def build(out_path: Path, check_only: bool = False) -> int:
    docs_json: list[dict[str, object]] = []
    search: list[dict[str, str]] = []
    problems: list[str] = []

    for doc_id, title, group, rel in DOCS:
        path = REPO / rel
        if not path.exists():
            problems.append(f"missing source: {rel}")
            continue
        md = path.read_text(encoding="utf-8")
        used: set[str] = set()
        html_body, headings = md_to_html(md, used)
        docs_json.append(
            {"id": doc_id, "title": title, "group": group, "html": html_body, "md": md, "headings": headings}
        )
        # search index: heading or paragraph level chunks
        chunks = re.split(r"\n\s*\n", md)
        current_heading = title
        for chunk in chunks:
            stripped = chunk.strip()
            if not stripped:
                continue
            head = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if head:
                current_heading = re.sub(r"[`*]", "", head.group(2))
                continue
            if stripped.startswith(("```", "|", "---")):
                continue
            text = re.sub(r"[`*#>|\[\]()]", " ", stripped)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) < 25:
                continue
            anchor = ""
            for h in headings:
                if h["text"].lower() in current_heading.lower():
                    anchor = h["id"]
            search.append(
                {
                    "doc": doc_id,
                    "docTitle": title,
                    "anchor": anchor,
                    "heading": current_heading,
                    "text": text[:220],
                }
            )

    shell = SHELL.replace(
        "__DOCS__",
        json.dumps(docs_json, ensure_ascii=True).replace("<", "\\u003c"),
    ).replace(
        "__SEARCH__",
        json.dumps(search, ensure_ascii=True).replace("<", "\\u003c"),
    )

    if check_only:
        if problems:
            for p in problems:
                print(f"ERROR: {p}", file=sys.stderr)
            return 1
        print(f"ok: {len(docs_json)} documents, {len(search)} search entries, no missing sources")
        return 0

    if problems:
        for p in problems:
            print(f"WARNING: {p}", file=sys.stderr)

    out_path.write_text(shell, encoding="utf-8")
    print(f"wrote {out_path.relative_to(REPO) if out_path.is_relative_to(REPO) else out_path}")
    print(f"  {len(docs_json)} documents, {len(search)} search entries, {len(shell) // 1024} KB")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the kit's single-file documentation site")
    parser.add_argument("--out", default="index.html", help="output path (default: index.html)")
    parser.add_argument("--check", action="store_true", help="verify sources exist, write nothing")
    args = parser.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    return build(out, check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
