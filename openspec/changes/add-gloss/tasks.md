Issue: #9

# Tasks

作業場所: worktree `.claude/worktrees/add-gloss`、ブランチ `feature/add-gloss`。テスト `uv run pytest`、lint `uv run ruff check . && uv run ruff format --check .`。生成器のパスは `plugin/skills/slide/scripts/slidekit/`（以下 `slidekit/`）。

## 1. 後方互換の基準

- [x] 1.1 いまの出力の部品ごとのハッシュを基準として保存し、比べるテストを足す
  - Files: `tests/test_compat.py`（新規）、`tests/fixtures/sample_parts.json`（新規）
  - Test first: このタスクは、いまの振る舞いを固定するテストなので、生成器のコードに触る前に作り、いまのコードで緑になることを確かめる。`examples/sample.md` から PPTX を作り、`docProps/core.xml` を除く部品の名前の集合と SHA-256 が基準ファイルと一致することを確かめる。基準ファイルは、このタスクの中で、変更前のコードの出力から作る。基準の作り直しの条件（design.md「後方互換は部品ごとのハッシュで固定する」）をテストのコメントに書く。テストが本当に守っているかは 6.1 で確かめる
  - Review: batch A / Risk: none

## 2. 色と大きさの定義

- [x] 2.1 添え訳の色、大きさの比率、行数の上限、2 列の箇条書きの項目の間隔を定義する
  - Files: `slidekit/palette.py`、`slidekit/fit.py`、`slidekit/render.py`（2 列の箇条書きの間隔 10pt を `fit.py` の定数から読むように変えるだけ）、`tests/test_palette.py`、`tests/test_fit.py`
  - Interface: `palette.GLOSS = "767676"`（`GRID_COLORS` には足さない）。`fit.GLOSS_RATIO = 0.6`、`fit.gloss_pt(pt: float) -> int`（本文の大きさから添え訳の大きさ）、`fit.MAX_GLOSS_LINES = 2`、`fit.COLUMN_BULLET_GAP_PT = 10`
  - Test first: `tests/test_palette.py` で `GLOSS` が `767676` で、`GRID_COLORS` の値に含まれないこと、`tests/test_fit.py` で `gloss_pt` が 40→24、30→18、24→14、22→13、20→12、18→11 を返すことを確かめて赤になる。1.1 のテストは緑のまま
  - Review: batch A / Risk: none

## 3. 原稿の解析と判定

- [x] 3.1 添え訳の行を対象に結びつけ、表以外の対象のデータに持たせ、拒否の規則を加える
  - Files: `slidekit/manuscript.py`、`tests/test_manuscript_gloss.py`（新規）
  - Interface: design.md「データの持ち方」のフィールド（`Cover.title_gloss`、`Cover.line_glosses`、`Statement.gloss`、`heading_gloss`、`Bullets.item_glosses`、`BulletsBlock.item_glosses`、`Figure.caption_gloss`、`TextBlock.gloss`）。型は `str | None` と、その並び（`list[str | None]`）
  - Test first: `tests/test_manuscript_gloss.py` が次を確かめて赤になる。表紙のタイトルと文、一言、見出し、箇条書きの項目、2 列の項目と文、図の説明文の添え訳が各フィールドに入ること。添え訳があっても箇条書きの項目の数が変わらないこと。拒否と行番号: スライドの先頭、空行の直後、画像の行（図と 2 列）・`|||` の直後、続けて 2 行（2 行目の行番号）、`**`、`^` だけの行、`^訳`、添え訳の中の絵文字・リンク・インラインコード・`__強調__`。添え訳の `**` 以外の強調がないスライドで、本文の強調 1 か所が拒否されないこと（添え訳を数えない）。添え訳のない原稿の解析結果のいまのフィールドが変わらないこと（既存のテストが緑のまま）
  - Review: batch B / Risk: none

- [x] 3.2 表の添え訳の行を解析する
  - Files: `slidekit/manuscript.py`、`tests/test_manuscript_gloss.py`
  - Interface: `Table.header_glosses: list[str | None]`（列の数と同じ長さ）、`Table.row_glosses: list[list[str | None]]`（`rows` と同じ形）
  - Test first: 見出し行と本文の行の添え訳がセルごとに入ること、`^ | 売上 | | 前年比 |` で 2 列目が `None` になること、列数の違う添え訳の行、すべて空の添え訳の行、区切り行の直後の添え訳、セルの中の `**` が拒否されることを確かめて赤になる
  - Review: batch B / Risk: none

