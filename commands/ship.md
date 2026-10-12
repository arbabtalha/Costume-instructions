---
description: Run the quality gates, fix blockers, commit, and write the PR body
argument-hint: [optional scope or PR title hint]
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

Scope: **$ARGUMENTS** (default: everything changed in this session).

Execute `instructions/40-quality-gates.md` in order. Stop and fix anything that fails; do not report success while a gate is red.

1. **Build gate**
   ```bash
   npm run typecheck --if-present && npm run lint --if-present && npm run build
   npm test --if-present
   ```
   Paste the real output. If a script does not exist, say so.
2. **Accessibility gate** - keyboard pass, focus visible, contrast in both themes, names on controls, reduced-motion path.
3. **Performance gate** - report only measured numbers with the tool used. No invented scores.
4. **SEO and security gate** - metadata, OG image, sitemap, robots, no secrets client-side, server-side authorization, input validated.
5. **Git hygiene** - review the diff, remove dead code and debug logs, confirm no `.env`, build output, or `node_modules` is staged.
6. **Commit** in logical chunks with conventional messages (`feat:`, `fix:`, `refactor:`, `style:`, `perf:`, `docs:`, `chore:`).
7. **PR body** - what changed, why, how it was verified, screenshots for UI changes, known gaps, rollback note if risky.

Final output:

```
Gates:    typecheck <pass/fail> | lint <pass/fail> | build <pass/fail> | tests <pass/fail/none>
Commit:   <hashes and subjects>
Verified: <what you actually ran>
Gaps:     <what is still unfinished or unverified>
PR:       <title + body>
```

No "should work". Either it ran, or it is listed under Gaps.
