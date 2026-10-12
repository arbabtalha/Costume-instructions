# 20 - UI/UX rules (priority ordered)

The 22-stack, 79-style, 192-palette design database lives in `skills/ui-ux-pro-max/`. This file is the part every agent must carry in its head: the priority order, the checks, the anti-patterns.

## Priority order

Fix in this order. A beautiful page with a broken contrast ratio is a broken page.

| # | Category | Impact | Must have | Anti-pattern |
|---|---|---|---|---|
| 1 | Accessibility | CRITICAL | 4.5:1 contrast, alt text, keyboard path, aria labels | removing focus rings, icon-only buttons with no label |
| 2 | Touch and interaction | CRITICAL | 44x44px targets, 8px+ spacing, press/loading feedback | hover-only affordances, 0ms state changes |
| 3 | Performance | HIGH | WebP/AVIF, lazy below fold, reserved space (CLS < 0.1) | layout thrash, unsized media |
| 4 | Style selection | HIGH | one language, matched to product type, SVG icons | mixing flat and skeuomorphic, emoji as icons |
| 5 | Layout and responsive | HIGH | mobile-first breakpoints, viewport meta, no h-scroll | fixed px containers, zoom disabled |
| 6 | Typography and color | MEDIUM | 16px base, 1.5 line-height, semantic tokens | 12px body text, gray-on-gray, hex in components |
| 7 | Animation | MEDIUM | 150-300ms, meaning-carrying, reduced motion | one duration everywhere, animating layout props |
| 8 | Forms and feedback | MEDIUM | visible labels, inline errors, helper text | placeholder-only labels, errors only at the top |
| 9 | Navigation | HIGH | predictable back, ≤5 bottom-nav items, deep links | overloaded nav, broken back button |
| 10 | Charts and data | LOW | legends, tooltips, non-color encoding | color as the only signal |

## Layout

- One primary action per screen. If two elements compete, demote one.
- Establish hierarchy with size, weight, and space before color.
- Use a 12-column grid on desktop, single column on mobile. Gutters from the spacing scale.
- Vertical rhythm: section padding 64-96px desktop, 40-56px mobile. Do not improvise.
- Max content width 60-75 characters for prose, 1280px for app shells.
- Density is a decision: marketing is spacious (24-96px scale), dashboards are dense (8-32px scale). Pick once per surface.
- Alignment beats decoration. Everything sits on the same grid.

## Typography

- Two families maximum: one for headings/display, one for UI/body. Often one is enough.
- Body 16px minimum, line-height 1.5-1.7, paragraph max width 70ch.
- Weights: use 2-3, not 6. Use size and color for emphasis before heavy weights.
- Never justify text. Never letter-space body copy. Balance headings (`text-wrap: balance`), avoid orphans.
- Numeric tables and stats get tabular numerals (`font-variant-numeric: tabular-nums`).

## Color

- 60/30/10: neutral surface, secondary tone, accent.
- Accent color is reserved for the primary action. If everything is accent-colored, nothing is.
- Semantic naming only in components: `--color-surface`, `--color-danger`, `--color-border`.
- Text on colored fills: check 4.5:1 against the fill, not against white.
- Never signal state with color alone. Pair with icon, label, or shape.
- Dark mode is not inverted light mode: reduce saturation, keep contrast, avoid pure black on pure white.

## Space and surface

- Space communicates grouping. Related items closer, unrelated items farther. No exceptions for aesthetics.
- Three shadow levels maximum, all from tokens. Flat surfaces stay flat.
- Borders and shadows are alternatives, not both, unless the design system says otherwise.
- Radius is a system decision: one scale, applied consistently (buttons and inputs share it).

## Motion

- Durations: 100-150ms micro (hover, press), 200-300ms transitions (drawer, modal), 300-500ms only for meaningful choreography.
- Easing: ease-out for entrances, ease-in for exits, ease-in-out for movement.
- Animate `transform` and `opacity`. Nothing else unless you measured it.
- Motion explains state change or spatial relationship. Decorative animation is a liability.
- Every animation respects `@media (prefers-reduced-motion: reduce)` and provides a static final state.

## Forms

- Label above the field, always visible. Placeholder is an example, never a label.
- Validate on blur and on submit, not on every keystroke.
- Error text next to the field, in text as well as color, with `aria-describedby` wired up.
- Autofocus the first field on a dedicated form page; never autofocus on mobile keyboards that cover the CTA.
- Submit button shows loading state and is disabled while pending. Prevent double submits.
- Multi-step: show progress, allow going back, preserve entered data.
- Success tells the user what happens next ("We sent a link to your@email.com").

## Navigation

- Desktop: horizontal nav, current item visibly marked, no more than 7 top-level items.
- Mobile: bottom nav for up to 5 app destinations, or a drawer for overflow. Never both for the same items.
- Breadcrumbs for anything 3 levels deep, in apps with hierarchy.
- Browser back must work. No route changes without history entries. Filters and tabs belong in the URL.
- Deep links: every meaningful view has a URL that restores it.

## Data display

- Tables: right-align numbers, left-align text, sticky header past 20 rows, sortable columns get an indicator, empty state explains itself.
- Charts: label axes, no 3D, no truncated y-axis on bar charts, accessible color sequence plus shape/label alternatives.
- Dashboards: KPI above the fold, trend next, detail below. Every number has a time range and a comparison.
- Skeletons for tables and cards, not spinners.
- Format numbers, dates, and currency with `Intl`. Locale-aware, never hand-rolled string math.

## Component states

Every interactive component defines all of: default, hover, focus-visible, active, disabled, loading, error (where applicable), empty (where applicable), and overlong-content behavior. Truncate with a tooltip or wrap, never clip silently.

## Content

- Button labels are verbs that describe the outcome ("Create project", not "Submit").
- Empty states: what this is, why it is empty, one action.
- Error copy: what failed, what to do next, whether data was saved.
- Microcopy is specific. "We'll email you a receipt" beats "Your request was processed".

## Pre-delivery checklist (copy into the PR)

- [ ] No emoji used as icons
- [ ] `cursor: pointer` on all clickable elements
- [ ] Hover states with 150-300ms transitions
- [ ] Text contrast 4.5:1 in light theme
- [ ] Text contrast 4.5:1 in dark theme
- [ ] Visible focus state for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive verified at 375, 768, 1024, 1440
- [ ] No horizontal scroll at 320px
- [ ] Empty, loading, error states designed
- [ ] Images sized, lazy below fold, hero prioritized
- [ ] All interactive elements keyboard reachable with accessible names

## Deeper search

Query the skill with a single dominant intent and 2-5 terms. One domain at a time.

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "error summary validation" --domain ux
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "glassmorphism dark" --domain style
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "fintech trust" --domain color
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "saas modern clean" --domain typography
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "virtualized list" --stack react
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "streaming suspense" --stack nextjs
```

Domains: `style color chart landing product ux typography icons gsap react web google-fonts`.
Stacks: `react nextjs vue svelte astro swiftui react-native flutter nuxtjs nuxt-ui html-tailwind shadcn jetpack-compose threejs angular laravel javafx wpf winui avalonia uno uwp`.

If a query returns nothing useful, retry once with a narrower rewrite. If that fails, say no verified match was found and label your fallback as general guidance. Do not persist unverified output into the design system.