- [x] 3.3 添え訳の行数の上限と、高さの判定を加える
  - Files: `slidekit/manuscript.py`、`tests/test_manuscript_gloss.py`
  - Test first: 次を確かめて赤になる（行の数は `fit.line_count` で数えて原稿を作る）。
    - 箇条書きの項目に 14pt の枠で 3 行の添え訳を書くと、添え訳の行番号と「上限は 2 行」を含む理由で拒否する。見出しと表紙の文の添え訳は 2 行で拒否する
    - 24pt で 2 行の項目 3 つに 14pt で 2 行の添え訳をつけると、3 つ目の添え訳の行番号で拒否する（添え訳がなければ通る）
    - 2 列の左の塊で、22pt で 2 行の項目 4 つに 13pt で 2 行の添え訳をつけると、4 つ目の項目の行番号で拒否する（添え訳がなければ通る）
    - 3 列の表で、1 行のセルに、見出し行・本文 1・2 行目に 11pt で 2 行の添え訳、本文 3・4 行目は添え訳なし、本文 5 行目に 2 行の添え訳をつけると、5 行目の添え訳の行番号で拒否する（5 行目の添え訳を除けば通る）
    - 上限まで書いた表紙（タイトル 2 行と添え訳 2 行、文 3 行と添え訳 1 行ずつ）・一言（3 行と 2 行）・図の説明文（3 行と 2 行）・2 列の文（3 行と 2 行）は通る
    - 標準エラーの形式が `<原稿のパス>:<行番号>: <理由>` であることを、`build.py` を動かして 1 件確かめる
  - Review: batch B / Risk: none

## 4. 描画

- [ ] 4.1 表紙・一言・見出しの添え訳を描く
  - Files: `slidekit/render.py`、`tests/test_render_gloss.py`（新規）
  - Test first: `tests/test_render_gloss.py` が、できた PPTX を python-pptx で読んで次を確かめて赤になる（位置は差 2 EMU まで）。見出しの添え訳の枠が y 1.225 インチ・高さ 0.375 インチで下端が 1.8 インチより上、見出しの枠の高さが 0.625 インチ、文字は 18pt。表紙のタイトルの添え訳（1 行と 2 行の両方）の枠の下端が 3.8 インチで、タイトルの枠の下端がその上端と同じ、文字は 24pt。表紙の文の添え訳が文の段落のすぐ次の段落で 12pt、枠の高さが 2.4 インチ。一言の添え訳が文の段落のすぐ次の段落で 24pt。すべて色は `767676`、書体はメイリオ（欧文・和文）、太字でない、左寄せ。添え訳のない見出し・表紙の枠はいまの位置と大きさ（1.1 のテストも緑のまま）
  - Review: solo / Risk: ui

- [ ] 4.2 箇条書き・2 列・図の説明文・表のセルの添え訳を描く
  - Files: `slidekit/render.py`、`tests/test_render_gloss.py`
  - Test first: 次を確かめて赤になる。箇条書きの項目の段落のすぐ次の段落が添え訳で 14pt、行頭の記号がなく（`buNone`）、`marL` 0.4 インチ・`indent` 0 で、文字の左端が項目の本文の左端（`marL + indent` = 0.4 インチ）と同じ、段落の前の間隔が 0。2 列の箇条書きと文で同じく 13pt。図の説明文の段落のすぐ次の段落が 12pt。表のセルの 2 つ目の段落が 11pt で、添え訳のないセルは段落が 1 つだけ。色・書体・太字・左寄せは 4.1 と同じ
  - Review: solo / Risk: ui

- [ ] 4.3 確認用の原稿を足し、配色の要件のテストを 5 色に直す
  - Files: `examples/bilingual.md`（新規。英語の本文と日本語の添え訳で、6 種のレイアウトとすべての対象を 1 つずつ含む、5〜7 枚の原稿）、`tests/test_render.py`（`COLORS` を 5 色に）、`tests/test_render_gloss.py`、`tests/test_examples.py`
  - Test first: `examples/bilingual.md` から生成でき、すべての文字と線の色が 5 色のどれかで、`767676` の文字は添え訳の段落だけにあり、すべての対象（delta spec「すべての対象に添え訳をつける」）に添え訳が描かれていることを確かめて赤になる。`examples/sample.md` の出力のどの文字にも `767676` がないことも確かめる
  - Review: batch C / Risk: none

## 5. 文書と版

- [ ] 5.1 Skill の文書に添え訳を書く
  - Files: `plugin/skills/slide/references/format.md`（「添え訳」の節: 書き方、対象、表の書き方、大きさ、上限、拒否されるもの）、`plugin/skills/slide/SKILL.md`（「原稿の書式（最短）」の原稿の例に添え訳の行を 1 つ足すか、別の短い例を 1 つ足す）、`plugin/skills/slide/references/writing.md`（「添え訳は本文と同じ意味にし、情報を足したり削ったりしない」）、`tests/test_skill_docs.py`
  - Test first: `tests/test_skill_docs.py` で、`SKILL.md` の例に `^ ` の行があること、`format.md` に `^ ` と大きさ・上限・拒否の記述があること、`writing.md` に添え訳の規則があることを確かめて赤になる。`SKILL.md` と `format.md` の例がそのまま生成できることは既存のテストで確かめる
  - Review: batch C / Risk: none

