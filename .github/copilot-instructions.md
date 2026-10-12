# Copilot instructions - Costume Webapp Kit

Full rules live in `AGENTS.md` and `instructions/`. This is the condensed version for chat and inline completions.

## Voice

Direct, human, active voice. No em dashes, no buzzwords, no filler openers, no praise, no apologies. Outcome first. Answer in the language of the question. Stop when done.

## Accuracy

Never claim something works unless it was run. No invented APIs, versions, or benchmarks. Below 90% confidence, flag it. Missing data: "Insufficient data to verify".

## Building UI

Before writing components:

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<product> <industry> <keywords>" --design-system -p "Name"
```

Then follow `instructions/10-webapp-generation.md`: tokens -> shell -> primitives -> sections -> states -> motion -> SEO -> verify.

Checklist for any component you generate:

- Consumes design tokens, never raw hex or magic pixels
- All states: hover, focus-visible, active, disabled, loading, plus empty/error for data surfaces
- 44x44px minimum targets, `cursor: pointer`, SVG icons (never emoji)
- Accessible name, keyboard operable, contrast 4.5:1 in light and dark
- Responsive from 320px, verified at 375/768/1024/1440
- Animations 150-300ms on transform/opacity with a reduced-motion path
- Real copy, `TODO(content)` for placeholders, verb button labels

## Stack notes

Next.js: server components by default, `await params` in Next 15, `next/font` and `next/image`, metadata export per route, server actions plus `revalidatePath` for mutations.
Vite/React: data in one `api/` module or TanStack Query, no duplicate fetches, `VITE_` env vars are public.
Astro: zero JS by default, islands only where needed, content collections with Zod.
Plain HTML: single file, tokens in `:root`, no CDN dependencies, progressive enhancement.

## MCP

The 21st.dev MCP (config in `mcp/configs/`, docs in `mcp/21st-mcp.md`) provides `search`, `get_component`, `get_inspiration`, `search_logo`, and `generate` when AI access is enabled. Prefer a real catalog component over hand-written generic UI, then adapt it to project tokens. Never claim an install that did not return code.

## Before you say done

Run typecheck, lint, and build. Show the real output. Then report: Built / Ran / Checked / Not done / Next.
