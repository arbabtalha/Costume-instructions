---
description: Audit code or UI and report ranked findings with file:line and fixes
argument-hint: [path, PR, or "everything I just changed"]
allowed-tools: Read, Grep, Glob, Bash, Task
---

Scope: **$ARGUMENTS** (default: uncommitted changes).

Delegate to the `qa-reviewer` subagent, then verify its blockers yourself. Review order is fixed by `instructions/40-quality-gates.md` section 7:

1. Correctness - broken behavior, race conditions, unhandled rejections, silent catches.
2. Accessibility - contrast (compute it), keyboard, focus, names, semantics, labels, reduced motion.
3. Responsiveness - 320 to 1440, overflow, touch targets.
4. Performance - measured numbers only, bundle, waterfalls, unsized media.
5. Security - secrets, server-side authorization, validation, escaping, cookies.
6. Consistency - tokens versus hardcoded values, reuse, naming.
7. Copy and polish - verb labels, actionable errors, guiding empty states.

Useful greps:

```bash
grep -rnE "#[0-9a-fA-F]{3,8}" --include='*.tsx' --include='*.css' src | head -40
grep -rn "!important\|outline: *none\|dangerouslySetInnerHTML\|: any\|console\.log" --include='*.ts*' src | head -40
```

Output:

```
BLOCKER  path:line  problem. Fix: concrete change.
SHOULD   path:line  problem. Fix: concrete change.
NIT      path:line  problem. Fix: concrete change.
---
Checked:     what you verified and how
Not checked: what you could not verify and why
Verdict:     ship | ship after blockers | needs rework
```

No vague feedback, no rewrites, no invented issues. If it is clean, say so in one line.
