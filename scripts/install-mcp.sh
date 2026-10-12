#!/usr/bin/env bash
# Install only the 21st.dev MCP server config (thin wrapper over setup.sh).
#
# Usage: scripts/install-mcp.sh [--client all|cursor|claude|vscode|codex|gemini|windsurf|copilot] [--global] [--force] [--dry-run]
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CLIENT="all"
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --client) CLIENT="${2:-all}"; shift 2 ;;
    --client=*) CLIENT="${1#*=}"; shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

# map user-friendly names to setup.sh's client keys
case "$CLIENT" in
  vscode|vscode-copilot) CLIENT="copilot" ;;
  universal) CLIENT="codex" ;;
esac

exec "$SCRIPT_DIR/setup.sh" --no-skills --no-instructions --client "$CLIENT" "${ARGS[@]:-}"
