Issue: #15

# Tasks

作業場所: worktree `.claude/worktrees/extend-table-statement-section`、ブランチ `feature/extend-table-statement-section`。テスト `uv run pytest`、lint `uv run ruff check . && uv run ruff format --check .`。生成器のパスは `plugin/skills/slide/scripts/slidekit/`（以下 `slidekit/`）。`add-flow-diagram` のマージとアーカイブの後に始める（D1）。

## 1. 前提

- [x] 1.1 ブランチを最新の main に載せ直し、delta を main の spec と照らす
  - Refs: D1、Requirement「Skill の内容」
  - Files: `openspec/changes/extend-table-statement-section/specs/`（違いがあったときだけ）
  - Verify: `git log main --oneline` に `add-flow-diagram` のアーカイブのコミットがあり、`openspec list --specs` に `flow-diagram` がある。`openspec show slide-plugin --type spec` の「Skill の内容」と、この変更の delta の MODIFIED の文が、7 種・改行・補足・列の強調の部分を除いて同じ（違えば `/opsx:update` で合わせる）。`openspec validate extend-table-statement-section --strict` が通る。`uv run pytest` が緑
  - Review: batch A / Risk: none

## 2. 原稿の解析と判定

- [ ] 2.1 改行 `<br>` を解析し、行数の数え方を加える
  - Refs: Requirement「改行」「未対応の書式の拒否」、D2、D3
  - Files: `slidekit/fit.py`、`slidekit/manuscript.py`、`tests/test_fit.py`、`tests/test_manuscript_breaks.py`（新規）
  - Interface: 改行は `Run.text` の中の `\n`。`fit.py` の、`\n` で分けた部分の行数を足す関数（名前は実装で決め、2.2・2.4・3.1 が使う）
  - Test first: `tests/test_fit.py` で、`\n` を含む文の行数が部分ごとの行数の合計になること。`tests/test_manuscript_breaks.py` で、一言と表のセル（見出し行と本文）の `<br>` が `\n` になること。見出し・箇条書き・表紙・図の説明文・左右 2 列・添え訳の `<br>` の拒否（行番号）。`<br/>`・`<BR>` の拒否。先頭・末尾・続けて 2 つの `<br>` の拒否。`<br>` で 2 行にしたセルが、行数の判定で 2 行と数えられること。これらを確かめて赤になる
  - Review: batch A / Risk: none

- [ ] 2.2 一言の補足を解析し、高さを判定する
  - Refs: Requirement「一言レイアウト」「添え訳の書式」、D2、D4、D9
  - Files: `slidekit/fit.py`、`slidekit/manuscript.py`、`tests/test_manuscript_statement.py`（新規）、`tests/test_manuscript_basic.py`
  - Interface: `Statement.notes`、`Statement.note_glosses`、`fit.PT_STATEMENT_NOTE`、`fit.STATEMENT_NOTE_GAP_PT`、`fit.STATEMENT_BOX_H`
  - Test first: 次を確かめて赤になる。一言と補足 1 行・2 行が `notes` に入り、強調が `Run` になること。補足 3 行で 3 つ目の補足の行の拒否（`test_statement_with_two_lines_and_no_heading_is_rejected` を、この条件に書き換える。D9）。24pt で 3 行になる補足の拒否。補足の添え訳が `note_glosses` に入り、14pt で 3 行のものが拒否されること。一言 3 行・補足 2 行ずつ・すべてに 2 行の添え訳で、`STATEMENT_BOX_H` を最初に超えた段落の行の拒否。補足に箇条書きの行を書いたときの拒否
  - Review: batch A / Risk: none

- [ ] 2.3 中扉を解析する
  - Refs: Requirement「中扉レイアウト」「原稿の区切りと表紙」「添え訳の書式」、D2、D5、D9
  - Files: `slidekit/manuscript.py`、`tests/test_manuscript_section.py`（新規）、`tests/test_manuscript_basic.py`
  - Interface: `manuscript.Section(title: str, title_gloss: str | None = None)`
  - Test first: 次を確かめて赤になる。2 枚目以降の `# 補足資料` だけのスライドが `Section` になること、その添え訳が `title_gloss` に入ること。`# ` とほかの行が混ざったスライドの、`# ` の行での拒否（`test_h1_outside_the_cover_is_rejected` を、この条件に書き換える。D9）。`# ` の 2 行の拒否。空のタイトルと、40pt で 3 行になるタイトルの拒否。表紙の判定が変わらないこと（既存のテストが緑のまま）
  - Review: batch A / Risk: none

- [ ] 2.4 表を 18pt で入らなければ 16pt で判定し直す
  - Refs: Requirement「表の文字の大きさ」「添え訳の文字」、D2、D6
  - Files: `slidekit/fit.py`、`slidekit/manuscript.py`、`tests/test_manuscript_table_size.py`（新規）
  - Interface: `Table.pt`、`fit.PT_CELL_SMALL`
  - Test first: 次を確かめて赤になる（セルの行数は `fit.line_count` で数えて原稿を作る）。18pt で収まる表は `pt == 18`。18pt で 3 行のセルがあり 16pt で 2 行になる 4 列の表は `pt == 16`。18pt で高さを超え 16pt で収まる表は `pt == 16`。16pt でも 3 行のセルの表は、そのセルの行の行番号と「16pt」を含む理由で拒否され、18pt の理由は出ないこと。16pt の表のセルの添え訳が 10pt で行数を判定されること。列の数の違いなど、大きさによらない違反が 1 回だけ出ること
  - Review: batch A / Risk: none

