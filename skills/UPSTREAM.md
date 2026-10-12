# Vendored sources

Regenerate with `scripts/vendor-update.sh`. Last sync: 2026-10-12

| Path | Upstream | Version | Commit |
|---|---|---|---|
| `skills/{ui-ux-pro-max,ui-styling,design,design-system,brand,banner-design,slides}/` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | v2.13.0 | `026b6e1` |
| `skills/21st-ui/` | https://github.com/21st-dev/magic-mcp | v1.0.1 | `6b5299e` |

Licenses: MIT (UI/UX Pro Max, `LICENSE-ui-ux-pro-max.txt`) and ISC (21st.dev, `LICENSE-21st-ui.txt`).

Prefer the installed copies inside a project (a single skill, updated by its own CLI)
over this vendored snapshot when you want the newest versions:

```bash
npx ui-ux-pro-max-cli@latest init --ai claude
npx @21st-dev/cli@latest init --client cursor
```
