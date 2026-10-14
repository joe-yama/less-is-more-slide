# Design

## Context

動機は proposal.md の「Why」、振る舞いは 2 つの delta spec を参照。寸法と文字の大きさは、`manuscript.py`（判定）と `render.py`（描画）が `fit.py` の同じ定数を使う（`tests/test_render.py` の `test_manuscript_and_render_share_size_definitions`）。この変更で足す大きさも `fit.py` に置く。

## 合意事項（2026-10-14 設計の対話、PO が設計案を承認）

`add-flow-diagram` と同じ対話で決めた（その変更の `design.md` の「合意事項」）。この変更に関わるものは次のとおり。

- 表: 18pt で入らない表は、1 段だけ（16pt）小さくする。見出しのセル全体の `**` で列を強調し、列を強調色の枠で囲む。セルの改行は `<br>`。
- 一言: 一言（40pt のまま）と補足（24pt、灰色）の 2 段にする。PO の資料の 3 段目（20pt の灰色）と 44pt は採らない。改行は `<br>` で書き手が決め、最後の行の短さを生成器は判定しない。
- 中扉: 2 枚目以降の `# タイトル` だけのスライド。
- 見出し: 27 字を超えても縮めず、拒否のままにする。
- `<br>` を書けるのは、一言とその補足、表のセルだけ。

## Decisions

### D1 前提と始め方

この変更は `add-flow-diagram` がマージされ、アーカイブされた後に実装する。最初のタスク（1.1）で、ブランチを最新の `main` に載せ直す。`slide-plugin` の「Skill の内容」の MODIFIED の文は、`add-flow-diagram` の後の文を元にしている。アーカイブの後の main の spec と比べ、構成図の部分が違っていれば、`/opsx:update` でこの変更の delta を合わせる。

### D2 データの持ち方

今のフィールドの型と意味は変えず、既定値つきで足す（互換のため）。

- `Statement.notes: list[Text]`（補足。既定は空）、`Statement.note_glosses: list[str | None]`（`notes` と同じ長さ）
- 新しいスライド `Section(title: str, title_gloss: str | None = None)`
- `Table.pt: int`（既定 18）、`Table.emphasis_col: int | None`（既定 `None`）
- 改行は、`Run.text` の中の `\n` で表す。`<br>` を書ける場所の解析で `<br>` を `\n` に置き換えてから、`runs` に渡す。

`fit.py` に足す定数: `PT_STATEMENT_NOTE = 24`、`STATEMENT_NOTE_GAP_PT = 12`（一言と補足の間、補足どうしの間）、`STATEMENT_BOX_H = 6.3`（一言の枠の高さ。`render.py` の今の `7.5 - 2 * HEAD_TOP` をこの定数に置き換える）、`PT_CELL_SMALL = 16`、`TABLE_EMPHASIS_LINE_PT = 1.5`。

### D3 改行の判定

- 改行として受け付けるのは `<br>` だけ。`<br/>`・`<br />`・`<BR>` など、`br` のタグのほかの書き方は「改行は `<br>` と書きます」と拒否する。
- 一言とその補足、表のセル（見出し行と本文の行）以外の行の `<br>` は、「`<br>` は一言・補足・表のセルにだけ書けます」と拒否する。添え訳の `<br>` も同じ理由で拒否する。
- 文の先頭や末尾の `<br>` と、続けて 2 つの `<br>` は、「`<br>` の前後に文字が要ります」と拒否する（空の行を作らない）。
- 行数は、`\n` で分けた部分ごとに `fit.line_count` で数えて足す。この計算は `fit.py` の関数にし、判定と描画の両方で使う。
- 描画では、`\n` の位置に `a:br` を入れ、同じ段落の中で行を改める。

### D4 一言と補足

