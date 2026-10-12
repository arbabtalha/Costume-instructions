# Gemini CLI context

This project ships the **Costume Webapp Kit**: instructions, a local UI/UX design intelligence skill, and MCP wiring so the agent can build production web apps instead of demos.

Read `AGENTS.md` first. It is the single source of truth for rules and routing. Then load only the instruction file the task needs from `instructions/`:

- `00-core.md` - voice, accuracy, slash commands
- `10-webapp-generation.md` - the build protocol (read this for any app work)
- `20-ui-ux-rules.md` - design, UX, accessibility priorities
- `30-stack-playbooks.md` - Next.js, Vite/React, Astro, Vue/Nuxt, SvelteKit, plain HTML
- `40-quality-gates.md` - pre-ship checks
- `50-prompt-recipes.md` - user-facing prompt templates
- `60-mcp-and-skill-usage.md` - using the skill and the 21st.dev MCP

Non-negotiables: tokens before components, run the design skill before designing, all loading/empty/error states, WCAG 2.2 AA, responsive from 320px, real content, typecheck/lint/build before claiming done, honest report including gaps.

Design skill:

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "saas analytics dashboard" --design-system -p "Ops Console"
python3 skills/ui-ux-pro-max/scripts/search.py "empty state onboarding" --domain ux
```

MCP: `mcp/configs/gemini.json` (merge into `~/.gemini/settings.json`), key from https://21st.dev/mcp. Full notes in `mcp/21st-mcp.md`.
