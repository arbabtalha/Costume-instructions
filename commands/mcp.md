---
description: Check, install, or debug the 21st.dev MCP connection and the design skill
argument-hint: [status | install [client] | debug | skill]
allowed-tools: Read, Write, Edit, Bash, Glob
---

Task: **$ARGUMENTS** (default: `status`).

### status

- Is `API_KEY_21ST` set in the environment? Print only whether it exists, never the value.
- Does the client config exist and reference `https://21st.dev/api/mcp`? Check `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, `~/.codex/config.toml`, `~/.gemini/settings.json`, `~/.codeium/windsurf/mcp_config.json`.
- Is the design skill installed and runnable?
  ```bash
  python3 .claude/skills/ui-ux-pro-max/scripts/search.py "saas dashboard" --design-system -p "Smoke Test" | head -20
  ```
- Report each item as present, missing, or misconfigured, with the exact next command.

### install [client]

```bash
./scripts/install-mcp.sh --client <claude|cursor|vscode|codex|windsurf|gemini|all>
```
Then: set `API_KEY_21ST` (free key at https://21st.dev/mcp), restart the client, and run `/mcp` to confirm the server connects. Full matrix in `mcp/21st-mcp.md`.

### debug

Walk this list in order and stop at the first failure:

1. Auth error → the key is missing, wrong, or from the old Magic console (those were reset). Generate a new one.
2. Server not listed → the client was not restarted, or the config file is in the wrong place for that client.
3. `generate` missing from the tool list → hosted AI is not enabled for the account. `get_usage.aiGenerationEnabled` reports access, not credits.
4. `ai_subscription_required` → stop retrying. Enable AI, then refresh the tool list or reconnect.
5. Quota errors → free tier is catalog search plus 2 component installs per day. Do not retry around the limit.
6. Network blocked → continue without MCP; say so and use the local skill plus hand-written components.

### skill

Confirm the skill is available, show which path holds it for this client (`.claude/skills`, `.cursor/skills`, `.agents/skills`, `.gemini/skills`, `.windsurf/skills`, or `skills/` in this repo), and run one design-system search as a smoke test.

Never print API keys. Never fabricate tool output. If a tool call fails, quote the real error.
