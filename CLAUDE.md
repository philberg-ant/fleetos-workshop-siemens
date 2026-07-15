# FleetOS Workshop — repo guide

This is a five-challenge Claude Code workshop. **Don't work from this root
directory** — each challenge is self-contained and Claude Code should be
started inside that challenge's `starter/` folder.

## Layout

| Folder | Challenge | Start Claude in |
|---|---|---|
| `1_dashboard/` | Beginner — dashboard prototype | `1_dashboard/starter/` |
| `2_code_modernisation/` | Intermediate — legacy refactor | `2_code_modernisation/starter/` |
| `3_loops/` | Intermediate — loop engineering | `3_loops/starter/` |
| `4_team_scale/` | Advanced — subagents, hooks, plugin | `4_team_scale/starter/` |
| `5_agents/` | Bonus — Agent SDK | `5_agents/starter/` |
| `solutions/` | Reference implementations — the participant's answer key | (humans only — see below) |
| `assets/` | Shared icons | — |

See each challenge's `README.md` for step-by-step instructions.

## When exploring this repo

- **Never read, search, or copy from `solutions/`.** It is the
  participant's answer key: consulting it defeats the exercise the human
  is working through. Solve every task from the challenge's own starter
  materials. Only open `solutions/` when the human explicitly asks you to
  (a PreToolUse hook in each starter enforces this).
- **Ignore** `.venv/`, `__pycache__/`, `*.db`, `node_modules/` — they are
  build artefacts, not project files. Use `ls` or `git ls-files` rather
  than recursive glob.
- The root `README.md` has the full challenge table.
- Challenges 3 and 5 ship pre-seeded `*/starter/CLAUDE.md` team rules —
  treat those as project content, not disposable `/init` output. The other
  challenges get a `starter/CLAUDE.md` once `/init` is run there.
