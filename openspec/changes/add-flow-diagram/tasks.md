Issue: #14

# Tasks

作業場所: worktree `.claude/worktrees/add-flow-diagram`、ブランチ `feature/add-flow-diagram`。テスト `uv run pytest`、lint `uv run ruff check . && uv run ruff format --check .`。生成器のパスは `plugin/skills/slide/scripts/slidekit/`（以下 `slidekit/`）。

## 1. 共通の部品

- [x] 1.1 行内の規則を `slidekit/inline.py` に移す
  - Refs: Requirement「構成図ファイルの行」、D1、D11
  - Files: `slidekit/inline.py`（新規）、`slidekit/manuscript.py`、`tests/test_inline.py`（新規）
  - Interface: `inline.Run`、`inline.Text`、`inline.runs(s: str) -> Text`、`inline.is_emoji(ch: str) -> bool`、`inline.inline_problems(s: str) -> list[str]`。`manuscript.Run` と `manuscript.Text` はそのまま使える
  - Test first: `tests/test_inline.py` が、`runs` の強調の分け方、`inline_problems` がインラインコード・リンク・`__`・`~~`・`*強調*`・閉じていない `**` のそれぞれに今と同じ理由を返すこと、`is_emoji` を確かめて赤になる。既存のテストと `tests/test_compat.py` は緑のまま
  - Review: batch A / Risk: none

- [x] 1.2 範囲の枠の色と、構成図の文字の大きさを定義する
  - Refs: Requirement「固定の配色と書体」「構成図の見た目」、D3
  - Files: `slidekit/palette.py`、`slidekit/fit.py`、`tests/test_palette.py`、`tests/test_fit.py`
  - Interface: `palette.FRAME = "BDBDBD"`（`GRID_COLORS` には足さない）。`fit.PT_BOX_NAME = 16`、`fit.PT_BOX_LINE = 12`、`fit.PT_FLOW_LABEL = 12`、`fit.PT_CROSS = 32`、`fit.PT_FLOW_NOTE = 16`
  - Test first: `FRAME` の値と、`GRID_COLORS` の値に含まれないこと、5 つの大きさの値を確かめて赤になる
  - Review: batch A / Risk: none

## 2. 構成図ファイルの解析（`slidekit/flow.py`）

- [x] 2.1 行の種類と配置の行を解析する
  - Refs: Requirement「構成図ファイルの行」「配置の行」、D1、D2
  - Files: `slidekit/flow.py`（新規）、`tests/test_flow.py`（新規）
  - Interface: `flow.parse_flow(text: str) -> FlowSpec`、`flow.FlowError(problems)`、`flow.FlowProblem(line: int | None, message: str)`、`FlowSpec`・`BoxSpec`・`GroupSpec`・`ArrowSpec`（D1 のフィールド）
  - Test first: `tests/test_flow.py` が次を確かめて赤になる。4 種の行の判定と読めない行の拒否（行番号）。配置の行のセルから箱と列・行の位置ができること、空のセル、上下に続く同じ名前が 1 つの行をまたぐ箱になること、離れたセルと別の列の同じ名前・列の数のずれ・名前に使えない文字・間に別の行を挟んだ配置の行・配置の行がないことの拒否。構成図ファイルの中の絵文字とリンクの拒否
  - Review: batch A / Risk: none

- [x] 2.2 箱の中の行・範囲の枠・矢印の行を解析する
  - Refs: Requirement「箱の中の行」「範囲の枠」（行の書式と名前の確認だけ）「矢印の行」、D2
  - Files: `slidekit/flow.py`、`tests/test_flow.py`
  - Test first: 次を確かめて赤になる。箱の中の行が書いた順に並び、`**` が強調の `Run` になること、5 行目・配置にない名前の拒否。`[ラベル] a, b` のメンバー、空のラベル・配置にない名前・同じラベルの 2 つ目の枠の拒否。矢印の属性 4 種と組み合わせ、`: ラベル` と `<br>` の 2 行、`× ` のラベル、知らない属性（理由に使える属性を並べる）・`上回り` と `下回り`・始点と終点が同じ・同じ組の 2 本目・3 行のラベル・ラベルの `**`・強調でない矢印の `×` の拒否と行番号
  - Review: batch A / Risk: none

