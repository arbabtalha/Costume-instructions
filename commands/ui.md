---
description: Design or redesign UI with the design intelligence skill, then apply it
argument-hint: [page, component, or "make this look better"]
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Task
---

Target: **$ARGUMENTS**

1. Run the design intelligence search first. Never design from memory:
   ```bash
   python3 skills/ui-ux-pro-max/scripts/search.py "<product> <industry> <keywords>" --design-system -p "<Project>"
   ```
   Add `--variance`, `--motion`, `--density` (1-10) when the product type calls for it (dashboards high density, brand sites high variance).
2. Follow `instructions/20-ui-ux-rules.md` in priority order: accessibility, touch, performance, style, layout, typography and color, motion, forms, navigation, data.
3. If the 21st.dev MCP is connected and this is a recognizable pattern (hero, pricing table, navbar, command palette, data table), search the catalog, show the best two matches, install the chosen one, then adapt it to project tokens. Never claim an install that did not return code.
4. Apply changes to the real files. Tokens only, no raw hex, no magic pixels.
5. Verify: contrast in both themes, keyboard path, focus visible, 375/768/1024/1440, reduced motion, then typecheck + lint + build.

Report: which search commands drove which decisions, what changed, what you could not verify.

Refuse the generic: no centered gradient hero with three identical cards, no emoji icons, no lorem ipsum, no five-font chaos.
