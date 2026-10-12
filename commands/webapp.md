---
description: Build or extend a web app end to end using the Costume protocol
argument-hint: [what to build, for whom, stack if you care]
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Task, WebFetch
---

Build this: **$ARGUMENTS**

Follow `instructions/10-webapp-generation.md` exactly. Sequence:

1. **Intake.** Extract product, primary job, surface, stack, content, constraints, integrations, definition of done. If four or more are missing, ask up to three questions that change the architecture. Otherwise state assumptions in one block and continue.
2. **Design system.** Run the UI/UX Pro Max search, persist it, and write the tokens:
   ```bash
   python3 skills/ui-ux-pro-max/scripts/search.py "<product> <industry> <keywords>" --design-system --persist -p "<Project>" --output-dir .
   ```
3. **Plan.** If the work touches more than three files, delegate to the `webapp-architect` subagent for the plan, then execute it.
4. **Build** in order: tokens, layout shell, primitives, sections, states, motion, SEO.
5. **Design review.** Delegate to `ui-ux-designer` if layout or visual direction is debatable.
6. **Implement.** Delegate to `frontend-implementer` for mechanical breadth, or write it directly.
7. **Verify.** Take a pass with `qa-reviewer`. Run typecheck, lint, build, and paste real output.

Constraints you must honor: tokens only, all four async states, WCAG 2.2 AA, responsive from 320px up, real content, reduced-motion path, no new dependency without justification.

Close with the report block: Built / Ran / Checked / Not done / Next. Include unfinished work honestly.