- [ ] 2.5 表の列の強調を解析する
  - Refs: Requirement「表の列の強調」、D2、D7
  - Files: `slidekit/manuscript.py`、`tests/test_manuscript_table_size.py`
  - Interface: `Table.emphasis_col`
  - Test first: 次を確かめて赤になる。`| 観点 | A 案 | B 案 | **C 案** |` で `emphasis_col == 3`。強調のない表は `None`。`**C** 案` の見出し行の拒否と理由。列の強調があり本文のセルにも `**` があると、本文の行で拒否されること。2 つの見出しのセルの強調で、2 か所目の拒否
  - Review: batch B / Risk: none

## 3. 描画

- [ ] 3.1 改行・一言の補足・中扉を描く
  - Refs: Requirement「改行」「一言レイアウト」「中扉レイアウト」「添え訳の文字」「添え訳の配置」、D3、D4、D5
  - Files: `slidekit/render.py`、`tests/test_render_extensions.py`（新規）
  - Test first: `tests/test_render_extensions.py` が、できた PPTX を python-pptx で読んで次を確かめて赤になる（位置の差は 2 EMU まで）。`<br>` を書いた一言と表のセルの段落に `a:br` が 1 つあり、前後の文字が分かれていること。補足の段落が一言の段落（と添え訳）の後にあり、24pt の `6B6B6B`、前の間隔 12pt で、その添え訳が 14pt の `767676` であること。中扉のタイトルがタイトルのプレースホルダーで、位置と大きさが表紙のタイトルと同じで、ページ番号があること。中扉のタイトルの添え訳が 24pt で、その枠の下端が 3.8 インチであること。補足のない一言の枠と段落が今と同じであること（`tests/test_compat.py` も緑のまま）
  - Review: batch B / Risk: ui

- [ ] 3.2 16pt の表と列の強調の線を描く
  - Refs: Requirement「表の文字の大きさ」「表の列の強調」「表レイアウト」「添え訳の文字」、D6、D7
  - Files: `slidekit/render.py`、`tests/test_render_extensions.py`
  - Test first: 次を確かめて赤になる。16pt の表のすべてのセルの文字が 16pt で、セルの添え訳が 10pt であること。列を強調した表で、その列の全セルの `lnL`・`lnR`、見出しのセルの `lnT`、最後の行のセルの `lnB`、隣の列の向かい合う辺が `B23A2E` の 1.5pt（19050 EMU）の実線であること。見出し行の下の線は灰色のままで、ほかの列の線と塗りは今と同じであること。見出しの文字が `B23A2E` であること
  - Review: batch B / Risk: ui

## 4. 見本・文書・版

- [ ] 4.1 見本の原稿に、表・一言・中扉のスライドを足す
  - Refs: D8、Requirement「中扉レイアウト」「表の列の強調」「表の文字の大きさ」「一言レイアウト」
  - Files: `examples/design-review.md`、`tests/test_examples.py`
  - Test first: `tests/test_examples.py` が次を確かめて赤になる。`examples/design-review.md` が `build.py` で終了コード 0 になること。補足のある一言、`pt == 16` で `emphasis_col` のある表、`Section` を 1 つずつ含むこと。`Section` の後にスライドがあること
  - Review: batch B / Risk: ui

- [ ] 4.2 Skill の文書を 7 種のレイアウトと、改行・補足・列の強調に直す
  - Refs: Requirement「Skill の内容」、D8
  - Files: `plugin/skills/slide/references/format.md`、`plugin/skills/slide/SKILL.md`、`plugin/skills/slide/references/writing.md`、`tests/test_skill_docs.py`
  - Test first: `tests/test_skill_docs.py` が次を確かめて赤になる。`SKILL.md` と `format.md` の原稿の例から、7 種（`Section` を含む）のスライドがすべてできること（`SIX` を 7 種に）。`format.md` の原稿の例に、補足のある一言、`<br>`、列の強調があり、生成できること（既存の生成のテスト）。`writing.md` に `<br>` の入れ方の規則があること（鍵となる語で確かめ、文言は写さない）
  - Review: batch B / Risk: none

- [ ] 4.3 版を 0.4.0 に上げ、すべてのテストと lint を通す
  - Refs: D8、D9
  - Files: `plugin/.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`tests/test_plugin.py`
  - Test first: `tests/test_plugin.py` の版のテストを 0.4.0 にして赤になる
  - Verify: `uv run pytest` がすべて緑。`uv run ruff check . && uv run ruff format --check .` が通る。`examples/design-review.md`・`examples/sample.md`・`examples/bilingual.md` の `build.py` での生成が終了コード 0。`openspec validate extend-table-statement-section --strict` が通る
  - Review: batch B / Risk: none

## Scenario と確かめるタスク

- slide-generation「中扉レイアウト」: 2.3（混ぜたときの拒否）、3.1（位置とページ番号）
- 「改行」: 2.1（解析と拒否）、3.1（`a:br`）
- 「表の文字の大きさ」: 2.4（判定）、3.2（16pt の描画）
- 「表の列の強調」: 2.5（判定）、3.2（線と文字の色）
- 「原稿の区切りと表紙」: 2.3（`# ` と `## ` の混在）、表紙の Scenario は既存のテスト
- 「一言レイアウト」: 2.2（補足の判定）、3.1（補足の描画）
- 「表レイアウト」: 3.2（強調のない列の線が今と同じ）、既存の Scenario は既存のテスト
- 「未対応の書式の拒否」: 既存のテスト。`<br>` の場所は 2.1
- 「添え訳の書式」「添え訳の文字」「添え訳の配置」の足した対象: 2.2・2.3（解析）、3.1（補足と中扉）、3.2（16pt の表の 10pt）
- slide-plugin「Skill の内容」: 4.2（中扉、補足・改行・列の強調。6 種の Scenario は既存のテストを 7 種に広げて確かめる）、構成図と添え訳の Scenario は `add-flow-diagram` のテスト
