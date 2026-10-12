# Claude Code instructions

@AGENTS.md

The import above is the full rule set. This file adds only what is Claude Code specific.

## Project layout for Claude Code

- `agents/` - subagents: `webapp-architect`, `ui-ux-designer`, `frontend-implementer`, `qa-reviewer`. Delegate multi-step work to them with the Task tool.
- `commands/` - `/webapp`, `/ui`, `/review`, `/ship`, `/mcp`.
- `skills/` - auto-discovered skills. `ui-ux-pro-max` is the design intelligence database; load it whenever the task touches UI.
- `.mcp.json` - the 21st.dev MCP server. Requires `API_KEY_21ST` in your environment. Check with `/mcp`; if the server is down, follow the fallback path in `instructions/60-mcp-and-skill-usage.md`.

## Working style here

- Use the design skill through Bash, not from memory: `python3 skills/ui-ux-pro-max/scripts/search.py ...`.
- Plan before writing when the change touches more than three files. State the plan in one short block, then execute it.
- Run `npm run typecheck`, `npm run lint`, and `npm run build` (or the stack equivalent) before reporting done.
- Keep commits one logical change each, with conventional commit messages.

## Installing this kit into another project

```bash
./scripts/setup.sh --target /path/to/project --client claude --mcp
```

Or install the repo directly as a plugin:

```bash
claude plugin marketplace add arbabtalha/Costume-instructions
/plugin install costume-webapp-kit
```
