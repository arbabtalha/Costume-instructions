# 30 - Stack playbooks

Pick one stack per project (see `10-webapp-generation.md`, Phase 2). These are the defaults this kit builds with, the file layout expected, and the traps that actually break builds.

Every playbook ends with the same verification: typecheck, lint, build, then click through the running app.

---

## Next.js (App Router) - default for real products

Scaffold:

```bash
npx create-next-app@latest my-app --typescript --app --tailwind --eslint --src-dir --import-alias "@/*"
npx shadcn@latest init
```

Layout:

```
src/app/
  layout.tsx            root layout: fonts, theme provider, metadata
  page.tsx              route
  loading.tsx           route-level skeleton
  error.tsx             route-level error boundary (client)
  not-found.tsx
  globals.css           tokens + base
  <route>/page.tsx
  api/<route>/route.ts  route handlers
src/components/ui/      primitives
src/features/<x>/       feature components, hooks, zod schemas
src/lib/                utils, clients, config
```

Rules:

- Server components by default. Add `"use client"` only at the smallest leaf that needs state or browser APIs.
- Data fetching on the server: `await` in the component, or `fetch` with an explicit `cache`/`revalidate`. Never `useEffect` for initial data.
- Mutations go through server actions or route handlers, then `revalidatePath`/`revalidateTag`. Not client-side fetch plus manual state sync.
- Metadata via the `metadata` export and `generateMetadata`. Set `metadataBase` so OG images resolve.
- Fonts via `next/font`. Never a `<link>` to Google Fonts.
- Images via `next/image` with `width`/`height` or `fill` inside an aspect-ratio box.
- Dynamic routes: `params` are async in Next 15, `await params`. Missing that is the most common build break.
- Keep secrets in server-only env (`process.env.X`). Anything prefixed `NEXT_PUBLIC_` is public forever.

Traps: `useSearchParams` needs a Suspense boundary; `cookies()`/`headers()` are async in 15; client components cannot import server-only modules; `next build` fails on unused imports only if lint is wired to fail, do not rely on lint to catch type errors.

---

## Vite + React - SPAs and embeds

```bash
npm create vite@latest my-app -- --template react-ts
npm i -D tailwindcss @tailwindcss/vite
```

Rules:

- Tailwind v4 uses the `@tailwindcss/vite` plugin plus `@import "tailwindcss";` in the entry CSS. No `tailwind.config.js` unless you need custom plugins; theme goes in `@theme {}`.
- Data layer: TanStack Query for server state, or plain `fetch` in a single `api/` module. Never fetch the same endpoint from three components.
- Routing: React Router with a layout route and nested routes. Set `errorElement`.
- Code-split every panel behind `React.lazy` once the bundle crosses 200KB gzipped.
- Env vars need the `VITE_` prefix and are public. Nothing secret in a Vite app.

---

## Astro - marketing, docs, content, SEO

```bash
npm create astro@latest my-site
npx astro add tailwind
```

Rules:

- Zero client JS by default. Add `client:visible` or `client:idle` only for genuinely interactive islands.
- Content collections for anything repeated; Zod schemas for frontmatter.
- `src/layouts/BaseLayout.astro` owns `<head>`, meta, OG, canonical, and JSON-LD.
- Static output plus sitemap integration. Add a prerender flag only where needed.
- Inline critical CSS, defer the rest. Ship images through `astro:assets` for automatic optimization.

---

## Vue 3 / Nuxt

- Nuxt for SSR/SEO; plain Vite + Vue for internal tools.
- `<script setup lang="ts">` everywhere. Props typed with `defineProps<{...}>()`.
- State: `useState` (Nuxt) or Pinia. Not a global `reactive` object.
- `useFetch`/`useAsyncData` on the server. Never both plus a client fetch for the same data.
- Nuxt UI or shadcn-vue for primitives; keep the same token discipline as React projects.

---

## SvelteKit

- Routes in `src/routes`, data in `+page.server.ts` load functions, page state in `+page.svelte`.
- Form actions for mutations, `use:enhance` for progressive enhancement.
- $state/$derived runes in Svelte 5; never mix in legacy stores in new code.
- Adapters per deploy target (`adapter-auto` for Vercel/Netlify, `adapter-static` for pure static).

---

## Single-file HTML - demo, client deliverable, no build step

One file, opens by double-click, zero network dependencies for core function.

Rules:

- `<meta charset>`, viewport, title, description in the head. Semantic landmarks (`header`, `nav`, `main`, `footer`).
- Tokens as CSS custom properties in `:root`, with a `@media (prefers-color-scheme: dark)` override block.
- System font stack or one self-contained font. No CDN fonts unless the user asked for them.
- Vanilla JS, no framework, event listeners delegated, no inline `onclick` attributes.
- Accessible from the keyboard, works with JS disabled for content (progressive enhancement).
- Ship the design in `starters/html-landing/index.html` as the starting point and adapt it, do not start blank.

---

## Tailwind discipline (all stacks)

- Tokens in the theme config or `@theme` block; utilities reference them (`bg-surface`, `text-muted`), not raw values (`bg-[#f5f5f4]`).
- Class order: layout, box, typography, background, border, effects, state, responsive. Keep it consistent so diffs stay readable.
- Extract a component when the same class string appears three times, not before.
- `cn()` (clsx + tailwind-merge) for conditional classes. Never string concatenation.
- Variants via CVA for anything with more than two visual variants.
- No `!important`. If you need it, the token or the component boundary is wrong.

---

## shadcn/ui discipline

- `npx shadcn@latest add button dialog table` installs source into your repo. Treat that code as yours: restyle it with tokens, do not fight it with wrapper divs and overrides.
- Keep the registry components in `components/ui/` untouched in structure so future `add` and `diff` keep working.
- Extend with variants in the same file or a colocated variants file. Do not fork into `components/ui2/`.

---

## Backend-adjacent rules (any stack)

- Validate at the boundary: zod (or valibot) schema per route handler or server action, parse, then use the typed result.
- One error shape for the API: `{ error: { code, message, details? } }`. Never leak stack traces to the client.
- Auth: session cookies `httpOnly`, `secure`, `sameSite=lax`, checked on the server for every protected route and every mutation. UI hiding is not authorization.
- Database access through one client module, queries parameterized, migrations committed.
- Rate-limit and size-limit public endpoints and uploads.
- Background work belongs in a queue or a scheduled job, not in a request handler that the user waits on.

---

## Environment and scripts

Every project this kit scaffolds ends up with these scripts in `package.json` (add the missing ones):

```json
{
  "scripts": {
    "dev": "…",
    "build": "…",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "format": "prettier --write .",
    "test": "…"
  }
}
```

`.env.example` committed with every variable name and a placeholder value. `.env` never committed. `README` states the runtime version (`.nvmrc` or `engines.node`).
