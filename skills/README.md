# Skills

Vendored, pinned copies of the design intelligence that this kit installs into projects. Everything here works offline: no API key, no network, no npm install.

| Skill | What it gives an agent | Source |
|---|---|---|
| `ui-ux-pro-max/` | 79 styles, 192 product palettes with reasoning, 74 font pairings, 119 UX guidelines, 105 icons, 17 GSAP presets, 25 chart types, 22 stack guides. Searchable via `scripts/search.py`. | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) |
| `ui-styling/` | Tailwind and shadcn/ui styling mechanics, token generation scripts, canvas fonts | same upstream |
| `design-system/` | token architecture (primitive/semantic/component), component specs, Tailwind integration, slide data | same upstream |
| `design/` | logo, icon, brand identity, social/banner design workflows, prompt engineering | same upstream |
| `brand/` | brand guidelines, color and type specifications, asset validation scripts | same upstream |
| `banner-design/` | banner sizes and style guidance | same upstream |
| `slides/` | slide deck structure and layout guidance | same upstream |
| `21st-ui/` | drives the 21st.dev MCP: when to search the catalog, install a component, or generate UI | [21st-dev/magic-mcp](https://github.com/21st-dev/magic-mcp) |

## Use it

```bash
# full design system for a product (the default first call)
python3 skills/ui-ux-pro-max/scripts/search.py "fintech analytics dashboard" --design-system -p "Ops Console"

# persist it for multi-session work
python3 skills/ui-ux-pro-max/scripts/search.py "fintech analytics dashboard" --design-system --persist -p "Ops Console" --output-dir .

# targeted lookups
python3 skills/ui-ux-pro-max/scripts/search.py "empty state onboarding" --domain ux
python3 skills/ui-ux-pro-max/scripts/search.py "glassmorphism dark" --domain style
python3 skills/ui-ux-pro-max/scripts/search.py "fintech trust" --domain color
python3 skills/ui-ux-pro-max/scripts/search.py "streaming suspense" --stack nextjs
```

Domains: `style color chart landing product ux typography icons gsap react web google-fonts`.
Stacks: `react nextjs vue svelte astro swiftui react-native flutter nuxtjs nuxt-ui html-tailwind shadcn jetpack-compose threejs angular laravel javafx wpf winui avalonia uno uwp`.

Tuning dials for `--design-system`: `--variance 1-10` (minimal to brutalist/bento), `--motion 1-10` (micro-interactions to complex choreography), `--density 1-10` (spacious marketing to dense dashboard).

## Install into a project

```bash
../scripts/setup.sh --target /path/to/project --client claude   # or all
```

That copies each skill into the client's skills directory (`.claude/skills`, `.cursor/skills`, `.agents/skills`, `.gemini/skills`, `.windsurf/skills`, `.github/prompts`) exactly like the upstream installer does.

## Updates

These copies are snapshots. To refresh from upstream:

```bash
scripts/vendor-update.sh          # re-vendor from both repos
scripts/vendor-update.sh --check  # report upstream versions only
```

Or install the upstream CLI inside a project when you want the newest release:

```bash
npx ui-ux-pro-max-cli@latest init --ai claude     # ai: claude|cursor|codex|gemini|copilot|windsurf|universal|all
```

Caveat: the upstream CLI generates localized skill content based on your locale (observed producing Chinese section text in an en_US-adjacent environment). The vendored copies here are the upstream repository's English source, which is why the kit defaults to them.

## Provenance and licenses

- UI/UX Pro Max and its sibling skills: MIT, (c) Next Level Builder. See `LICENSE-ui-ux-pro-max.txt`.
- 21st UI skill: ISC, (c) 21st.dev. See `LICENSE-21st-ui.txt`.
- Version and commit pins: `UPSTREAM.md`.

Skill search results are recommendations. They never override you, the project's rules, or a repository's existing design system, and no private project data should be pasted into queries or persisted output.
