#!/usr/bin/env bash
# Costume Webapp Kit installer
#
# Applies the instruction set, the design skill(s), and the 21st.dev MCP wiring
# into any project directory.
#
# Usage: scripts/setup.sh [options]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET=""
CLIENTS=""
INSTALL_SKILLS=1
INSTALL_INSTRUCTIONS=1
INSTALL_MCP=1
FORCE=0
DRY_RUN=0
UPSTREAM=0
GLOBAL=0

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; DIM='\033[2m'; NC='\033[0m'
log()  { printf "${BLUE}==>${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}  +${NC} %s\n" "$*"; }
skip() { printf "${YELLOW}  ~${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}!!${NC} %s\n" "$*"; }
warn_err() { printf "${YELLOW}!!${NC} %s\n" "$*" >&2; }
die()  { printf "${RED}xx${NC} %s\n" "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Costume Webapp Kit installer

Usage: scripts/setup.sh [options]

Options:
  --target DIR          Project to install into (default: current directory)
  --client LIST         Comma-separated: all, claude, cursor, copilot, codex,
                        gemini, windsurf, universal (default: auto-detect)
  --global              Install skills and MCP config into $HOME instead of the project
  --no-skills           Skip the design skills
  --no-instructions     Skip AGENTS.md and instruction files
  --no-mcp              Skip the 21st.dev MCP config
  --upstream            Pull skills from the upstream npm CLI instead of the
                        vendored copies in this repo
  --force               Overwrite files that already exist
  --dry-run             Print what would happen, change nothing
  -h, --help            This help

Examples:
  scripts/setup.sh                                   # auto-detect, install everything
  scripts/setup.sh --client all --force              # all clients, overwrite
  scripts/setup.sh --target ~/code/my-app            # install into another project
  scripts/setup.sh --no-mcp --client claude          # instructions + skills only

After running, export your 21st.dev key and restart the editor:
  export API_KEY_21ST="your-key"   # free key: https://21st.dev/mcp
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --target=*) TARGET="${1#*=}"; shift ;;
    --client) CLIENTS="${2:-}"; shift 2 ;;
    --client=*) CLIENTS="${1#*=}"; shift ;;
    --global|-g) GLOBAL=1; shift ;;
    --no-skills) INSTALL_SKILLS=0; shift ;;
    --no-instructions) INSTALL_INSTRUCTIONS=0; shift ;;
    --no-mcp) INSTALL_MCP=0; shift ;;
    --upstream) UPSTREAM=1; shift ;;
    --force|-f) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1 (try --help)" ;;
  esac
done

[ -n "$TARGET" ] || TARGET="$(pwd)"
[ -d "$TARGET" ] || die "Target directory does not exist: $TARGET"
TARGET="$(cd "$TARGET" && pwd)"

if [ "$GLOBAL" -eq 1 ]; then
  ROOT_DIR="$HOME"
else
  ROOT_DIR="$TARGET"
fi

# ---------------------------------------------------------------- clients ---
detect_clients() {
  local found=""
  [ -d "$TARGET/.claude" ]   && found="$found claude"
  [ -d "$TARGET/.cursor" ]   && found="$found cursor"
  [ -d "$TARGET/.windsurf" ] && found="$found windsurf"
  [ -d "$TARGET/.gemini" ]   && found="$found gemini"
  [ -d "$TARGET/.agents" ]   && found="$found universal"
  [ -d "$TARGET/.codex" ]    && found="$found codex"
  [ -d "$TARGET/.github" ]   && found="$found copilot"
  if [ -z "$found" ]; then
    found=" claude universal copilot"
    warn_err "No client marker found in $TARGET. Installing for: claude, universal (AGENTS.md + .agents/skills), copilot"
  fi
  echo $found
}

normalize_clients() {
  local list="$1" out=""
  case "$list" in
    all) out="claude cursor copilot codex gemini windsurf universal" ;;
    *)   out="$(echo "$list" | tr ',' ' ')" ;;
  esac
  local c
  for c in $out; do
    case "$c" in
      claude|cursor|copilot|codex|gemini|windsurf|universal) : ;;
      *) die "Unknown client: $c (valid: all, claude, cursor, copilot, codex, gemini, windsurf, universal)" ;;
    esac
  done
  echo $out
}

if [ -z "$CLIENTS" ]; then
  CLIENTS="$(detect_clients)"
else
  CLIENTS="$(normalize_clients "$CLIENTS")"
fi

# skills target dir per client (mirrors the upstream UI/UX Pro Max installer)
skills_dir_for() {
  case "$1" in
    claude)    echo ".claude/skills" ;;
    cursor)    echo ".cursor/skills" ;;
    copilot)   echo ".github/prompts" ;;
    codex)     echo ".agents/skills" ;;
    universal) echo ".agents/skills" ;;
    gemini)    echo ".gemini/skills" ;;
    windsurf)  echo ".windsurf/skills" ;;
    *) die "No skills dir for client: $1" ;;
  esac
}

