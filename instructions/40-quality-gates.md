# 40 - Quality gates

Nothing is "done" until it passes these. Run the checks, paste the real output, then report.

## 1. Build gate (blocking)

```bash
npm run typecheck --if-present
npm run lint --if-present
npm run build
```

- Zero type errors. `@ts-ignore` and `any` require a written reason in the PR.
- Zero lint errors. Warnings get fixed or explicitly waived with a comment.
- The production build must succeed, not just `dev`.
- If the project has tests: `npm test` must pass. If it has none, say so in the report instead of implying coverage.

## 2. Accessibility gate (WCAG 2.2 AA)

| Check | How to verify |
|---|---|
| Contrast 4.5:1 body, 3:1 large text and UI borders | Compute it, do not eyeball. Run the skill: `search.py "text contrast on colored button" --domain ux` |
| Keyboard: every interactive element reachable | Tab through the whole page, no mouse |
| Focus visible | `:focus-visible` ring, 2px+, contrast against both themes |
| No keyboard trap | Modals and menus trap focus intentionally and release on close |
| Accessible names | Icon buttons, inputs, links with image-only content |
| Landmarks and headings | `header/nav/main/footer`, one `h1`, no skipped levels |
| Forms | Label bound with `for`/`htmlFor`, errors via `aria-describedby`, `aria-invalid` |
| Async status | `aria-live="polite"` for toasts and result counts |
| Motion | `prefers-reduced-motion` path exists and works |
| Images and media | Meaningful `alt`, empty `alt=""` for decorative, captions for video |
| Zoom | 200% zoom without content loss, no `user-scalable=no` |
| Target size | 24x24px minimum (2.2), 44x44px recommended |
| Dragging | Any drag interaction has a non-drag alternative |

## 3. Performance gate

Budgets:

| Metric | Budget | Notes |
|---|---|---|
| LCP | < 2.5s mobile | hero image `fetchpriority="high"`, no render-blocking JS |
| CLS | < 0.1 | reserve space for media, fonts, banners |
| INP | < 200ms | break long tasks, debounce input handlers |
| Initial JS | < 200KB gz marketing, < 350KB gz app shell | check with `npx source-map-explorer` or the build output |
| Images | AVIF/WebP, `srcset`, `sizes`, lazy below fold | no 2MB PNGs |
| Fonts | ≤ 2 families, subset, `display: swap`, preconnect or self-host | avoid FOUT jank with `size-adjust` |
| Requests | < 50 on first paint | bundle third-party scripts behind consent or on idle |

Rules:

- Measure before optimizing. Report the tool and number (`next build` output, Lighthouse, or the DevTools performance panel). Never invent a score.
- Third-party scripts (analytics, chat, A/B) load after first paint, never blocking.
- Cache static assets immutably; cache data with explicit revalidation.

## 4. SEO and metadata gate

- `<title>` unique per route, 50-60 chars, brand last.
- Meta description 140-160 chars, written for the user, not stuffed with keywords.
- Canonical URL, Open Graph title/description/image (1200x630), Twitter card.
- `sitemap.xml` and `robots.txt` present and correct for the environment.
- Semantic HTML: `main`, `article`, `section` with headings, `nav` for navigation lists.
- JSON-LD for `Organization`, `Product`, `Article`, `FAQPage` where it applies.
- URL structure: lowercase, hyphenated, no ids in the path when a slug is possible.
- Internal links descriptive ("See pricing", never "click here"). No orphan pages.

## 5. Security gate

- No secrets in client bundles or the repo. Check env usage: anything reachable from the browser is public.
- Input validated server-side with a schema, output escaped. No `dangerouslySetInnerHTML`/`v-html`/`innerHTML` with user data unless sanitized.
- Auth checked on the server for every protected read and write. UI gating is cosmetic only.
- CSRF protection on cookie-based mutations (framework default or explicit token).
- Cookies: `httpOnly`, `secure`, `sameSite=lax` at minimum; no tokens in `localStorage` for auth.
- Uploads: validate type and size, never trust the client, store outside the web root or in object storage.
- Dependencies: no abandoned packages, run `npm audit --omit=dev` and triage findings.
- Headers: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Strict-Transport-Security` on the deploy target.
- Errors: no stack traces, SQL, or internal paths returned to clients. Log with request ids.

## 6. Code quality gate

- Dead code, unused exports, and orphan files removed (not commented out).
- No `console.log` left in shipped code; use the project logger.
- One concern per file; components over ~300 lines get split.
- Naming: files kebab-case or the repo's existing convention, components PascalCase, booleans read as questions (`isOpen`, `hasAccess`).
- Comments explain why, not what. No commented-out code blocks.
- Types at module boundaries; no `any` leaking through props or API responses.
- Tests where behavior is non-obvious: pure helpers, schema parsing, price/date math, permission checks, reducer logic.

## 7. Review protocol (when reviewing someone else's UI or code)

Report findings in this order, each with file and line, severity, and a concrete fix:

1. Correctness: broken behavior, wrong data, race conditions.
2. Accessibility: contrast, keyboard, labels, semantics.
3. Responsiveness: breakpoints, overflow, touch targets.
4. Performance: bundle, CLS, request waterfalls.
5. Consistency: tokens, spacing, component reuse, copy tone.
6. Polish: alignment, easing, focus order, empty states.

Severity tags: `BLOCKER` (must fix before merge), `SHOULD` (fix in this PR), `NIT` (optional). No vague feedback. No rewrite requests without a reason.

## 8. Git and delivery gate

- Commit messages: `<type>: <what changed>` with types `feat|fix|refactor|style|perf|docs|test|chore|build|ci`. One logical change per commit.
- No generated artifacts, `node_modules`, build output, or `.env` files in commits.
- No `--force` pushes to shared branches. No amend after push.
- PR body: what changed, why, how it was verified, screenshots for UI changes, known gaps.
- Screenshots or a short screen recording for any visual change. Before and after.

## 9. Honesty gate

Before claiming completion, answer these:

- Did I run every command I am about to quote? If not, do not quote it.
- Did I verify the routes render, or only that the build compiled?
- Are the placeholders labeled `TODO(content)` so they are not shipped by accident?
- Which parts did I not touch, and could they be affected by this change?

Unverified claims are worse than admitted gaps.
