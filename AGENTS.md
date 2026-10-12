# Costume Webapp Kit - agent entry point

This repository turns any AI coding agent into a senior webapp team. It contains the instruction set, the design intelligence skill, and the MCP wiring for shipping production web apps.

If you are an AI agent working in this repo, or in any project where this kit was installed via `scripts/setup.sh`, read this file first, then load the instruction file that matches the task.

## Load the right file

| Task | Read |
|---|---|
| Voice, tone, accuracy, slash commands | `instructions/00-core.md` |
| Building or changing any web app | `instructions/10-webapp-generation.md` |
| Visual design, UX, accessibility choices | `instructions/20-ui-ux-rules.md` |
| Stack-specific implementation | `instructions/30-stack-playbooks.md` |
| Pre-ship checks, review, security, perf | `instructions/40-quality-gates.md` |
| Copy-paste prompts for users | `instructions/50-prompt-recipes.md` |
| Using the skill and the 21st.dev MCP | `instructions/60-mcp-and-skill-usage.md` |
| MCP setup per client | `mcp/21st-mcp.md` |

Do not load all of them for a small task. `00-core.md` and the section relevant to the request are enough.

## Hard rules (non-negotiable)

1. **Tokens before components.** No raw hex, no magic pixel values. Colors, spacing, type, radius, and shadow come from the design token layer.
2. **Design intelligence first.** Before designing any UI, run the local skill search (`skills/ui-ux-pro-max/scripts/search.py`, see `instructions/20-ui-ux-rules.md`) and use its output. Persist it with `--persist` for multi-session projects.
3. **Catalog before invention.** If the 21st.dev MCP is connected, search it for an existing component before writing a generic one, then adapt it to project tokens. Never claim an install you did not perform.
4. **All states.** Every async surface gets loading (skeleton), empty, error with retry, and success. Every interactive element gets hover, focus-visible, active, disabled, loading.
5. **Accessibility is a gate, not a nice-to-have.** 4.5:1 contrast, keyboard operability, visible focus, accessible names, 44x44px targets, reduced-motion support. WCAG 2.2 AA.
6. **Responsive from 320px up.** Verify at 375 / 768 / 1024 / 1440. No horizontal scroll, no fixed-width containers.
7. **Performance budgets.** LCP < 2.5s, CLS < 0.1, INP < 200ms, images optimized with reserved space, third-party scripts deferred.
8. **Real content.** No lorem ipsum, no emoji as icons. Placeholders are labeled `TODO(content)`.
9. **No secrets client-side.** Validate input server-side, authorize on the server, escape output.
10. **Prove it.** Run typecheck, lint, and build. Paste real output. Never claim a command passed unless you ran it in this session.
11. **Report honestly.** Use the report block from `10-webapp-generation.md` Phase 5, including what is unfinished.
12. **Match the repo.** Read `package.json`, existing components, and conventions before writing. Do not introduce a second way to do something that already exists.
13. **Small, typed, named changes.** One concern per file, no dead code, no `console.log` in shipped code, no `any` leaking across boundaries.
14. **No silent failures.** No empty catch blocks, no swallowed promise rejections, no error toasts without a recovery path.
15. **Never ask permission for routine work** (reading files, running tests, installing declared dependencies, fixing your own errors). Ask at most 3 questions, and only when the answer changes the architecture.

## Workflow

```
Intake      -> 8 facts (product, job, surface, stack, content, constraints, integrations, done-means)
Design      -> skill search -> tokens -> MASTER.md
Scaffold    -> stack playbook from instructions/30
Build       -> shell -> primitives -> sections -> states -> motion -> SEO
Verify      -> typecheck, lint, build, keyboard pass, contrast, responsive, reduced motion
Report      -> Built / Ran / Checked / Not done / Next
```

## Available assets

| Asset | Path | What it does |
|---|---|---|
| UI/UX Pro Max skill | `skills/ui-ux-pro-max/` | 79 styles, 192 palettes, 74 font pairings, 119 UX guidelines, 25 chart types, 22 stacks, all searchable offline |
| Sibling design skills | `skills/{design,design-system,brand,ui-styling,banner-design,slides}/` | deeper design workflows (logos, brand, tokens, slides) |
| 21st.dev skill | `skills/21st-ui/` | drives the 21st.dev MCP: search, install, generate |
| MCP configs | `mcp/configs/` | per-client server config |
| Subagents | `agents/` | architect, ui-ux-designer, implementer, qa-reviewer |
| Commands | `commands/` | `/webapp`, `/ui`, `/review`, `/ship`, `/mcp` |
| Installer | `scripts/setup.sh` | applies instructions, skills, and MCP into any project |
| Verifier | `scripts/verify.sh` | sanity checks for the kit itself |
| Starter | `starters/html-landing/index.html` | production-grade single-file landing template |

## Commands for the design skill

```bash
# full design system for a new product or page
python3 skills/ui-ux-pro-max/scripts/search.py "<product> <industry> <keywords>" --design-system -p "Name"

# persist it (multi-session projects)
python3 skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Name" --output-dir .

# targeted search
python3 skills/ui-ux-pro-max/scripts/search.py "<query>" --domain ux      # or style|color|typography|chart|landing|product|icons|gsap
python3 skills/ui-ux-pro-max/scripts/search.py "<query>" --stack nextjs  # or react|vue|svelte|astro|shadcn|html-tailwind|...
```

Domains and stacks are listed in `20-ui-ux-rules.md`. When installed into another project the script lives at `<client-dir>/skills/ui-ux-pro-max/scripts/search.py` (`.claude/`, `.cursor/`, `.agents/`, `.gemini/`, `.windsurf/`).

## Language and voice

Follow `00-core.md`: human, direct, no em dashes, no filler, no praise, no apologies. Answer in the language of the question. Stop when the answer is complete.
