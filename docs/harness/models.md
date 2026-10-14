# Models and effort

Which model and effort each role uses. This is the only place that names them: `CLAUDE.md`, `AGENTS.md`, `.claude/rules/` and the skills refer here instead of writing a model name.

| Role | Model | Effort | Why |
|---|---|---|---|
| Decision: the design session, including writing `design.md` and `tasks.md` as the plan | Opus | high | A wrong decision costs every later step. The session that decides also breaks the work into tasks, so the split is written once. |
| Final review of the whole branch | Opus | high | It catches what the batched reviews missed, and it is the last check before the PR. |
| Implementation | Sonnet | medium | The task is already specified in `tasks.md`; the work is writing the tests and the code the task names. |
| Intermediate review | Sonnet | medium | It checks a few tasks against the parts of the change they name; the final review covers the rest. |
| Controller: the `harness:execute` session | Sonnet | medium | It dispatches, judges replies against the change files and records; the decisions that need the top model sit in the design session and the final review. |

No role uses Haiku.

## How the model and effort are set

- The `model` of an Agent call is set per role on every dispatch. An omitted `model` inherits the session's, so always pass it.
- Effort is not an Agent parameter. It comes from the session or from the agent's frontmatter. The `harness:implementer` frontmatter is `sonnet` / `medium`. An intermediate review dispatches `harness:reviewer-intermediate`, whose frontmatter is `sonnet` / `medium` (same instructions as `harness:reviewer`, generated from it). The final review dispatches `harness:reviewer`, whose frontmatter is `opus` / `high`.
- The controller is the session itself: start the `harness:execute` session on Sonnet with effort medium (`/model`). The design session stays on the top model.

## Copilot CLI

| Role | Model | Effort |
|---|---|---|
| Decision: the design session | claude-opus-5.5 | high |
| Final review of the whole branch | claude-opus-5.5 | high |
| Implementation | claude-sonnet-5.5 | medium |
| Intermediate review | claude-sonnet-5.5 | medium |

Dispatch with `task`, passing `model` and `reasoning_effort` from this table; without `model` the dispatch fails (the agent definitions' `model: sonnet` and `model: opus` are not Copilot ids). The intermediate review uses `harness:reviewer-intermediate` with the fast model, the final review `harness:reviewer`. If `task` answers that a model is not available, use `gpt-5.6-luna`, or another id from the list in that error.
