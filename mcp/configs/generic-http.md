# Any HTTP-capable MCP client

Transport: streamable HTTP
Endpoint:  https://21st.dev/api/mcp
Auth:      header  x-api-key: <YOUR_21ST_API_KEY>

Get a free key (issued instantly) at https://21st.dev/mcp

Clients that cannot speak HTTP MCP can use the stdio compatibility proxy
(@21st-dev/magic), which forwards every message to the same server:

  npx -y @21st-dev/magic@latest API_KEY="<YOUR_21ST_API_KEY>"

Or run the official installer for your client:

  npx @21st-dev/cli@latest init --client cursor   # claude | codex | vscode | devin
