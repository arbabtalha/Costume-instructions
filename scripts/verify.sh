#!/usr/bin/env bash
# Verify the Costume Webapp Kit is intact and working.
#
# Usage: scripts/verify.sh [--quiet]
# Exit code 0 = everything checks out, 1 = something is broken.
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

PASS=0
FAIL=0
WARN=0
QUIET=0
[ "${1:-}" = "--quiet" ] && QUIET=1

green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
red()   { printf '\033[0;31m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[0;33m%s\033[0m\n' "$*"; }

check() { # check <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    [ "$QUIET" -eq 1 ] || green "  PASS  $desc"
    PASS=$((PASS + 1))
  else
    red "  FAIL  $desc"
    FAIL=$((FAIL + 1))
  fi
}

soft() { # soft <description> <command...> - warnings only
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    [ "$QUIET" -eq 1 ] || green "  PASS  $desc"
    PASS=$((PASS + 1))
  else
    yellow "  WARN  $desc"
    WARN=$((WARN + 1))
  fi
}

echo "Verifying Costume Webapp Kit in $REPO_ROOT"
echo

echo "Instructions"
for f in AGENTS.md CLAUDE.md GEMINI.md README.md LICENSE \
         instructions/00-core.md instructions/10-webapp-generation.md instructions/20-ui-ux-rules.md \
         instructions/30-stack-playbooks.md instructions/40-quality-gates.md instructions/50-prompt-recipes.md \
         instructions/60-mcp-and-skill-usage.md; do
  check "$f exists" test -f "$f"
done

echo
echo "Client wiring"
check ".mcp.json exists" test -f .mcp.json
check ".cursor/rules/10-webapp-generation.mdc exists" test -f .cursor/rules/10-webapp-generation.mdc
check ".github/copilot-instructions.md exists" test -f .github/copilot-instructions.md
check ".claude-plugin/plugin.json is valid JSON" python3 -c "import json;json.load(open('.claude-plugin/plugin.json'))"
check ".claude-plugin/marketplace.json is valid JSON" python3 -c "import json;json.load(open('.claude-plugin/marketplace.json'))"
check ".mcp.json is valid JSON" python3 -c "import json;json.load(open('.mcp.json'))"
check "all mcp configs are valid JSON" bash -c 'for f in mcp/configs/*.json; do python3 -c "import json,sys;json.load(open(sys.argv[1]))" "$f" || exit 1; done'

echo
echo "Skills"
for s in ui-ux-pro-max ui-styling design design-system brand banner-design slides 21st-ui; do
  check "skills/$s/SKILL.md" test -f "skills/$s/SKILL.md"
done
check "vendored licenses present" test -f skills/LICENSE-ui-ux-pro-max.txt -a -f skills/LICENSE-21st-ui.txt

echo
echo "Design skill runtime"
if command -v python3 >/dev/null 2>&1; then
  check "search.py --help runs" python3 skills/ui-ux-pro-max/scripts/search.py --help
  check "design-system query returns output" bash -c 'python3 skills/ui-ux-pro-max/scripts/search.py "saas dashboard" --design-system -p "Verify" | grep -q "TARGET"'
  check "domain query returns output" bash -c 'python3 skills/ui-ux-pro-max/scripts/search.py "empty state" --domain ux | grep -q "Result"'
  check "stack query returns output" bash -c 'python3 skills/ui-ux-pro-max/scripts/search.py "streaming suspense" --stack nextjs | grep -q "Result"'
  check "skill data files present" bash -c 'test -f skills/ui-ux-pro-max/data/styles.csv -a -f skills/ui-ux-pro-max/data/colors.csv -a -f skills/ui-ux-pro-max/data/stacks/nextjs.csv'
else
  yellow "  WARN  python3 not found: skill runtime checks skipped"
  WARN=$((WARN + 1))
fi

echo
echo "Agents and commands"
for a in webapp-architect ui-ux-designer frontend-implementer qa-reviewer; do
  check "agents/$a.md has frontmatter" bash -c "head -1 agents/$a.md | grep -q -- '---' && grep -q '^name:' agents/$a.md"
done
for c in webapp ui review ship mcp; do
  check "commands/$c.md has frontmatter" bash -c "head -1 commands/$c.md | grep -q -- '---' && grep -q '^description:' commands/$c.md"
done

echo
echo "Scripts"
check "setup.sh is executable" test -x scripts/setup.sh
check "setup.sh --help works" bash scripts/setup.sh --help
check "install-mcp.sh is executable" test -x scripts/install-mcp.sh
check "setup.sh dry run succeeds (temp dir)" bash -c 'tmp=$(mktemp -d) && scripts/setup.sh --target "$tmp" --client claude --dry-run >/dev/null && rm -rf "$tmp"'

echo
echo "Hygiene"
soft "no node_modules committed" bash -c '! git ls-files | grep -q "^node_modules/"'
soft "no .env committed" bash -c '! git ls-files | grep -qE "(^|/)\.env$"'
soft "no __pycache__ in skills" bash -c '! find skills -name "__pycache__" -type d | grep -q .'
soft "no API keys hardcoded" bash -c '! grep -rIn --exclude-dir=.git --exclude-dir=skills -E "(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})" . | grep -q .'

echo
printf 'PASS %s   FAIL %s   WARN %s\n' "$PASS" "$FAIL" "$WARN"
if [ "$FAIL" -gt 0 ]; then
  red "Verification failed"
  exit 1
fi
green "All checks passed"
