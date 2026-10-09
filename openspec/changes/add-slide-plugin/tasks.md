Issue: #3

# Tasks

作業場所: worktree `.claude/worktrees/add-slide-plugin`、ブランチ `feature/add-slide-plugin`。テスト `uv run pytest`、lint `uv run ruff check . && uv run ruff format --check .`。

## 1. 開発基盤

- [x] 1.1 開発用の Python 環境と色の定数を作る
  - Files: `pyproject.toml`、`uv.lock`、`LICENSE`、`plugin/skills/slide/scripts/slidekit/__init__.py`、`plugin/skills/slide/scripts/slidekit/palette.py`、`tests/test_palette.py`
  - Interface: `slidekit.palette` の `PAPER`・`INK`・`GRAY`・`ACCENT`・`GRID_COLORS`（design.md「Interface」）
  - Test first: `tests/test_palette.py` が 4 色の値と、格子の 4 文字 → 色（`.` は `None`）の対応を確かめて赤になる
  - Review: batch A / Risk: none（`uv.lock` の作成は lockfile を変える導入なので PO の承認を待つ。依存は design.md「新しい依存」の 3 つだけ）

- [x] 1.2 CI の job `check` に Python の手順を足す
  - Files: `.github/workflows/ci.yml`
  - Verify: push 後の CI で job `check` が緑になり、ログに `uv sync --locked`、`ruff check`、`ruff format --check`、`pytest` の各手順が出る。job 名 `check` は変わっていない（`grep -n '^  check:' .github/workflows/ci.yml` が 1 行出る）
  - Review: batch A / Risk: none

- [x] 1.3 コマンドを記録し、ハーネスの設定値を PO に渡す
  - Files: `AGENTS.md`（コマンド表）、スクラッチパッドに `.claude/settings.json` の全文案と `.harness/env.json` の全文案（コミットしない）
  - Verify: `AGENTS.md` のコマンド表に lint（`uv run ruff check`、パターン `\.py$`）とテスト（`uv run pytest`）がある。PO に 2 つのファイルの配置を依頼し、配置後に `.py` を 1 つ編集して lint のフックが動くことを確かめる。配置を待たずに次のタスクへ進んでよい（design.md「ハーネスの設定は PO が置く」）
  - Review: solo / Risk: security（ハーネスの設定）

## 2. ドット絵

- [x] 2.1 格子ファイルの解析と検証
  - Files: `plugin/skills/slide/scripts/slidekit/grid.py`、`tests/test_grid.py`
  - Interface: `Problem`、`GridError`、`Grid`、`parse_grid`
  - Test first: `tests/test_grid.py` が、8×8 の正しい格子の受理、3 行目 5 文字目の `x` の拒否（行・文字の位置と使える文字を理由に含む）、短い 2 行目の拒否、幅 65 の拒否、末尾の空行の無視を確かめて赤になる
  - Review: batch B / Risk: none

- [x] 2.2 格子から PNG を作る
  - Files: `plugin/skills/slide/scripts/slidekit/png.py`、`tests/test_png.py`
  - Interface: `encode_png(grid, scale) -> bytes`
  - Test first: `tests/test_png.py` が、8×8 を拡大率 10 で変換した PNG を標準ライブラリで復号し、80×80 であること、各ドットが 10×10 の同じ色であること、画素が 3 色と完全な透明だけであることを確かめて赤になる
  - Review: batch B / Risk: none

- [x] 2.3 同梱アイコン 14 個と参照の解決
  - Files: `plugin/skills/slide/icons/*.txt`（14 個）、`slidekit/grid.py`（`icon_names`、`resolve`）、`tests/test_icons.py`
  - Interface: `icon_names() -> list[str]`、`resolve(ref, base_dir) -> Grid`
  - Test first: `tests/test_icons.py` が、14 個の名前がちょうど spec の一覧であること、すべて 16×16 の正しい格子であること、`icon:gear` と相対パスの `.txt` が解決できること、存在しない名前・ファイルと `.txt` 以外の参照が `GridError` になることを確かめて赤になる
  - Review: batch B / Risk: none

