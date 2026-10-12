# 21st.dev MCP (formerly Magic MCP)

The server asked for in the original setup request: **`21st-dev/magic-mcp`**.

Important fact as of this writing: Magic MCP was replaced by the unified **21st MCP**. The `@21st-dev/magic` npm package (v0.2.3) is now a thin stdio compatibility proxy that forwards to the same server, so old configs keep working. New setups should use the 21st CLI or the HTTP endpoint directly.

- Server type: streamable HTTP MCP
- Endpoint: `https://21st.dev/api/mcp`
- Auth: header `x-api-key: <YOUR_KEY>`
- API key: free and instant at <https://21st.dev/mcp>
- Old Magic API keys were reset and no longer work anywhere.

## Install (pick one)

### Option A - official CLI (recommended)

```bash
npx @21st-dev/cli@latest init --client cursor    # then re-run with --write to merge the config
npx @21st-dev/cli@latest init --client claude
npx @21st-dev/cli@latest init --client codex
npx @21st-dev/cli@latest init --client vscode
npx @21st-dev/cli@latest init --client devin     # windsurf is accepted as an alias
```

Set `API_KEY_21ST` in your environment (or in the client's plugin configuration) before starting the editor.

### Option B - this repo's installer

```bash
./scripts/install-mcp.sh --client claude     # or cursor | vscode | codex | windsurf | gemini | all
```

It copies the right file from `mcp/configs/` into your project (or writes the global config with `--global`) and never overwrites without `--force`.

### Option C - manual, by client

| Client | File | Source in this repo |
|---|---|---|
| Claude Code (project) | `.mcp.json` | `mcp/configs/claude-code.json` |
| Claude Code (CLI) | `claude mcp add --transport http 21st https://21st.dev/api/mcp --header "x-api-key: $API_KEY_21ST"` | - |
| Cursor | `.cursor/mcp.json` | `mcp/configs/cursor.json` |
| VS Code / Copilot | `.vscode/mcp.json` | `mcp/configs/vscode.json` |
| Codex CLI | `~/.codex/config.toml` | `mcp/configs/codex.toml` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | `mcp/configs/windsurf.json` |
| Gemini CLI | `~/.gemini/settings.json` | `mcp/configs/gemini.json` |
| Claude Desktop | `claude_desktop_config.json` | `mcp/configs/claude-desktop.json` |
| Anything else HTTP-capable | - | `mcp/configs/generic-http.md` |

Raw config, minimal form:

```json
{
  "mcpServers": {
    "21st": {
      "url": "https://21st.dev/api/mcp",
      "headers": { "x-api-key": "${API_KEY_21ST}" }
    }
  }
}
```

### Option D - stdio compatibility proxy (clients without HTTP MCP)

```json
{
  "mcpServers": {
    "21st": {
      "command": "npx",
      "args": ["-y", "@21st-dev/magic@latest"],
      "env": { "API_KEY_21ST": "your-key" }
    }
  }
}
```

The key is also accepted as `API_KEY="..."`, `--API_KEY=...`, `/API_KEY:...`, or via `TWENTY_FIRST_API_KEY` / `API_KEY_21ST`.

### Option E - install the upstream plugin instead

The upstream repo is itself a plugin marketplace:

```bash
# Claude Code
claude plugin marketplace add 21st-dev/magic-mcp   # then: /plugin install 21st

# Grok Build
grok plugin marketplace add 21st-dev/magic-mcp && grok plugin install 21st --trust

# Codex CLI
codex plugin marketplace add 21st-dev/magic-mcp    # then install "21st" from /plugins
```

## Tools

| Tool | Purpose |
|---|---|
| `search` | find components, themes, templates in the catalog |
| `get_component` | fetch full code + metadata for a result |
| `get_inspiration` | browse styles and ideas |
| `search_logo` | brand logo as JSX/TSX, one brand per call |
| `generate` | hosted UI generation (listed only with AI access enabled) |
| `iterate_generation` | refine a generation |
| `get_usage` | account capabilities, includes `aiGenerationEnabled` |

Legacy names are translated server side:

| Magic tool | Current |
|---|---|
| `21st_magic_component_builder` | `generate` |
| `21st_magic_component_inspiration` | `get_inspiration` |
| `21st_magic_component_refiner` | `generate` |
| `logo_search` | `search_logo` |

## Limits and gotchas

- **Free tier**: catalog search plus 2 component installs per day. Paid components return code only after unlock.
- **AI generation is separate**: component access does not enable hosted AI. If `generate` is missing from the tool list, AI is off for the account. `get_usage.aiGenerationEnabled` reports access, not remaining credits.
- `ai_subscription_required` means exactly that. Do not retry; enable AI, then refresh the tool list or reconnect.
- **Old keys were reset.** If you get auth errors with a key from the old Magic console, generate a new one.
- `.mcp.json` supports `${VAR}` expansion in Claude Code; other clients differ (VS Code uses `${env:VAR}`, Gemini's file wants the literal key). See the configs.
- Restart the client after changing MCP config. Most clients only read it at startup.

## Using it well (agent behavior)

See `instructions/60-mcp-and-skill-usage.md`. Short version: search the catalog before writing generic UI, adapt whatever you install to the project's tokens, and never claim an install succeeded unless you wrote the returned code into the repo.

## Verify

```bash
# in the client
/mcp                      # Claude Code: lists servers and their status
# tools/list should show search, get_component, get_inspiration, search_logo

# from a shell, check the endpoint answers (needs a valid key)
curl -sS -X POST https://21st.dev/api/mcp \
  -H "content-type: application/json" \
  -H "accept: application/json, text/event-stream" \
  -H "x-api-key: $API_KEY_21ST" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

This repo's CI cannot test the endpoint (no key, and the sandbox used to build the kit has no route to `21st.dev`). Everything documented here comes from the upstream repo (`21st-dev/magic-mcp`) at the time of writing: README, `mcp.json`, `server.json`, `package.json`, and the plugin manifests.