log "Costume Webapp Kit"
printf "${DIM}  repo:   %s${NC}\n" "$REPO_ROOT"
printf "${DIM}  target: %s${NC}\n" "$ROOT_DIR"
printf "${DIM}  clients:%s${NC}\n" "$CLIENTS"
[ "$DRY_RUN" -eq 1 ] && warn "Dry run: nothing will be written"

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$ROOT_DIR/.costume-backup/$STAMP"

backup() {
  local f="$1"
  [ -e "$f" ] || return 0
  [ "$DRY_RUN" -eq 1 ] && return 0
  mkdir -p "$BACKUP_DIR"
  local dest="$BACKUP_DIR/$(echo "${f#"$ROOT_DIR"/}" | tr '/' '_')"
  cp -R "$f" "$dest"
}

copy_file() {
  local src="$1" dest="$2"
  if [ -e "$dest" ] && [ "$FORCE" -eq 0 ]; then
    if cmp -s "$src" "$dest" 2>/dev/null; then
      skip "up to date: ${dest#"$ROOT_DIR"/}"
    else
      skip "exists, kept: ${dest#"$ROOT_DIR"/}  (use --force to overwrite)"
    fi
    return 0
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "would write: ${dest#"$ROOT_DIR"/}"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  ok "${dest#"$ROOT_DIR"/}"
}

copy_tree() {
  local src="$1" dest="$2"
  if [ ! -d "$src" ]; then
    warn "missing source: $src"
    return 0
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "would install tree: ${dest#"$ROOT_DIR"/} ($(find "$src" -type f | wc -l | tr -d ' ') files)"
    return 0
  fi
  mkdir -p "$dest"
  # copy contents, skipping caches that never belong in a project
  ( cd "$src" && find . -type d -name '__pycache__' -prune -o -type f -print ) | while IFS= read -r rel; do
    mkdir -p "$dest/$(dirname "$rel")"
    cp "$src/$rel" "$dest/$rel"
  done
  ok "${dest#"$ROOT_DIR"/} ($(find "$dest" -type f | wc -l | tr -d ' ') files)"
}

# --------------------------------------------------------------- skill copy ---
install_skills_vendored() {
  local client="$1" sdir skill count=0
  sdir="$(skills_dir_for "$client")"
  for skill in "$REPO_ROOT"/skills/*/; do
    [ -f "$skill/SKILL.md" ] || continue
    copy_tree "$skill" "$ROOT_DIR/$sdir/$(basename "$skill")"
    count=$((count + 1))
  done
  [ "$count" -gt 0 ] || warn "no vendored skills found in $REPO_ROOT/skills"
}

install_skills_upstream() {
  local client="$1" key="$1"
  case "$client" in
    universal) key="universal" ;;
    codex)     key="codex" ;;
  esac
  log "Installing skills from upstream CLI for: $client"
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "would run: npx -y ui-ux-pro-max-cli@latest init --ai $key --force (cwd: $ROOT_DIR)"
    return 0
  fi
  if ! command -v npx >/dev/null 2>&1; then
    warn "npx not found, falling back to vendored skills"
    install_skills_vendored "$client"
    return 0
  fi
  ( cd "$ROOT_DIR" && npx -y ui-ux-pro-max-cli@latest init --ai "$key" --force ) \
    || { warn "upstream install failed, falling back to vendored skills"; install_skills_vendored "$client"; }
}

# ------------------------------------------------------------- json merging ---
merge_json() {
  # merge_json <file> <python-expr-on-data> ... we use a small python program
  local dest="$1" payload="$2" root_key="$3"
  local py=""
  command -v python3 >/dev/null 2>&1 && py="python3"
  [ -z "$py" ] && command -v python >/dev/null 2>&1 && py="python"
  if [ -z "$py" ]; then
    warn "python not found: writing config as-is (existing settings in ${dest#"$ROOT_DIR"/} are untouched)"
    copy_file "$payload" "$dest"
    return 0
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "would merge 21st server into ${dest#"$ROOT_DIR"/}"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  [ -e "$dest" ] && backup "$dest"
  COSTUME_DEST="$dest" COSTUME_PAYLOAD="$payload" COSTUME_ROOTKEY="$root_key" "$py" - <<'PY'
import json, os, sys

dest = os.environ["COSTUME_DEST"]
payload = os.environ["COSTUME_PAYLOAD"]
root_key = os.environ["COSTUME_ROOTKEY"]

with open(payload) as fh:
    incoming = json.load(fh)

existing = {}
if os.path.exists(dest) and os.path.getsize(dest) > 0:
    try:
        with open(dest) as fh:
            existing = json.load(fh)
    except json.JSONDecodeError:
        print("  ! existing file is not valid JSON, leaving it alone: %s" % dest)
        sys.exit(0)

server_key = "21st"
if root_key == "servers":          # VS Code
    new_servers = incoming.get("servers", {})
else:
    new_servers = incoming.get("mcpServers", {})

bucket = existing.setdefault(root_key, {})
bucket.update(new_servers)

with open(dest, "w") as fh:
    json.dump(existing, fh, indent=2)
    fh.write("\n")

print("  + merged %s into %s" % (", ".join(new_servers.keys()) or server_key, dest))
PY
}

# --------------------------------------------------------- managed md block ---
write_managed_block() {
  # write_managed_block <file> <block-file>
  local dest="$1" block_file="$2"
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "would update managed block in ${dest#"$ROOT_DIR"/}"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  [ -e "$dest" ] && backup "$dest"
  COSTUME_DEST="$dest" COSTUME_BLOCK="$block_file" python3 - <<'PY' 2>/dev/null || \
  { warn "python3 unavailable, writing block directly"; { printf '\n'; cat "$block_file"; } >> "$dest"; }
import os

dest = os.environ["COSTUME_DEST"]
block_file = os.environ["COSTUME_BLOCK"]

with open(block_file) as fh:
    block = fh.read().rstrip() + "\n"

start, end = "<!-- costume:start -->", "<!-- costume:end -->"
wrapped = "%s\n%s%s\n" % (start, block, end)

existing = ""
if os.path.exists(dest):
    with open(dest) as fh:
        existing = fh.read()

if start in existing and end in existing:
    head, rest = existing.split(start, 1)
    _, tail = rest.split(end, 1)
    new = head.rstrip() + "\n\n" + wrapped + tail
elif existing.strip():
    new = existing.rstrip() + "\n\n" + wrapped + "\n"
else:
    new = wrapped

with open(dest, "w") as fh:
    fh.write(new)
print("  + managed block updated: %s" % dest)
PY
}

AGENTS_BLOCK="$(mktemp)"
cat > "$AGENTS_BLOCK" <<'EOF'
# Costume Webapp Kit

This project uses the Costume Webapp Kit: an instruction set, a local UI/UX design
intelligence skill, and the 21st.dev MCP server.

Rules, workflow, and file routing: `.costume/instructions/00-core.md` and
`.costume/instructions/10-webapp-generation.md`. Read those before building UI.

Non-negotiables: tokens before components; run the design skill before designing;
all loading/empty/error states; WCAG 2.2 AA; responsive from 320px up; real content;
typecheck + lint + build before claiming done; honest report including gaps.

Design skill (installed for your client under `skills/ui-ux-pro-max`):

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<product> <industry> <keywords>" --design-system -p "Project"
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<query>" --domain ux
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<query>" --stack nextjs
```

21st.dev MCP: HTTP server at https://21st.dev/api/mcp (header `x-api-key`, env
`API_KEY_21ST`). Tools: search, get_component, get_inspiration, search_logo, and
`generate` when hosted AI is enabled. Prefer a real catalog component over
hand-written generic UI, then adapt it to project tokens. Never claim an install
that did not return code. Setup: https://21st.dev/mcp, notes: `.costume/mcp.md`.
EOF

# ---------------------------------------------------------------- 1. skills ---
if [ "$INSTALL_SKILLS" -eq 1 ]; then
  log "1/3 Design skills (UI/UX Pro Max + design, brand, slides)"
  for client in $CLIENTS; do
    label="$client"
    [ "$GLOBAL" -eq 1 ] && label="$client (global)"
    if [ "$UPSTREAM" -eq 1 ]; then
      install_skills_upstream "$client"
    else
      install_skills_vendored "$client"
      printf "${DIM}     -> %s/%s${NC}\n" "$ROOT_DIR" "$(skills_dir_for "$client")"
    fi
  done
else
  log "1/3 Design skills: skipped"
fi

# ---------------------------------------------------------- 2. instructions ---
if [ "$INSTALL_INSTRUCTIONS" -eq 1 ]; then
  log "2/3 Instructions"
  for f in "$REPO_ROOT"/instructions/*.md; do
    [ -f "$f" ] || continue
    copy_file "$f" "$ROOT_DIR/.costume/instructions/$(basename "$f")"
  done
  copy_file "$REPO_ROOT/mcp/21st-mcp.md" "$ROOT_DIR/.costume/mcp.md"
  copy_file "$REPO_ROOT/skills/README.md" "$ROOT_DIR/.costume/skills.md"

  # AGENTS.md is the cross-tool standard (Codex, Cursor, Zed, Amp, Gemini CLI,
  # Claude Code via import). Always write it, whoever the detected client is.
  write_managed_block "$ROOT_DIR/AGENTS.md" "$AGENTS_BLOCK"

  for client in $CLIENTS; do
    case "$client" in
      claude)
        write_managed_block "$ROOT_DIR/CLAUDE.md" "$AGENTS_BLOCK" ;;
      cursor)
        copy_file "$REPO_ROOT/.cursor/rules/00-costume-core.mdc" "$ROOT_DIR/.cursor/rules/00-costume-core.mdc"
        copy_file "$REPO_ROOT/.cursor/rules/10-webapp-generation.mdc" "$ROOT_DIR/.cursor/rules/10-webapp-generation.mdc"
        copy_file "$REPO_ROOT/.cursor/rules/20-ui-ux.mdc" "$ROOT_DIR/.cursor/rules/20-ui-ux.mdc" ;;
      copilot)
        write_managed_block "$ROOT_DIR/.github/copilot-instructions.md" "$AGENTS_BLOCK" ;;
      windsurf)
        write_managed_block "$ROOT_DIR/.windsurf/rules/costume.md" "$AGENTS_BLOCK" ;;
      gemini)
        write_managed_block "$ROOT_DIR/GEMINI.md" "$AGENTS_BLOCK" ;;
      codex|universal)
        : ;;  # AGENTS.md already written above
    esac
  done
  rm -f "$AGENTS_BLOCK"
else
  log "2/3 Instructions: skipped"
fi

# ----------------------------------------------------------------- 3. MCP ---
if [ "$INSTALL_MCP" -eq 1 ]; then
  log "3/3 21st.dev MCP"
  for client in $CLIENTS; do
    case "$client" in
      claude)
        merge_json "$ROOT_DIR/.mcp.json" "$REPO_ROOT/mcp/configs/claude-code.json" "mcpServers" ;;
      cursor)
        merge_json "$ROOT_DIR/.cursor/mcp.json" "$REPO_ROOT/mcp/configs/cursor.json" "mcpServers" ;;
      copilot)
        merge_json "$ROOT_DIR/.vscode/mcp.json" "$REPO_ROOT/mcp/configs/vscode.json" "servers" ;;
      windsurf)
        if [ "$GLOBAL" -eq 1 ]; then
          merge_json "$HOME/.codeium/windsurf/mcp_config.json" "$REPO_ROOT/mcp/configs/windsurf.json" "mcpServers"
        else
          skip "windsurf MCP config is global: run with --global, or copy mcp/configs/windsurf.json to ~/.codeium/windsurf/mcp_config.json"
        fi ;;
      gemini)
        if [ "$GLOBAL" -eq 1 ]; then
          merge_json "$HOME/.gemini/settings.json" "$REPO_ROOT/mcp/configs/gemini.json" "mcpServers"
        else
          skip "gemini MCP config is global: run with --global, or merge mcp/configs/gemini.json into ~/.gemini/settings.json"
        fi ;;
      codex|universal)
        if [ "$GLOBAL" -eq 1 ]; then
          if [ -e "$HOME/.codex/config.toml" ]; then
            skip "codex config exists: append mcp/configs/codex.toml to ~/.codex/config.toml (not auto-merged)"
          else
            copy_file "$REPO_ROOT/mcp/configs/codex.toml" "$HOME/.codex/config.toml"
          fi
        else
          skip "codex MCP config is global: run with --global, or append mcp/configs/codex.toml to ~/.codex/config.toml"
        fi ;;
    esac
  done
else
  log "3/3 21st.dev MCP: skipped"
fi

# -------------------------------------------------------------- manifest ---
if [ "$DRY_RUN" -eq 0 ]; then
  {
    echo "installed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "client=$(echo $CLIENTS | tr ' ' ',')"
    echo "source=$REPO_ROOT"
    echo "skills=$INSTALL_SKILLS instructions=$INSTALL_INSTRUCTIONS mcp=$INSTALL_MCP upstream=$UPSTREAM"
  } > "$ROOT_DIR/.costume/manifest.txt" 2>/dev/null || true
fi

printf "\n"
log "Done"
cat <<EOF

Next steps
  1. Export your key (free, instant):  export API_KEY_21ST="your-key"   ->  https://21st.dev/mcp
     Persist it in ~/.zshrc or ~/.bashrc, then restart your editor so the MCP server connects.
  2. Verify the MCP:  /mcp     (Claude Code)  or  run  /mcp  command in this kit's commands.
  3. Smoke test the skill:
     python3 $(skills_dir_for "$(echo $CLIENTS | awk '{print $1}')")/ui-ux-pro-max/scripts/search.py "saas dashboard" --design-system -p "Test"
  4. Read the rules your agent now follows: .costume/instructions/10-webapp-generation.md

Files written are listed above. Backups of anything replaced: ${BACKUP_DIR#"$ROOT_DIR"/}
Uninstall by deleting .costume/, the installed skills dirs, and the managed blocks marked "costume".
EOF
