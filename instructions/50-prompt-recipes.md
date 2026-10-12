# 50 - Prompt recipes

Copy these into any AI coding agent that has this kit installed. They assume the agent reads `AGENTS.md` and has the UI/UX Pro Max skill plus the 21st.dev MCP available. Add your product specifics and delete what does not apply.

## 1. New product, from scratch

```
Build <product> for <audience>. The one job: <primary action>.
Stack: <Next.js 15 App Router | Astro | Vite+React | plain HTML>.
Read AGENTS.md and instructions/10-webapp-generation.md, then:
1. Run the UI/UX Pro Max design system search for <product type + keywords> and persist MASTER.md.
2. Build tokens -> layout shell -> primitives -> sections -> states.
3. Verify at 375/768/1024/1440, keyboard pass, contrast, reduced motion.
4. Run typecheck + lint + build and paste the output.
Report with the Built/Ran/Checked/Not done/Next block.
```

## 2. Landing page that does not look AI-generated

```
Build a landing page for <product>.
Constraints:
- One clear primary action, repeated at most 3 times.
- Layout must NOT be a centered gradient hero with three identical feature cards.
  Use <asymmetric split | editorial | bento | product screenshot-led>.
- Real copy for <product>. Every string must be specific, no lorem ipsum.
- Pull one visual idea from the 21st.dev catalog (search "hero", "pricing table", "testimonial")
  and adapt it to my tokens instead of writing from scratch.
- Sections: <hero, proof, how it works, features, pricing, FAQ, CTA>.
Section order and CTA placement must come from a `--domain landing` search.
```

## 3. Dashboard or admin panel

```
Build the <name> dashboard for <domain>.
- KPI row above the fold, trend chart second, table third.
- Data comes from <endpoint / mock file>. Keep one data layer, no per-component fetching.
- States: loading skeletons matching final layout, empty, error with retry, partial failure.
- Table: sortable, sticky header past 20 rows, right-aligned numerics, tabular numerals.
- Charts: accessible palette, labels, tooltips, no color-only encoding. Search `--domain chart`.
- Density: pass --density 8 to the design system search; 8-32px spacing scale.
- Accessible by keyboard, filters reflected in the URL.
Build, then verify and report honestly.
```

## 4. Convert a screenshot or Figma export to code

```
Here is a screenshot of the design. Recreate it as production code.
- <stack> with my existing tokens; map the design's colors/spacing onto my scale,
  and tell me where the design conflicts with the scale.
- Responsive: mobile first, adapt rather than shrink.
- Preserve hierarchy, do not pixel-copy defects like low contrast. Flag any
  contrast ratio under 4.5:1 and propose the nearest passing token.
- Interactive elements get all states (hover, focus-visible, active, disabled).
```

## 5. Upgrade the UI of an existing repo

```
Audit and fix the UI in this repo, highest impact first.
Order: accessibility -> touch targets -> performance -> style consistency -> layout -> typography -> motion.
For each issue: file, line, severity (BLOCKER/SHOULD/NIT), concrete fix.
Apply the fixes, then run typecheck + lint + build and show the output.
Do not restructure the app. Do not rename public components.
```

## 6. Fix a broken build

```
<build fails / page is blank>. Find the root cause.
- Read the actual error output first, do not guess.
- Reproduce with the smallest command that fails.
- Fix the cause, not the symptom. No @ts-ignore, no try/catch to hide it, no dependency downgrade without explaining.
- State the root cause in one line, then what you changed, then re-run the failing command and paste the result.
```

## 7. Add one component the right way

```
Add a <pricing table | navbar | testimonials | command palette | data table>.
1. Search the 21st.dev catalog through MCP for the component type.
2. Show me the 2 best matches with a one-line difference.
3. Install the chosen one, then adapt it to my tokens, folder layout, and cn() helper.
4. Add all states, keyboard support, and a mobile layout.
5. Wire it into <page> and verify.
```

## 8. Design system extraction

```
Extract a design system from this codebase or screenshot:
- primitive tokens (color ramps, type scale, spacing, radius, shadow, z-index)
- semantic tokens mapped on top (surface, text, border, accent, danger, success)
- component tokens for buttons, inputs, cards, tables
- dark mode mapping for every semantic token
Output as CSS custom properties plus a Tailwind @theme block, and
a short table of what changed versus the current values.
Search the skill with --design-system and reconcile your output with it.
```

## 9. Performance pass

```
Run a performance pass on <page>:
- Report measured LCP/CLS/INP and initial JS size, with the tool and command used.
- Fix the two worst items only, then re-measure and show the delta.
- Do not optimize anything you did not measure.
- Do not add a heavier dependency to fix a small problem.
```

## 10. Pre-ship review

```
/review then /ship. Act as a senior frontend reviewer with taste.
Blockers: accessibility, correctness, security, build failures.
Then consistency with tokens, responsiveness, empty/loading/error states, copy quality, motion.
Output a numbered list with file:line and severity, then apply the BLOCKER and SHOULD fixes,
then produce the report block plus a PR body I can paste.
```

## Rules for writing your own prompt

- Name the product, the audience, and the single primary action.
- Name the stack, or say "detect from the repo".
- Name the constraints that change the design (SEO, offline, i18n, existing design system, browser support).
- Ask for the verification you want to see, and expect real command output, not a claim.
- Ask for the honest gaps. Every build has them.
