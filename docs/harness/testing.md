# Test design

Where each behavior is tested, and what is not tested. The always-on rules are in `.claude/rules/testing.md`; read this file when writing a change's test plan (`design.md`) and when reviewing tests. Adapt the layer table to the stack once it exists.

## One layer per behavior

Each behavior is tested at exactly **one** layer: the cheapest one that can show it. The change's `design.md` holds the test plan, a table of behavior → layer. A second layer for the same behavior needs a reason in that table.

| Layer | Tests | Default for |
|---|---|---|
| Unit | manuscript parsing and refusals, fit (line count, width), grid and icons, palette, PNG | anything that does not need a PPTX file (`tests/test_manuscript_*.py`, `test_fit.py`, `test_grid.py`) |
| Render | build a PPTX in memory or a temp dir and inspect it with python-pptx: shapes, sizes, fonts, colors, frame heights | everything that only the generated slide shows (`tests/test_render*.py`) |
| CLI | `build.py` / `pixel.py` as a subprocess: exit code, error message, output file | one happy path and the refusal path per script (`tests/test_*_cli.py`) |
| Compatibility | SHA-256 of each PPTX part from `examples/sample.md` | output that must not change (`tests/test_compat.py`) |
| Plugin and docs | plugin manifests, Skill and Agent files, README commands | structure and paths, not wording (`tests/test_plugin.py`, `test_skill_docs.py`, `test_readme.py`) |
| PowerPoint by eye | the PO opens the PPTX in PowerPoint | how it looks ("made by a person"), projection legibility; no automated test |

## Tests we do not write

- Verbatim copy assertions (policy text, landing-page copy, labels). Assert a key, a role or a structure instead.
- Re-assertions of CSS declarations in unit or component tests; style lint and visual tests own them.
- "The removed text is absent" tests.
- Copies of design-doc assets (mockups, sample data pasted from docs) as fixtures or snapshots.
- E2E steps re-implemented in unit or component tests.
- A test at a second layer for a behavior its layer already tests.

## Invariants over per-feature tests

A rule that holds everywhere is tested once, as an invariant every feature passes through, not written again in each change:

- **Shared after-each check.** Example: fixtures seed known personal values, and one after-each hook asserts the logs contain none of them. A new feature is covered as soon as its tests run.
- **Route × audience refusal table.** One table lists every read route and who may read it; one test walks the table, checks each refusal, and fails when the router has a read route the table does not list. A new route adds a row, not a test file.

Proving an invariant: `harness:mutation-check` ("Where it goes in a change").

## Test-to-source ratio

CI warns (step `Test-to-source ratio`) when a PR adds more than `HARNESS_TEST_RATIO_MAX` (default 3) test lines per added source line (docs, specs and config count as neither), so a test-only PR always warns. Cut the duplicated layers, or give the reason in a PR body line starting `Test ratio:`.
