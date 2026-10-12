# Costume Webapp Kit

**Turn any AI coding agent into a senior webapp team.** Instructions that are enforced, offline design intelligence, and the component MCP, wired for every major AI coding tool.

[![Verify](https://img.shields.io/badge/verify-scripts%2Fverify.sh-blue)](scripts/verify.sh)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-UI%2FUX%20Pro%20Max%20v2.13.0-purple)](skills/README.md)
[![MCP](https://img.shields.io/badge/MCP-21st.dev%20%28Magic%29-orange)](mcp/21st-mcp.md)
[![Clients](https://img.shields.io/badge/clients-Claude%20%C2%B7%20Cursor%20%C2%B7%20Copilot%20%C2%B7%20Codex%20%C2%B7%20Gemini%20%C2%B7%20Windsurf-black)](#what-lands-where)

Most AI webapp output looks the same: a gradient hero, three identical feature cards, lorem ipsum, a spinner where a loading state should be, `#7c3aed` pasted into eight files, and a "done" claim with no build run. This repo fixes that with rules the agent has to follow, a design database it has to search, real components it can install, and verification it has to show.

---

## What you get

| | |
|---|---|
| **Instructions** | 7 files, ~1,500 lines: voice and accuracy, the build protocol with 25 numbered rules, UI/UX priority order, six stack playbooks, quality gates, prompt recipes, tool usage rules |
| **Design intelligence** | UI/UX Pro Max, vendored and offline: 79 styles, 192 palettes with reasoning, 74 font pairings, 119 UX guidelines, 105 icons, 25 chart types, 22 stacks, one Python script |
| **Component MCP** | 21st.dev (the server behind Magic MCP): `search`, `get_component`, `get_inspiration`, `search_logo`, and hosted `generate`, with configs for six clients |
| **Agents** | `webapp-architect`, `ui-ux-designer`, `frontend-implementer`, `qa-reviewer` |
| **Commands** | `/webapp`, `/ui`, `/review`, `/ship`, `/mcp` |
| **Installer** | `scripts/setup.sh`: copies skills, writes instruction files, merges MCP config, never clobbers your settings |
| **Starter** | A dependency-free landing page that applies every rule at once |
| **Site** | `index.html` plus `repository-files.json`: searchable docs and tracked text files, with file preview, copy, and download actions |

---

## Quick start

### Option A - install into your project (recommended)

```bash
git clone https://github.com/arbabtalha/Costume-instructions
cd Costume-instructions
./scripts/setup.sh --target ~/code/my-app --client all
```

Then set your key and restart the editor:

```bash
export API_KEY_21ST="your-key"     # free and instant: https://21st.dev/mcp
```

Add flags as needed: `--client claude` for one tool, `--no-mcp` for instructions and skills only, `--upstream` to pull the newest skills from npm instead of the vendored copies, `--dry-run` to see the plan, `--global` for home-directory installs.

### Option B - install this repo as a plugin (Claude Code)

```bash
claude plugin marketplace add arbabtalha/Costume-instructions
/plugin install costume-webapp-kit
```

The plugin brings the skills, the four subagents, the five commands, and the MCP server config.

### Option C - use it in place

Clone it, open your AI coding tool in the repo, and work inside `starters/` or any project you point the tools at. Everything under `skills/` is directly runnable:

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "fintech analytics dashboard" --design-system -p "Ops Console"
```

---

## What lands where

`scripts/setup.sh` detects your clients (or takes `--client all`):

| Client | Instructions | Skills | MCP config |
|---|---|---|---|
| **Claude Code** | `CLAUDE.md` + `AGENTS.md` | `.claude/skills/` | `.mcp.json` |
| **Cursor** | `.cursor/rules/*.mdc` | `.cursor/skills/` | `.cursor/mcp.json` |
| **VS Code / Copilot** | `.github/copilot-instructions.md` | `.github/prompts/` | `.vscode/mcp.json` |
| **Codex CLI** | `AGENTS.md` | `.agents/skills/` | `~/.codex/config.toml` |
| **Gemini CLI** | `GEMINI.md` | `.gemini/skills/` | `~/.gemini/settings.json` |
| **Windsurf** | `.windsurf/rules/costume.md` | `.windsurf/skills/` | `~/.codeium/windsurf/mcp_config.json` |

Existing files are preserved: instruction files get an idempotent managed block, JSON configs are merged, and anything overwritten is backed up under `.costume-backup/<timestamp>/`.

---

## The design intelligence skill

UI/UX Pro Max is the reason the output stops looking generic. It is a searchable local database, not a vibe.

```bash
# full design system for a new product or page (start here)
python3 skills/ui-ux-pro-max/scripts/search.py "saas analytics dashboard b2b" --design-system -p "Ops Console"

# persist it so later sessions stay consistent
python3 skills/ui-ux-pro-max/scripts/search.py "saas analytics dashboard" --design-system --persist -p "Ops Console" --output-dir .
# -> design-system/ops-console/MASTER.md  (+ pages/<page>.md overrides)

# targeted searches
python3 skills/ui-ux-pro-max/scripts/search.py "empty state onboarding" --domain ux
python3 skills/ui-ux-pro-max/scripts/search.py "glassmorphism dark" --domain style
python3 skills/ui-ux-pro-max/scripts/search.py "fintech trust" --domain color
python3 skills/ui-ux-pro-max/scripts/search.py "saas modern clean" --domain typography
python3 skills/ui-ux-pro-max/scripts/search.py "streaming suspense" --stack nextjs
```

Domains: `style color chart landing product ux typography icons gsap react web google-fonts`.
Stacks: `react nextjs vue svelte astro swiftui react-native flutter nuxtjs nuxt-ui html-tailwind shadcn jetpack-compose threejs angular laravel javafx wpf winui avalonia uno uwp`.
Dials: `--variance 1-10`, `--motion 1-10`, `--density 1-10`.

Details, licenses, and the update path: [`skills/README.md`](skills/README.md).

---

## The 21st.dev MCP

Requested as `21st-dev/magic-mcp`. Important: **Magic MCP is now the 21st MCP.** The server is HTTP MCP at `https://21st.dev/api/mcp`, authenticated with an `x-api-key` header. The old `@21st-dev/magic` npm package still works as a stdio compatibility proxy, and old Magic API keys were reset.

```bash
# official installer
npx @21st-dev/cli@latest init --client cursor     # claude | codex | vscode | devin | windsurf

# or this repo's installer
./scripts/install-mcp.sh --client claude

# or the stdio proxy for clients without HTTP MCP
npx -y @21st-dev/magic@latest API_KEY="<YOUR_21ST_API_KEY>"
```

| Tool | Use |
|---|---|
| `search` | find components, themes, templates |
| `get_component` | fetch code and metadata, then install |
| `get_inspiration` | explore styles before committing |
| `search_logo` | brand logos as JSX/TSX |
| `generate` | hosted UI generation, when AI access is enabled |
| `get_usage` | what the account can do, including `aiGenerationEnabled` |

Free tier covers catalog search plus 2 component installs per day. Hosted AI is a separate entitlement. Per-client configs and troubleshooting: [`mcp/21st-mcp.md`](mcp/21st-mcp.md).

---

## Subagents

| Agent | Use it for |
|---|---|
| `webapp-architect` | plan a new app or feature: stack, layout, data flow, states, risks, build order |
| `ui-ux-designer` | tokens, section structure, component specs, motion, anti-generic direction |
| `frontend-implementer` | write the code once the plan and tokens exist, then verify it |
| `qa-reviewer` | audit accessibility, responsiveness, performance, security, consistency with severity ratings |

Commands: `/webapp` (full build protocol), `/ui` (design pass), `/review` (ranked audit), `/ship` (gates, commit, PR body), `/mcp` (connection status and fixes).

---

## The loop every agent follows

1. **Intake** - product, primary action, surface, stack, content, constraints, integrations, definition of done.
2. **Design system** - search the database, persist `MASTER.md`, write tokens before any component.
3. **Scaffold** - the stack playbook for Next.js, Vite/React, Astro, Vue/Nuxt, SvelteKit, or single-file HTML.
4. **Build** - shell, primitives, sections, then loading, empty, error and success states.
5. **Verify** - typecheck, lint, build, keyboard pass, contrast in both themes, 375/768/1024/1440, reduced motion.
6. **Report** - Built / Ran / Checked / Not done / Next. Unfinished work stated, not hidden.

Non-negotiables, condensed: tokens instead of hex, a real component instead of invented UI, all four async states, WCAG 2.2 AA, responsive from 320px, real copy, no secrets in client code, and never a "done" claim without pasted command output.

---

## Repository layout

```
AGENTS.md                entry point for every agent (rules, routing, workflow)
CLAUDE.md  GEMINI.md     client-specific entry files
instructions/            the instruction set
  00-core.md               voice, accuracy, behavior, slash commands
  10-webapp-generation.md  the build protocol, 25 numbered rules, definition of done
  20-ui-ux-rules.md        priority order, checks, anti-patterns
  30-stack-playbooks.md    Next.js, Vite, Astro, Vue/Nuxt, SvelteKit, HTML, Tailwind, shadcn
  40-quality-gates.md      build, a11y, perf, SEO, security, review, git, honesty
  50-prompt-recipes.md     copy-paste prompts for users
  60-mcp-and-skill-usage.md how agents use the skill and the MCP
agents/                  four subagents
commands/                five slash commands
skills/                  vendored UI/UX Pro Max + design, brand, slides, 21st-ui (MIT/ISC)
mcp/                     docs + per-client configs
scripts/                 setup.sh, install-mcp.sh, verify.sh, vendor-update.sh, build-site.py
starters/                dependency-free landing page + framework recipes
index.html               generated docs site with docs + repository file search (make site)
repository-files.json      generated index of tracked text files for public search and preview
costume-instructions.html  the original personal prompt page, kept as-is
.cursor/rules/  .github/  client wiring that works without setup.sh
```

---

## Browse and search the repository files

Open the generated site and search from the top bar, or choose **Browse all files**. Search covers the curated docs and the full contents of tracked text files. The browser lists tracked project source files and assets, previews text, copies source, and downloads originals; binary assets are downloadable directly. The text index is loaded only when needed, so it does not slow the initial page load. Untracked local files are never published into the index.

The site and `repository-files.json` are generated by `make site` and should be committed together. For local file browsing, serve the repository over HTTP (for example, `python3 -m http.server 8000` from the repo root). Browsers block fetching the separate search index when the HTML is opened with `file://`.

## Requirements

- **Required:** a git-enabled editor with an AI coding tool, and Python 3.8+ for the design skill.
- **Optional:** Node 18+ for the MCP stdio proxy, plugin installs, and JS stack starters.
- **Optional:** an API key from <https://21st.dev/mcp> for catalog search and generation. Everything else works without it.

## Verify

```bash
./scripts/verify.sh          # structure, JSON, skill runtime, scripts, hygiene
make site                    # rebuild index.html and repository-files.json
./scripts/vendor-update.sh --check   # upstream versions vs vendored
```

CI runs `scripts/verify.sh` on every push and pull request.

## Keeping it current

```bash
./scripts/vendor-update.sh   # re-vendor the skills from upstream repos
npx ui-ux-pro-max-cli@latest init --ai claude   # or install the newest skill release directly
```

## Credits and license

MIT for this repository's own work. Vendored third-party components keep their licenses: UI/UX Pro Max (MIT, Next Level Builder) and the 21st.dev UI skill (ISC). See [`LICENSE`](LICENSE) and `skills/LICENSE-*.txt`.

Not affiliated with 21st.dev, Next Level Builder, or any AI vendor. The setup instructions are documented from their upstream repositories.

Built by [arbabtalha](https://github.com/arbabtalha). Use it, fork it, ship with it.