- 見出しのないスライドの行（添え訳を除く）が 1〜3 行なら一言とする。1 行目が一言、2・3 行目が補足。4 行目があれば、その行で「一言の補足は 2 行までです」と拒否する。2 行目以降に箇条書き・表・画像の行があれば、今の理由で拒否する。
- 一言は 40pt で 3 行まで、補足は 24pt で、本文の幅（11.53 インチ）で 2 行まで。補足の添え訳は 14pt で 2 行まで。
- 高さ: 一言、その添え訳、補足（前に `STATEMENT_NOTE_GAP_PT`）、その添え訳の順に積み、`STATEMENT_BOX_H` を最初に超えた段落の行で拒否する（今の `_check_stack` の書き方に合わせる）。
- 描画: 今の一言の文字の枠（上下中央）に、一言の段落とその添え訳の段落の後へ、補足の段落（24pt、`GRAY`、前の間隔 `STATEMENT_NOTE_GAP_PT`）とその添え訳を足す。補足のない一言の出力は今と同じにする。

### D5 中扉

- 2 枚目以降のスライドで、行（添え訳を除く）が `# ` の 1 行だけなら `Section` とする。`# ` の行がほかの行と混ざっていれば、`# ` の行で「中扉は `# タイトル` の 1 行だけです。見出しは `## ` です」と拒否する。
- タイトルの判定は表紙のタイトルと同じ（40pt、本文の幅、2 行まで。空なら拒否）。添え訳は表紙のタイトルの添え訳と同じ。
- 描画: タイトルだけのレイアウト（`LAYOUT_TITLE_ONLY`）に、表紙のタイトルと同じ位置・大きさ・下寄せで置く。添え訳の置き方も表紙と同じ。表紙のタイトルとその添え訳を描く今の処理を関数に分け、表紙と中扉の両方から呼ぶ（表紙の出力は変えない）。ページ番号は、ほかのスライドと同じく入れる。

### D6 表の大きさの段

- `_table` を、大きさによらない判定（列の数、区切り行、行の数、列の強調）と、大きさごとの判定（セルの行数、添え訳の行数、高さ）に分ける。
- 大きさごとの判定は、違反をすぐに足さず、いったん集める。18pt で違反がなければ 18pt、あれば 16pt で判定し直し、違反がなければ 16pt にする。16pt でも違反があれば、16pt の違反だけを足す（理由の pt は 16 になる）。
- 16pt の表では、セルの添え訳は `gloss_pt(16)` = 10pt、行の高さの計算は `fit.table_row_height_in` に 16pt を渡す。セルの幅は 18pt の表と同じ。
- 描画は `Table.pt` を使う。18pt の表の出力は今と同じにする。

### D7 列の強調

- 見出し行のセルを `runs` にした結果が、強調の `Run` 1 つだけ（セルの文字全体が `**…**`）なら、その列を `emphasis_col` とする。見出しのセルに強調があり、文字全体でなければ、見出し行で「列の強調は、見出しのセルの文字全体を `**` で囲みます」と拒否する。
- 強調の数は、今の `_check_lines` の数え方のまま（見出しのセルの `**` が 1 か所）。2 か所目の行で拒否する。
- 描画: 強調した列のすべてのセルの `lnL` と `lnR`、見出しのセルの `lnT`、最後の行のセルの `lnB` を、`ACCENT` の 1.5pt の実線にする。隣の列のセルの、向かい合う辺（左隣の `lnR`、右隣の `lnL`）も同じ線にする（PowerPoint がどちらの辺の指定を使っても同じ見た目にするため）。見出し行の下の灰色の線は、強調した列でも残す。

### D8 見本と文書

- `examples/design-review.md`（`add-flow-diagram` が作る）に、次を足す: 一言と補足（`**C 案**` の強調と `<br>`）、4 列で 16pt になる比べる表（推す案の列の強調と、セルの `<br>`）、本編のあとの中扉 `# 補足資料` と、その後の 1 枚。中身は一般の例だけにする。
- `references/format.md`: レイアウトを 7 種にし、中扉の節、一言の補足、改行、表が 16pt になる条件、列の強調を書く。「枠に収まる長さ」の表に、一言の補足と 16pt の表のセルの行を足す。
- `SKILL.md`: 「原稿の書式（最短）」の例に中扉を足して 7 種にする（例は生成できるままにする）。
- `writing.md`: 規則に「2 行以上になる一言は、意味の切れ目で `<br>` を入れる」「補足は、一言の理由か条件を 1〜2 行で書く」を足す。
- 版は 0.4.0（`plugin.json` と `marketplace.json`）。