- [x] 2.3 構成図ファイルの中の強調を数える
  - Refs: Requirement「構成図の強調」、D8
  - Files: `slidekit/flow.py`、`tests/test_flow.py`
  - Interface: `FlowSpec.emphasis_lines: list[int]`
  - Test first: 次を確かめて赤になる。同じ箱から出る 2 本の `強調` は 1 か所（`emphasis_lines` が 1 つ）。共通の箱を持たない 2 本目の `強調` の拒否（2 本目の行番号）。同じ箱に入る 3 本は 1 か所。箱の中の `**` が 1 か所と数えられること、`強調` の矢印と箱の中の `**` の両方で、2 か所目の行の拒否
  - Review: batch A / Risk: none

## 3. 配置（`slidekit/layout.py`）

- [ ] 3.1 箱の大きさ、列と行の間隔、範囲の枠の位置を計算する
  - Refs: Requirement「箱の大きさ」「列と行の間隔」「範囲の枠」、D3、D4
  - Files: `slidekit/layout.py`（新規）、`tests/test_layout.py`（新規）
  - Interface: `layout.layout_flow(spec: FlowSpec, max_w: float, max_h: float) -> Diagram`、`Diagram`・`PlacedBox`・`PlacedFrame`・`PlacedArrow`・`PlacedLabel`・`PlacedCross`（D1 のフィールド）。D3 の寸法の定数
  - Test first: `tests/test_layout.py` が `Diagram` の座標で次を確かめて赤になる（差は 1e-6 インチまで）。同じ列の箱の幅がそろい、最も長い名前が入ること。`BOX_MIN_W` と `BOX_MIN_H`。行をまたぐ箱の上端と下端。最大の幅を超える箱の中の行の拒否（行番号と箱の名前）。入れ子の枠が内側の枠の外にあり、線が重ならないこと。左右に並ぶ 2 つの枠の間が、`COL_GAP` + 2×`FRAME_PAD` であること。メンバーでない箱が入る枠と、一部だけ重なる枠の拒否（枠の行番号と箱の名前）。枠のラベルが枠に入らないときの拒否
  - Review: batch B / Risk: none

- [ ] 3.2 矢印の経路を決め、箱を横切る経路を拒否する
  - Refs: Requirement「矢印の経路」、D5
  - Files: `slidekit/layout.py`、`tests/test_layout.py`
  - Test first: 次を確かめて赤になる。同じ行・同じ列・斜めの直線の端点。1 から 3 に分かれる矢印が同じ点から出ること。`上回り` が 4 点の経路で、横向きの線分がすべての箱と枠より上にあること。2 本の `上回り` の通り道が分かれること。`下回り`。箱を横切る直線の拒否（理由に `上回り` か `下回り`）。同じ列どうしの回り込みの拒否。同じ辺から出る 2 本目の回り込みの拒否。枠のラベルを通る経路の拒否
  - Review: batch B / Risk: none

- [ ] 3.3 ラベルと × を置き、重なりと図の大きさを判定する
  - Refs: Requirement「ラベルと × の位置」「構成図の大きさの上限」、D6、D7、D4 の 6
  - Files: `slidekit/layout.py`、`tests/test_layout.py`
  - Test first: 次を確かめて赤になる。水平な矢印のラベルが線の下で、2 つの箱の間にあること。ラベルに合わせて列の間が広がること（12pt で 2.0 インチのラベル）。垂直な矢印のラベルが線の右にあること。斜めの矢印のラベルが下側、下側が重なるときは上側にあること。両方重なるときの拒否（矢印の行番号）。× 印が横向きの線分の中点にあり、文が外側にあること。原点が全体の左上にあること。幅が `max_w` を超える図と、高さが `max_h` を超える図の拒否（図の幅か高さと枠の大きさ、行番号なし）。設計の対話の図 1〜4・6・7 が `max_w = 11.53`・`max_h = 4.9` で、図 5 の 2 つが `max_w = 5.5` で通ること（`examples/design-review/` は 6.1 で作るので、ここではテストの中の文字で書く）
  - Review: batch B / Risk: none

## 4. 原稿への組み込み