- [ ] 5.2 作成役と点検役の定義に、添え訳の観点を足す
  - Files: `plugin/agents/writer.md`、`plugin/agents/critic.md`、`tests/test_plugin.py`
  - Test first: `tests/test_plugin.py` で、`writer.md` に「添え訳を本文と同じ意味にし、片方にしかない情報を作らない」こと、`critic.md` に「添え訳と本文の意味が合っているか、片方にしかない情報がないか」を点検することが書いてあるのを確かめて赤になる。`critic.md` の道具が読み取りだけであることは既存のテストのまま
  - Review: batch C / Risk: none

- [ ] 5.3 プラグインの版を 0.2.0 に上げる
  - Files: `plugin/.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`tests/test_plugin.py`
  - Test first: `tests/test_plugin.py` で、両方のマニフェストの版が `0.2.0` で一致することを確かめて赤になる
  - Review: batch C / Risk: none

## 6. 確認

- [ ] 6.1 守りのテストを `harness:mutation-check` で確かめる
  - Verify: それぞれ変えた複製で、対応するテストが赤になり、変えない複製（対照）では緑になる。結果を ledger に記す。
    - `fit.BULLET_GAP_PT` を 12 から 13 にした複製: 1.1 のテストが赤
    - 箇条書きの添え訳の段落の `buNone` を外した複製と、`marL` を 0 にした複製: 4.2 のテストが赤
    - 箇条書きの高さの合計から添え訳の高さを除いた複製: 3.3 の箇条書きの高さのテストが赤
    - 続けて 2 行の添え訳を受け付けるようにした複製: 3.1 のテストが赤
    - 添え訳の色を `GRAY` にした複製: 4.1 と 4.3 のテストが赤
  - Review: batch D / Risk: none

- [ ] 6.2 すべてのコマンドを通し、確認用の PPTX を作る
  - Verify: `uv run pytest` がすべて緑、`uv run ruff check . && uv run ruff format --check .` が通る。`uv run plugin/skills/slide/scripts/build.py examples/bilingual.md -o <一時フォルダ>/bilingual.pptx` と `examples/sample.md` の生成が終了コード 0。PR の本文に、PO が受け入れで PowerPoint で開いて見るファイルの作り方と、見る点（見出しと添え訳が重ならないか、添え訳が読める濃さか、表の 11pt が投影で読めるか）を書く
  - Review: batch D / Risk: none

## シナリオと確認するタスク

- slide-generation「添え訳の書式」: 箇条書きの項目と見出し → 3.1。すべての対象 → 3.1・3.2（解析）、4.3（描画）。表の一部のセル → 3.2
- slide-generation「添え訳の拒否」: 対象のない添え訳、対象にできない行の後、続けて 2 行、強調、空と記号の誤り、絵文字 → 3.1（6.1 で mutation check）。表の列数の誤り → 3.2。区切り行の直後 → 3.2
- slide-generation「添え訳の文字」: 各レイアウトの大きさ → 4.1・4.2（6.1）
- slide-generation「添え訳の配置」: 箇条書きの位置・大きさ・色 → 4.2（6.1）。見出しは本文の枠と重ならない、表紙のタイトル → 4.1
- slide-generation「添え訳の行数と枠の高さ」: 長すぎる、見出しは 1 行まで、枠の高さを超える、2 列の箇条書きの高さ、表の高さ、上限まで書いても収まる → 3.3（6.1）
- slide-generation「添え訳のない原稿の互換」: 見本原稿の出力が変わらない → 1.1（6.1）
- slide-generation「固定の配色と書体」: 配色と書体 → 4.3 と既存の `tests/test_render.py`。添え訳の色は添え訳だけ → 4.3（6.1）
- slide-plugin「Skill の内容」: 例がそのまま通る、6 種のレイアウト → 既存の `tests/test_skill_docs.py`。添え訳の例、添え訳の書き方の規則 → 5.1
- slide-plugin「作成役 Agent」: 主題からスライドを作る → 既存（add-slide-plugin の確認のとおり）。添え訳を書くときの観点 → 5.2
- slide-plugin「点検役 Agent」: 道具が読み取りだけ、仕込んだ AI っぽさ → 既存。添え訳を点検する観点 → 5.2

## Proposals

- （batch A レビュー、Minor）`tests/test_fit.py` の `test_gloss_limits` は定数がリテラルと等しいことしか見ていない。振る舞いは 3.3 と 6.1 のテストで守られるので、残すか消すかは後の整理で決める。
- （batch B レビュー、Minor）表紙の文が 4 行以上で、上限を超えた行に添え訳があると、「表紙の文は 3 行までです」に加えて「この行には添え訳をつけられません」も出る。上限を超えた分岐で添え訳を読み捨てれば 1 件になる。
- （batch B レビュー、Minor）`^2 is square` のような行で、同じ行番号に「`^` の次に空白がない」と「対象がない」の 2 件が出る。
- （batch B レビュー、Minor）`manuscript.py` の `_check_stack` の理由の文が、はみ出した段落が添え訳のときも「この項目の下端」になる。行番号は正しい。