### D9 互換

`examples/sample.md` の出力は変えない。`tests/test_compat.py` の基準を作り直してはならない。今のテストのうち、仕様が変わる次の 2 つは、この変更の delta spec に合わせて書き換える（弱めるのではなく、新しい拒否の条件を確かめる形にする）: `tests/test_manuscript_basic.py` の `test_statement_with_two_lines_and_no_heading_is_rejected`（補足 3 行で拒否、に変える）と `test_h1_outside_the_cover_is_rejected`（`# ` とほかの行が混ざると拒否、に変える）。

### 2026-10-14 一言と補足の間隔は 12pt にする
- Ruling: 一言と補足の間、補足どうしの間は 12pt あける。
- Reason: 箇条書きの項目の間（`BULLET_GAP_PT` = 12pt）と同じにして、段の間隔の種類を増やさない。
- Cost if wrong: 補足が一言に近すぎる、または離れすぎて見える。PO が見本で判断し、定数 1 つを変える。

### 2026-10-14 列の強調の線は 1.5pt にする
- Ruling: 列の強調の枠は、ACCENT の 1.5pt の実線にする。
- Reason: PO の依頼文は太さを決めていない。表の横線（1pt）より太くして枠が強調だと分かるようにし、構成図の強調の矢印（2pt）より細くして表の文字より目立たないようにする。
- Cost if wrong: 枠が目立ちすぎるか、弱すぎる。PO が見本で判断し、定数 1 つを変える。

## Test plan

| 振る舞い（spec の Scenario） | 層 | テスト |
|---|---|---|
| 改行（3 つの Scenario の解析と拒否、行数の数え方） | Unit | `tests/test_manuscript_breaks.py`（新規）、`tests/test_fit.py` |
| 一言レイアウト（補足、補足の多すぎ・長すぎ、高さ） | Unit | `tests/test_manuscript_statement.py`（新規）、`tests/test_manuscript_basic.py`（D9 の書き換え） |
| 中扉レイアウト（混ぜたときの拒否）、原稿の区切りと表紙 | Unit | `tests/test_manuscript_section.py`（新規）、`tests/test_manuscript_basic.py`（D9 の書き換え） |
| 表の文字の大きさ（3 つの Scenario の判定） | Unit | `tests/test_manuscript_table_size.py`（新規） |
| 表の列の強調（一部の強調、ほかの強調） | Unit | `tests/test_manuscript_table_size.py` |
| 改行の描画、一言と補足の描画、中扉の位置とページ番号、中扉と補足の添え訳 | Render | `tests/test_render_extensions.py`（新規） |
| 16pt の表と 10pt の添え訳、列の強調の線、表レイアウト | Render | `tests/test_render_extensions.py` |
| 添え訳の書式・文字・配置（足した対象） | Render | `tests/test_render_extensions.py`（今の `tests/test_render_gloss.py` は変えない） |
| 未対応の書式の拒否（7 種） | Unit | 既存の `tests/test_manuscript_basic.py` が緑のまま。`<br>` は改行の行で確かめる |
| 互換（`examples/sample.md` の出力） | Compatibility | 既存の `tests/test_compat.py` |
| 見本の原稿が生成できる | CLI | `tests/test_examples.py` |
| Skill の内容（7 種、補足・改行・列の強調の例と規則） | Plugin and docs | `tests/test_skill_docs.py` |
| 見本の見た目（16pt の表が読めるか、列の枠、補足、中扉） | PowerPoint by eye | PO の受け入れ |
