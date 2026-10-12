# Starters

Copy-paste starting points that already follow the kit's rules. They are small on purpose: enough structure to be correct, not enough to be in the way.

## `html-landing/index.html`

A production-grade single-file landing page: design tokens, light and dark themes, semantic landmarks, skip link, keyboard-accessible everything, `prefers-reduced-motion` handling, inline SVG icons (no emoji, no icon fonts), real copy, schema.org JSON-LD, and zero dependencies. Opens by double-click.

Use it when:

- The deliverable is a single file (client handoff, demo, static host).
- You need a fast baseline before a framework is chosen.
- You want a worked example of every rule in `instructions/10-webapp-generation.md` applied at once.

Adapt in this order: tokens in `:root`, then content, then sections. Delete what you do not need instead of leaving dead markup.

What it demonstrates, if you are reviewing it:

- Token layers: primitive (`--stone-500`), semantic (`--color-surface`), component-level usage in the buttons
- Asymmetric hero instead of the centered gradient cliché
- Bento grid with one wide cell instead of three identical cards
- `aria-labelledby` on every section, `aria-hidden` on decorative SVG, labeled terminal mock with `role="img"`
- Focus-visible rings, 44px minimum targets, contrast checked in both themes
- Native `<details>` FAQ, no JS required
- Motion that respects `prefers-reduced-motion`, only `opacity` and `transform`
- One small progressive-enhancement script, page works with JS disabled

## Framework starters

Do not hand-build a scaffold. Use the official one, then apply the kit:

```bash
# Next.js (default for real products)
npx create-next-app@latest my-app --typescript --app --tailwind --eslint --src-dir --import-alias "@/*"
npx shadcn@latest init

# Vite + React (SPA, embed, existing backend)
npm create vite@latest my-app -- --template react-ts

# Astro (marketing, docs, content, SEO)
npm create astro@latest my-site && npx astro add tailwind

# Vue / Nuxt
npx nuxi@latest init my-app

# SvelteKit
npx sv create my-app
```

Then, in order:

1. Install the kit: `../scripts/setup.sh --target my-app --client claude` (or `all`).
2. Generate the design system: `python3 skills/ui-ux-pro-max/scripts/search.py "<product> <keywords>" --design-system --persist -p "My App" --output-dir .`
3. Wire the tokens into the framework's theme mechanism (Tailwind `@theme`, CSS `:root`, or the design-system package).
4. Follow `instructions/30-stack-playbooks.md` for that stack's file layout and traps.

The kit expects every started project to end up with `dev`, `build`, `typecheck`, `lint`, and `test` scripts, a committed `.env.example`, and a README that names the runtime version.
