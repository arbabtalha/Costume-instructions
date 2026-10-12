#!/usr/bin/env bash
# Refresh the vendored skills from upstream, or upgrade the kit's own install.
#
# Usage:
#   scripts/vendor-update.sh                 # re-vendor skills from upstream repos
#   scripts/vendor-update.sh --check         # report upstream versions only
#
# Vendored content:
#   skills/*              <- nextlevelbuilder/ui-ux-pro-max-skill (.claude/skills)
#   skills/21st-ui        <- 21st-dev/magic-mcp (skills/21st-ui)
#
# The kit prefers vendored copies so installs work offline and pinned. Rerun this
# script when upstream ships new styles, palettes, or stacks.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

UUX_REPO="https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git"
MAGIC_REPO="https://github.com/21st-dev/magic-mcp.git"

log() { printf '\033[0;34m==> %s\033[0m\n' "$*"; }

log "Cloning upstream repos (shallow)"
git clone --depth 1 "$UUX_REPO" "$TMP_DIR/ui-ux-pro-max-skill" >/dev/null 2>&1
git clone --depth 1 "$MAGIC_REPO" "$TMP_DIR/magic-mcp" >/dev/null 2>&1

UUX_VERSION="$(jq -r '.version' "$TMP_DIR/ui-ux-pro-max-skill/.claude-plugin/plugin.json" 2>/dev/null || echo unknown)"
MAGIC_VERSION="$(jq -r '.version' "$TMP_DIR/magic-mcp/.claude-plugin/plugin.json" 2>/dev/null || echo unknown)"
UUX_COMMIT="$(git -C "$TMP_DIR/ui-ux-pro-max-skill" rev-parse --short HEAD)"
MAGIC_COMMIT="$(git -C "$TMP_DIR/magic-mcp" rev-parse --short HEAD)"

log "Upstream: ui-ux-pro-max-skill v$UUX_VERSION ($UUX_COMMIT), magic-mcp v$MAGIC_VERSION ($MAGIC_COMMIT)"

if [ "$CHECK_ONLY" -eq 1 ]; then
  echo
  echo "Vendored versions recorded in skills/UPSTREAM.md:"
  sed -n '1,20p' "$REPO_ROOT/skills/UPSTREAM.md" 2>/dev/null || echo "  (no UPSTREAM.md yet)"
  exit 0
fi

log "Syncing skills/"
rm -rf "$REPO_ROOT/skills/design" "$REPO_ROOT/skills/design-system" "$REPO_ROOT/skills/brand" \
       "$REPO_ROOT/skills/banner-design" "$REPO_ROOT/skills/slides" "$REPO_ROOT/skills/ui-styling" \
       "$REPO_ROOT/skills/ui-ux-pro-max" "$REPO_ROOT/skills/21st-ui"
cp -R "$TMP_DIR/ui-ux-pro-max-skill/.claude/skills/." "$REPO_ROOT/skills/"
mkdir -p "$REPO_ROOT/skills/21st-ui"
cp "$TMP_DIR/magic-mcp/skills/21st-ui/SKILL.md" "$REPO_ROOT/skills/21st-ui/SKILL.md"
cp "$TMP_DIR/ui-ux-pro-max-skill/LICENSE" "$REPO_ROOT/skills/LICENSE-ui-ux-pro-max.txt"
cp "$TMP_DIR/magic-mcp/LICENSE" "$REPO_ROOT/skills/LICENSE-21st-ui.txt"
find "$REPO_ROOT/skills" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$REPO_ROOT/skills" -name '*.pyc' -delete 2>/dev/null || true

cat > "$REPO_ROOT/skills/UPSTREAM.md" <<EOF
# Vendored sources

Regenerate with \`scripts/vendor-update.sh\`. Last sync: $(date -u +%Y-%m-%dT%H:%M:%SZ)

| Path | Upstream | Version | Commit |
|---|---|---|---|
| \`skills/{ui-ux-pro-max,ui-styling,design,design-system,brand,banner-design,slides}/\` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | v$UUX_VERSION | \`$UUX_COMMIT\` |
| \`skills/21st-ui/\` | https://github.com/21st-dev/magic-mcp | v$MAGIC_VERSION | \`$MAGIC_COMMIT\` |

Licenses: MIT (UI/UX Pro Max, \`LICENSE-ui-ux-pro-max.txt\`) and ISC (21st.dev, \`LICENSE-21st-ui.txt\`).

Prefer the installed copies inside a project (a single skill, updated by its own CLI)
over this vendored snapshot when you want the newest versions:

\`\`\`bash
npx ui-ux-pro-max-cli@latest init --ai claude
npx @21st-dev/cli@latest init --client cursor
\`\`\`
EOF

log "Done. Vendored skill trees:"
for d in "$REPO_ROOT"/skills/*/; do
  [ -f "$d/SKILL.md" ] || continue
  printf '  %-22s %s files\n' "$(basename "$d")" "$(find "$d" -type f | wc -l | tr -d ' ')"
done
echo
log "Next: run scripts/verify.sh, then commit the refreshed skills."