- [x] 2.4 ドット絵の CLI
  - Files: `plugin/skills/slide/scripts/pixel.py`（PEP 723、依存なし）、`tests/test_pixel_cli.py`
  - Interface: `pixel.main(argv) -> int`
  - Test first: `tests/test_pixel_cli.py` が、`--list` で 14 個の名前が 1 行ずつ出ること、`icon:gear` の既定の拡大率で 256×256 の PNG ができること、違反のある格子で終了コード 1・標準エラーに理由・PNG を作らないことを確かめて赤になる
  - Review: batch B / Risk: none

## 3. 原稿の解析

- [x] 3.1 文字幅の見積もり
  - Files: `plugin/skills/slide/scripts/slidekit/fit.py`、`tests/test_fit.py`
  - Interface: `text_width_em(text) -> float`、`line_count(text, font_pt, box_width_in) -> int`
  - Test first: `tests/test_fit.py` が、全角 1.0em・半角 0.6em の見積もりと、design.md の見出しの枠で全角 15 文字が 1 行・60 文字が 2 行以上になることを確かめて赤になる
  - Review: batch C / Risk: none

- [x] 3.2 原稿の区切り・表紙・一言・箇条書き・強調・絵文字・未対応の書式
  - Files: `plugin/skills/slide/scripts/slidekit/manuscript.py`、`tests/test_manuscript_basic.py`
  - Interface: `ManuscriptError`、`parse(text, base_dir) -> Deck`
  - Test first: `tests/test_manuscript_basic.py` が、slide-generation spec の「原稿の区切りと表紙」「一言レイアウト」「箇条書きレイアウト」「未対応の書式の拒否」「強調」「絵文字の拒否」の全シナリオと、複数の違反がすべて行番号付きで集まることを確かめて赤になる
  - Review: batch C / Risk: none

- [x] 3.3 図・表・左右 2 列
  - Files: `slidekit/manuscript.py`、`tests/test_manuscript_layouts.py`、`tests/fixtures/`（テスト用の格子）
  - Test first: `tests/test_manuscript_layouts.py` が、spec の「図レイアウト」「表レイアウト」「左右 2 列レイアウト」の全シナリオと、図の参照先の格子の違反が原稿の行番号と格子の位置で報告されることを確かめて赤になる
  - Review: batch C / Risk: none

- [x] 3.4 枠からのはみ出しの判定
  - Files: `slidekit/manuscript.py`、`tests/test_manuscript_fit.py`
  - Test first: `tests/test_manuscript_fit.py` が、design.md「寸法と文字の大きさ」の表の要素ごとに、上限ちょうどの行数は通り、1 行超えると拒否されること（spec の「見出しが長すぎる」「収まる長さ」を含む）を確かめて赤になる
  - Review: batch C / Risk: none

## 4. PPTX の生成

- [x] 4.1 6 種のレイアウトを PPTX に描く
  - Files: `plugin/skills/slide/scripts/slidekit/render.py`、`tests/test_render.py`
  - Interface: `render(deck, out_path) -> None`
  - Test first: `tests/test_render.py` が、6 種すべてを含む原稿の出力を python-pptx と XML で開き、spec の「固定の配色と書体」「装飾を持たない」「普通の PowerPoint 文書としての体裁」「強調」（色で表し太字でない）「表レイアウト」（塗りなし・横線だけ）の各シナリオ、テーマの書体がメイリオであること、画像の代替テキスト、作成日時が生成時刻であることを確かめて赤になる
  - Review: solo / Risk: ui

- [x] 4.2 生成器の CLI
  - Files: `plugin/skills/slide/scripts/build.py`（PEP 723: python-pptx）、`tests/test_build_cli.py`
  - Interface: `build.main(argv) -> int`
  - Test first: `tests/test_build_cli.py` が、spec の「生成コマンド」の全シナリオ（成功で 0 と PPTX、違反の行ごとの `<パス>:<行>: <理由>`、失敗時に既存の出力が変わらない）を確かめて赤になる
  - Review: batch D / Risk: none

- [x] 4.3 守りのテストの変異確認
  - Files: なし（記録は ledger と PR の証拠）
  - Verify: `harness:mutation-check` で、(a) 絵文字の判定を外す、(b) 色を 1 つ 4 色以外に変える、(c) 表のセルに塗りを足す、(d) 失敗時にも出力を書く、(e) 書体を 1 か所メイリオ以外にする、のそれぞれでテストが赤になり、元に戻すと緑になる
  - Review: batch D / Risk: none

## 5. Skill・Agent・配布