- [ ] 4.1 図と左右 2 列から構成図ファイルを参照し、注記・強調・違反の報告を組み込む
  - Refs: Requirement「構成図の図と注記」「図レイアウト」「左右 2 列レイアウト」「構成図の強調」「構成図の違反の報告」、D1、D8、D10
  - Files: `slidekit/manuscript.py`、`tests/test_manuscript_flow.py`（新規）、`tests/test_build_cli.py`
  - Interface: `manuscript.DiagramFigure`、`manuscript.DiagramBlock`（D1 のフィールド）
  - Test first: `tests/test_manuscript_flow.py` が次を確かめて赤になる。`.flow` の図が `DiagramFigure` になり、注記が `note` に入ること。2 列の画像の行が `DiagramBlock` になること。注記が 16pt で 4 行になるときの拒否。注記の添え訳の拒否。注記の高さの分だけ `max_h` が減ること（注記がなければ収まり、あれば高さで拒否される構成図）。構成図に 1 か所、注記に 1 か所の強調で、注記の行の拒否。左右に 1 か所ずつで、右の画像の行の拒否。構成図ファイルの違反が「構成図ファイル <参照> の <行番号> 行目:」の形で画像の行に付くこと、行のない違反の形、ないファイルの拒否。`tests/test_build_cli.py` に、標準エラーの 1 行が `:<画像の行>: 構成図ファイル` を含むことを 1 件足す
  - Review: batch B / Risk: none

## 5. 描画

- [ ] 5.1 グループ図形・箱・範囲の枠・注記を描く
  - Refs: Requirement「構成図の見た目」（箱と枠）「構成図のまとまりと代替テキスト」「構成図の図と注記」「装飾を持たない」「固定の配色と書体」、D9
  - Files: `slidekit/render.py`、`tests/test_render_flow.py`（新規）、`tests/test_render.py`（`COLORS` を 6 色に）
  - Test first: `tests/test_render_flow.py` が、構成図を含む原稿から作った PPTX を python-pptx で読んで次を確かめて赤になる（位置の差は 2 EMU まで）。グループ図形が 1 つで、名前が `構成図`、`descr` が `説明`。グループの左上が（0.9, 1.8）インチ、2 列の右の塊では右の塊の x。箱が角丸でない長方形で、塗りがなく、線が 1.25pt の `1A1A1A`。名前が 16pt の `1A1A1A`、中の行が 12pt の `6B6B6B`、強調の行の語句が `B23A2E`。枠が 1pt の破線の `BDBDBD`、ラベルが 12pt の `6B6B6B`。`BDBDBD` が枠の線にしか使われていないこと。どの図形にも `p:style` と効果がないこと。すべての段落が左寄せで、書体がメイリオであること。注記が図の下端から 0.3 インチ下で、16pt であること
  - Review: batch C / Risk: ui

- [ ] 5.2 矢印・ラベル・× を描く
  - Refs: Requirement「構成図の見た目」（矢印・ラベル・×）「装飾を持たない」、D9
  - Files: `slidekit/render.py`、`tests/test_render_flow.py`
  - Test first: 次を確かめて赤になる。直線がコネクタで、折れ線が開いた経路の図形であること。どちらも 1.5pt の `1A1A1A` で、終わりが三角であること。`強調` が 2pt の `B23A2E`、`破線` が `dash` であること。ラベルが 12pt の `6B6B6B`、強調の矢印のラベルが `B23A2E` であること。× 印が 32pt の `B23A2E`、文が 12pt の `B23A2E` であること。描いた線の端点と経路の点が `Diagram` の座標と一致すること
  - Review: batch C / Risk: ui

## 6. 見本・文書・版

- [ ] 6.1 7 つの図の見本の原稿を作る
  - Refs: D12、Requirement「構成図の図と注記」「左右 2 列レイアウト」
  - Files: `examples/design-review.md`（新規）、`examples/design-review/*.flow`（新規）、`tests/test_examples.py`
  - Test first: `tests/test_examples.py` が、`examples/design-review.md` が `build.py` で終了コード 0 になること、構成図が 8 つ（図のレイアウトが 6 枚、2 列が 1 枚で左右に 1 つずつ）あること、注記のある図が 2 枚以上あることを確かめて赤になる。`tests/test_compat.py` は緑のまま
  - Review: batch C / Risk: ui

