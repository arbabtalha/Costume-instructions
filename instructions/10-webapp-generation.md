# 10 - Webapp generation protocol

This is the build law for any request that creates or changes a web application: landing pages, dashboards, SaaS products, admin panels, docs sites, internal tools, single-file HTML deliverables.

Read `00-core.md` first (voice and accuracy), then this file top to bottom. Rules are numbered so they can be cited in reviews.

---

## Phase 0 - Intake (before any code)

Extract these eight facts from the request. If four or more are missing, ask up to three questions that change the architecture. Otherwise write the assumption list in one short block and proceed.

1. **Product**: what it is, in one sentence, and who it is for.
2. **Job to be done**: the single action the primary user must complete.
3. **Surface**: marketing page, app shell, dashboard, tool, docs, or embed.
4. **Stack**: detected from the repo when one exists (`package.json`, `pubspec.yaml`, `*.xcodeproj`, `composer.json`), or chosen from the decision tree below. Never silently default a stack.
5. **Content**: real copy, real data, real assets. If none exist, mark every placeholder with `TODO(content)` and keep it obvious.
6. **Constraints**: framework version, design system, brand tokens, browser support, offline, i18n, budget.
7. **Integrations**: auth, payments, database, analytics, third-party APIs.
8. **Done means**: what the user will run or click to accept the work.

**R1.** Never start from a blank file when a repo exists. Read `package.json`, existing components, tokens, and routing before writing. Match what is there.

---

## Phase 1 - Design system before components

**R2.** No page-level styling before tokens exist. Tokens are the contract; components consume them.

Run the design intelligence search that ships with this kit (UI/UX Pro Max) and use its output as the source of truth:

```bash
# in this repo
python3 skills/ui-ux-pro-max/scripts/search.py "<product type> <industry> <keywords>" --design-system -p "Project Name"

# after setup.sh installed it into your project
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<product type> <industry> <keywords>" --design-system -p "Project Name"
```

Persist it so later sessions stay consistent:

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Project Name" --output-dir .
```

That writes `design-system/<slug>/MASTER.md` (global truth) and lets page overrides live in `design-system/<slug>/pages/<page>.md`. Read the MASTER file before touching UI in later sessions. Never regenerate it with `--force` without the user asking.

If the skill is not installed and cannot be installed, fall back to hand-authored tokens, say so, and still follow the token rules below.

**R3.** One token layer, three tiers: primitive (`--color-blue-600`), semantic (`--color-surface`, `--color-text-muted`), component (`--button-bg`). Components reference semantic or component tokens only.

**R4.** Zero raw hex or magic pixel values inside components. Every color, radius, shadow, font size, and spacing step comes from a token. A grep for `#` or `px` in a component file should return almost nothing except 1px borders and similar primitives defined in the scale.

**R5.** Scales are fixed, not improvised:
- spacing: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96
- type: 12 / 14 / 16 / 20 / 24 / 30 / 38 / 48 / 60 (body 16, line-height 1.5 minimum)
- radius: one base with two variants
- shadow: 0 to 3 levels, no decorative shadows on flat surfaces
- z-index: named layers only, never arbitrary numbers

**R6.** Dark mode is a token swap (`prefers-color-scheme` plus a class or `data-theme` override), never a second stylesheet and never a filter. Check contrast in both themes.

**R7.** Fonts: maximum two families, `font-display: swap`, subset where possible, self-host or preconnect. Never load five weights of three families for a landing page.

---

## Phase 2 - Stack and scaffold

Choose with the decision tree. Do not default to React for a five-section marketing page, and do not default to plain HTML for an authenticated app.

| Situation | Stack | Scaffold |
|---|---|---|
| Marketing, docs, blog, content-first, SEO critical | Astro (or Next.js if the team already uses it) | `npm create astro@latest` |
| Authenticated product, dashboard, multi-route app | Next.js App Router + TypeScript | `npx create-next-app@latest --ts --app --tailwind --eslint` |
| SPA inside an existing backend, heavy client state | Vite + React + TypeScript | `npm create vite@latest -- --template react-ts` |
| Vue team | Nuxt 3 or Vite + Vue 3 | `npx nuxi@latest init` |
| Svelte team | SvelteKit | `npx sv create` |
| Single deliverable, no build step, must open by double-click | Hand-written HTML + CSS + minimal JS | one `index.html` |
| Native mobile plus web | React Native / Flutter (see `30-stack-playbooks.md`) | native toolchain |

**R8.** TypeScript strict for any app that will live longer than a demo. No `any` to silence errors; fix the type or write a real `unknown` guard.

**R9.** Component library decision, in order of preference:
1. Reuse what the repo already has.
2. Pull a real component from the 21st.dev catalog through the MCP server (see `60-mcp-and-skill-usage.md`), then adapt it to the project tokens.
3. Add shadcn/ui primitives (`npx shadcn@latest add <component>`) for accessible base behavior.
4. Write it by hand with full keyboard and ARIA support.

**R10.** Every dependency must justify itself. State what it replaces. Banned without a written reason: moment, lodash (use natives), a CSS framework inside a Tailwind project, animation libraries for one fade, icon fonts, jQuery.

**R11.** Structure the app by feature, not by file type:

```
src/
  app/            routes, layouts, route handlers
  components/     shared, presentational, no data fetching
    ui/           primitives (button, input, dialog)
  features/<x>/   components + hooks + schema + tests for one domain
  lib/            pure helpers, clients, config
  styles/         tokens, globals
```

**R12.** Server state belongs to the server. Data fetching happens in server components, loaders, or route handlers, not in `useEffect` chains scattered through presentational components.

---

## Phase 3 - Build order

Build in this order, in one pass each. Do not jump to polish before the shell exists.