- [x] 5.1 見本原稿と、開発環境の外での生成
  - Files: `examples/sample.md`、`examples/robot.txt`、`tests/test_examples.py`、`.github/workflows/ci.yml`（`uv run --no-project` で見本を生成する手順）
  - Test first: `tests/test_examples.py` が、見本が 6 種のレイアウトをすべて含み、格子ファイルを参照し、生成に成功することを確かめて赤になる。CI の新しい手順は push 後の job `check` で緑になることを確かめる
  - Review: batch E / Risk: none

- [x] 5.2 Skill の本文と参照文書
  - Files: `plugin/skills/slide/SKILL.md`、`plugin/skills/slide/references/format.md`、`plugin/skills/slide/references/writing.md`、`tests/test_skill_docs.py`
  - Test first: `tests/test_skill_docs.py` が、SKILL.md と format.md の原稿の例（コードブロック）をすべて生成器に通して成功すること、6 種のレイアウトの書き方がそれぞれ載っていること、SKILL.md のコマンドが design.md の形（`uv run <Skill のフォルダ>/scripts/...`）であること、writing.md に AI っぽさの一覧の 12 項目があることを確かめて赤になる
  - Review: batch E / Risk: none

- [x] 5.3 2 つの Agent とマニフェスト
  - Files: `plugin/agents/writer.md`、`plugin/agents/critic.md`、`plugin/.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`tests/test_plugin.py`、`tests/fixtures/ai_tells.md`（AI っぽさを 5 種仕込んだ原稿。6.2 で使う）
  - Test first: `tests/test_plugin.py` が、2 つのマニフェストが JSON として正しく spec の項目を持つこと、マーケットプレイスがプラグインを 1 つだけ載せ source が `./plugin` であること、critic の `tools` が Read・Glob・Grep だけであること、writer と critic が Skill `slide` を参照することを確かめて赤になる
  - Review: batch E / Risk: none

- [ ] 5.4 README
  - Files: `README.md`、`tests/test_readme.py`
  - Test first: `tests/test_readme.py` が、Claude Code と Copilot CLI それぞれの導入コマンド、uv が必要なこと、見本原稿の場所が書いてあることを確かめて赤になる
  - Review: batch E / Risk: none

## 6. 統合確認

- [ ] 6.1 すべてのコマンドを通す
  - Verify: `uv run ruff check . && uv run ruff format --check . && uv run pytest` がすべて成功し、push 後の CI の job `check` が緑
  - Review: batch F（ブランチ全体の最終レビューで併せて見る）/ Risk: none

- [ ] 6.2 両方の CLI でプラグインを読み込んで動かす
  - Verify: `claude --plugin-dir ./plugin -p` と `copilot --plugin-dir ./plugin -p` のそれぞれで、(a) Skill `slide` と Agent `writer`・`critic` が見えること、(b) 作成役に主題と 3 行の材料を渡すと原稿と PPTX ができ返答に両方のパスがあること、(c) 点検役に `tests/fixtures/ai_tells.md` を渡すと 5 種のうち 4 種以上がスライド番号・引用・書き直し案付きで指摘され、ファイルが変わらないことを確かめる。結果と使った CLI の版を PR の証拠に書く。片方の CLI で失敗したら、原因を Issue に書いて PO に伝える
  - Review: batch F（ブランチ全体の最終レビューで併せて見る）/ Risk: none

## spec のシナリオと確かめるタスク

- slide-generation「生成コマンド」3 件 → 4.2
- 「原稿の区切りと表紙」「一言」「箇条書き」「未対応の書式」「絵文字」の各シナリオ → 3.2
- 「強調」→ 3.2（2 か所の拒否）、4.1（色で表す）
- 「図」「表」「左右 2 列」→ 3.3（受理と拒否）、4.1（表の塗りと線）
- 「枠からのはみ出し」2 件 → 3.1、3.4
- 「固定の配色と書体」「装飾を持たない」「普通の PowerPoint 文書としての体裁」→ 4.1、4.3
- pixel-art「格子ファイルの書式」4 件 → 2.1
- 「PNG への変換」2 件 → 2.2、2.4
- 「同梱アイコン」3 件 → 2.3、2.4
- slide-plugin「マニフェスト」→ 5.3
- 「Claude Code に導入する」「Copilot CLI に導入する」→ 6.2（`--plugin-dir`）、PO の受け入れ（マーケットプレイスからの導入）
- 「開発環境の外で動かす」→ 5.1（CI の `uv run --no-project`）
- 「Skill の例がそのまま通る」「6 種のレイアウトがすべて載っている」→ 5.2
- 「主題からスライドを作る」→ 6.2
- 「道具が読み取りだけ」→ 5.3
- 「仕込んだ AI っぽさを見つける」→ 6.2
- 「README の導入手順」→ 5.4

## Workflow follow-up

- PO の受け入れ: README の手順で、Claude Code と Copilot CLI の両方にマーケットプレイスからプラグインを導入する。`examples/sample.md` から作った PPTX を PowerPoint（と、あれば Keynote）で開き、はみ出しがなく「人が作った」ように見えるかを判断する。
- マージ後に `/opsx:archive`、`docs/changes.md` に rulings を写し、`docs/status.md` を更新する。

## Proposals

- （batch A レビュー Minor）`tests/test_palette.py` で、4 色の値と `GRID_COLORS` の対応が同じ値を二重に書いている。どちらか一方の書き方に寄せられる。
- （batch A レビュー Minor）CI の `astral-sh/setup-uv` に `enable-cache` を付けると、依存の取得が速くなる。
- （1.3 レビュー Minor）`AGENTS.md` の「The first change that introduces the stack adds ...」の文は、スタックが入った今は古い。現在の手順を書く文に改められる。
- （1.3 レビュー Minor）編集ごとの lint フックは `ruff check` だけで、整形の違反は CI の `ruff format --check` で初めて分かる。フックで整形も確かめる案がある。
- （batch B レビュー Minor）`pixel.py --scale abc` は argparse の使い方の誤りとして終了コード 2 を返す。spec の終了コード 1 に揃える案がある。
- （batch B レビュー Minor）`pixel.py` の出力先のフォルダがないと、Python のトレースバックが出る。日本語の理由を 1 行出す案がある。
- （batch B レビュー Minor）格子の行分けに `splitlines` を使っており、U+2028 などでも行が分かれる。`\n` だけで分ける案がある。
- （batch B レビュー Minor）64×64 の格子を拡大率 64 で変換すると、メモリ上に約 67 MB の画素を作る。行ごとに組み立てる案がある。
- （batch B レビュー Minor）同梱アイコンの cloud・people・gear は形が粗い。PO の受け入れで描き直すかを決める。
- （batch C レビュー Minor）表のセルの幅の見積もり（`manuscript.py` の 474 行目付近と 508 行目付近）が、強調の記号 `**` も文字として数えている。安全側に外れるだけだが、記号を除いて数える案がある。
- （batch C レビュー Minor）`5*3 と 2*4` のように単独の `*` が 2 つある文は、対になった `*…*` として拒否される。design.md の規則どおりだが、数式の `*` を許す判定に改める案がある。
- （batch C レビュー Minor）`manuscript.py` に同じ幅の計算式が 2 か所ある。1 つにまとめられる。
- （4.1 レビュー Minor）既定のテンプレートのマスターと 11 のレイアウトが 4:3 のプレースホルダの位置のまま残っている。利用者が PowerPoint でスライドを足すと、プレースホルダが左に寄る。16:9 に合わせて直す案がある。
- （4.1 レビュー Minor）箇条書きの記号の色（`buClr`）を指定しておらず、項目が `**…**` で始まると `・` が強調色になる。記号の色をほぼ黒に固定する案がある。
- （4.1 レビュー Minor）表の空のセルは文字の連なりがなく、大きさと書体の指定（`endParaRPr`）を持たない。表示には影響しない。
- （4.1 再レビュー Minor）一言の文字の色をテストで確かめていない。
- （4.1 再レビュー Minor）原稿の解析と描画が大きさの定義を共有していることを確かめるテストが、名前の有無（`hasattr`）しか見ていない。
- （batch D レビュー Minor）`build.py` の出力先のフォルダがないと、`mkstemp` の `FileNotFoundError` がトレースバックのまま出る。日本語の理由を 1 行出す案がある。
- （batch D レビュー Minor）原稿を読めないときの理由が `<パス>: 原稿を読めません` で、行番号を持たない。spec の書式の外だが妥当。
- （batch D レビュー Minor）`tests/test_build_cli.py` の違反の行数の確認が `>= 2` で弱い。ちょうどの件数で確かめられる。