- [ ] 6.2 Skill の文書に構成図を書く
  - Refs: Requirement「Skill の内容」、D12
  - Files: `plugin/skills/slide/references/format.md`、`plugin/skills/slide/SKILL.md`、`plugin/skills/slide/references/writing.md`、`tests/test_skill_docs.py`
  - Test first: `tests/test_skill_docs.py` が次を確かめて赤になる。`format.md` と `SKILL.md` のすべての `flow` の例が `parse_flow` と `layout_flow`（11.53 × 4.9）で通ること。`format.md` の原稿の例が、最初の `flow` の例を `構成.flow` として置いたうえで生成できること（既存のテストを広げる）。`format.md` に構成図の 4 種の行と図の強調の数え方の節が、`writing.md` に構成図の使いどころの規則があること（見出しか鍵となる語で確かめ、文言は写さない）
  - Review: batch C / Risk: none

- [ ] 6.3 作成役・点検役に構成図の観点を足し、版を 0.3.0 に上げる
  - Refs: Requirement「作成役 Agent」「点検役 Agent」、D12
  - Files: `plugin/agents/writer.md`、`plugin/agents/critic.md`、`plugin/.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`tests/test_plugin.py`
  - Test first: `tests/test_plugin.py` が次を確かめて赤になる。作成役の定義に、構成図を構成や流れの説明だけに使うこと・構成図ファイルを原稿と同じフォルダに書くこと・拒否されたら構成図ファイルも直すことがあること。点検役の定義に、参照された構成図ファイルも読むこと・飾りの構成図を指摘することがあること。点検役の道具が読み取りだけのままであること。両方のマニフェストの版が 0.3.0 であること（既存の 0.2.0 のテストを置き換える）
  - Review: batch C / Risk: none

- [ ] 6.4 すべてのテストと lint を通し、見本の PPTX を作る
  - Refs: D11、D12
  - Files: なし（確認だけ）
  - Verify: `uv run pytest` がすべて緑。`uv run ruff check . && uv run ruff format --check .` が通る。`uv run plugin/skills/slide/scripts/build.py examples/design-review.md -o <一時フォルダ>/design-review.pptx` と、`examples/sample.md`・`examples/bilingual.md` の生成が終了コード 0。`openspec validate add-flow-diagram --strict` が通る
  - Review: batch C / Risk: none

## Scenario と確かめるタスク

- flow-diagram「構成図ファイルの行」: 2.1（4 種の行、読めない行、絵文字）
- 「配置の行」: 2.1（またぐ箱の解析）、3.1（またぐ箱の上端と下端）
- 「箱の中の行」: 2.2（解析と拒否）、5.1（強調色）
- 「範囲の枠」: 3.1
- 「矢印の行」: 2.2
- 「箱の大きさ」: 3.1
- 「列と行の間隔」: 3.1（2 つの枠）、3.3（ラベルの入る広さ）
- 「矢印の経路」: 3.2
- 「ラベルと × の位置」: 3.3
- 「構成図の大きさの上限」: 3.3（幅）、4.1（左右 2 列の幅は `max_w` の渡し方として）
- 「構成図の見た目」: 5.1、5.2
- 「構成図のまとまりと代替テキスト」: 5.1
- 「構成図の強調」: 2.3（同じ箱、離れた 2 本）、4.1（構成図と注記）
- 「構成図の違反の報告」: 4.1
- slide-generation「構成図の図と注記」: 4.1（拒否）、5.1（位置と大きさ）
- 「図レイアウト」の「構成図ファイルの図」: 4.1。既存の Scenario は既存のテスト
- 「左右 2 列レイアウト」の「2 つの構成図を比べる」: 4.1（解析）、5.1（位置）
- 「固定の配色と書体」: 5.1（6 色、範囲の枠の色）、既存の `tests/test_render.py`
- 「装飾を持たない」の「構成図に装飾がない」: 5.1
- slide-plugin「Skill の内容」の 2 つの Scenario: 6.2
- 「作成役 Agent」「点検役 Agent」の構成図の観点: 6.3