1. **Tokens and globals** (Phase 1 output).
2. **Layout shell**: root layout, nav, footer, page container, responsive grid. Verify at 375 / 768 / 1024 / 1440 before continuing.
3. **Generic primitives**: button, input, card, badge, dialog, table, toast. All states: default, hover, focus-visible, active, disabled, loading.
4. **Sections or feature modules**, top to bottom, real content.
5. **States for every async surface**: loading (skeleton that matches final layout), empty (explains the next action), error (what happened plus retry), success, and partial failure.
6. **Forms**: visible labels, inline validation on blur, errors next to the field, disabled state while submitting, success confirmation that says what happens next.
7. **Motion pass**: only where it explains something. 150-300ms, transform and opacity only, `prefers-reduced-motion` respected globally.
8. **SEO and metadata**: title, description, canonical, Open Graph image, `sitemap.xml`, `robots.txt`, semantic landmarks, JSON-LD for content pages.
9. **Verify** (Phase 4), then report (Phase 5).

**R13.** Loading states use skeletons shaped like the final content, not spinners in the middle of an empty page, and not layout shift when data lands.

**R14.** Every interactive element has: `cursor: pointer`, a hover state, a visible focus ring, and a 44x44px minimum touch target. Icon-only buttons carry an accessible label.

**R15.** Never use emoji as icons. Use SVG (Lucide, Heroicons, or the icon data in the UI/UX Pro Max skill).

**R16.** Empty states are designed, not blank. Copy explains why the area is empty and what to click.

**R17.** Copy is written, not lorem ipsum. Button labels are verbs. Error messages say what to do next, not "Something went wrong".

**R18.** Mobile-first CSS. Breakpoints are `sm 640`, `md 768`, `lg 1024`, `xl 1280`. No horizontal scroll at any width from 320px up. No fixed pixel container widths.

**R19.** Images: correct intrinsic `width`/`height` (or aspect-ratio) to prevent CLS, `loading="lazy"` below the fold, `fetchpriority="high"` on the hero, AVIF/WebP with fallback, responsive `sizes` and `srcset`.

**R20.** No layout thrashing: animate transform and opacity, never `width`, `height`, `top`, or `left`. No `scroll` handlers without throttling or IntersectionObserver.

---

## Phase 4 - Accessibility, performance, security gates

Full checklists are in `40-quality-gates.md`. The non-negotiables:

**R21.** WCAG 2.2 AA: text contrast 4.5:1 (3:1 for large text), visible focus, full keyboard operability, no keyboard traps, accessible names on all controls, `aria-live` for async status.

**R22.** Performance budgets: LCP under 2.5s on mid-tier mobile, CLS under 0.1, INP under 200ms, initial JS under 200KB gzipped for a marketing page, under 350KB for an app shell. Report the numbers you measured, and only the ones you measured.

**R23.** Security basics: no secrets in client code or the repo, validate and sanitize all input at the boundary (zod or equivalent), escape anything rendered as HTML (never `dangerouslySetInnerHTML` with user data), authenticate and authorize on the server, rate-limit public endpoints, keep dependencies current.

**R24.** Error handling: no silent catches. Log server errors, show the user a recoverable message with a retry, and add an error boundary or route-level error file so one failure does not blank the app.

**R25.** Types, lint, build must all pass before you say the work is done. Run them yourself:

```bash
npm run typecheck --if-present && npm run lint --if-present && npm run build
```

---

## Phase 5 - Report

Close every build with this block, in this order, short:

```
Built:      <what exists now, file paths>
Ran:        <exact commands and their real result>
Tokens:     design-system/<slug>/MASTER.md (from UI/UX Pro Max)
Checked:    375/768/1024/1440, keyboard pass, contrast, reduced motion
Not done:   <honest gaps, TODO(content) markers, unverified items>
Next:       <one or two concrete next actions>
```

No summary of what the code does line by line. No victory speech.

---

## Anti-pattern list (instant reject)

| Never | Why |
|---|---|
| Purple-to-blue gradient hero with three identical feature cards | Every AI-generated site looks like this. Differentiate or justify. |
| Emoji as icons, lorem ipsum, "Lorem" placeholders left in code | Visible amateur tell |
| Three fonts, four weights, five radii, random hex codes | No system, no coherence |
| Spinner-only loading, blank empty states, generic error toasts | Unfinished |
| `useEffect` data fetching in every component | Waterfalls, race conditions, no caching |
| Hover-only affordances, `outline: none` without replacement | Breaks keyboard and touch |
| Animating `height`/`width`, 1s transitions, no reduced-motion | Jank and accessibility failure |
| Right-aligned `!important` patches and `style={{}}` overrides | Fights the design system |
| Client-side-only auth checks or secrets in `NEXT_PUBLIC_*` | Security hole |
| Copying a component without reading its dependencies | Breaks the build |
| Claiming tests/build passed without running them | Dishonest |

## Definition of done

- [ ] Tokens define every color, space, type size, radius, shadow used in the UI
- [ ] Design system generated or adapted, persisted, and referenced
- [ ] All four states implemented for every async surface
- [ ] Responsive verified at 320, 375, 768, 1024, 1440, no horizontal scroll
- [ ] Keyboard traversal complete, focus visible, no traps, no mouse-only features
- [ ] Contrast checked in light and dark themes
- [ ] Reduced motion respected
- [ ] Meta tags, OG image, sitemap, robots, semantic landmarks, one `h1` per page
- [ ] Images sized and optimized, fonts swapped, no CLS from media
- [ ] `typecheck`, `lint`, `build` pass with real output shown
- [ ] No secrets, no committed `.env`, no stray `console.log`, no dead files
- [ ] Report block written with honest gaps
