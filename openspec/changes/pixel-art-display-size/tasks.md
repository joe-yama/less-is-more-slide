Issue: #6

# Tasks

作業場所: worktree `.claude/worktrees/pixel-art-display-size`、ブランチ `feature/pixel-art-display-size`。テスト `uv run pytest`、lint `uv run ruff check . && uv run ruff format --check .`。

## 1. 格子の上限を外す

- [x] 1.1 格子の幅と高さの上限 64 を外し、利用者向けの記述を直す
  - Files: `plugin/skills/slide/scripts/slidekit/grid.py`、`tests/test_grid.py`、`plugin/skills/slide/SKILL.md`（79 行目の「1〜64 × 1〜64」）、`plugin/skills/slide/references/format.md`（「格子ファイル」の「幅と高さは 1〜64」）
  - Test first: `tests/test_grid.py` で、幅 65・高さ 65 を拒否するいまのテストを、幅 200・高さ 150 の格子を 200×150 として受け付けるテストに置き換え、赤になる（design.md「格子の大きさに上限を設けない」）。空の格子の拒否のテストは残す
  - Review: batch A / Risk: none

## 2. 表示の大きさ

- [x] 2.1 ドット数から画像の大きさを決め、PNG の拡大率の下限を 1 にする
  - Files: `plugin/skills/slide/scripts/slidekit/render.py`、`tests/test_render.py`、`plugin/skills/slide/references/format.md`（図の節に、画像の大きさはドット数で決まり、16×16 は 1.2 インチ、32〜48 ドットで 2.4 インチ、長辺は最大 4.6 インチになることを 1〜2 文で書く）
  - Interface: `render.py` の、長辺のドット数を受け取って画像の長辺（インチ）を返す関数と、目標・1 ドットの上下限・長辺の上限の定数（design.md「定数の置き場所」）
  - Test first: `tests/test_render.py` が、delta spec「ドット絵の表示の大きさ」の 7 つのシナリオ（8×8 → 0.6、`icon:gear` → 1.2、32×32 と 40×40 → 2.4、64×64 → 3.2、200×200 → 4.6、32×16 → 2.4×1.2、左右 2 列の `icon:box` → 1.2、いずれもインチで差 2 EMU まで）を、できた PPTX の画像の寸法で確かめて赤になる。PNG の画素数は、いまの `test_picture_alt_text_and_size` の式を `min(64, max(1, ceil(1024 / n)))` に直し、200×200 の格子で 1200 ピクセル四方（拡大率 6）になることも確かめる（design.md「PNG の拡大率の下限を 1 にする」）
  - Review: solo / Risk: ui

- [ ] 2.2 図の説明文を画像の右端に付けて置く
  - Files: `plugin/skills/slide/scripts/slidekit/render.py`、`tests/test_render.py`
  - Test first: `tests/test_render.py` の `test_figure_caption_right_of_picture` を、説明文の枠の左端 = 画像の右端 + 0.5 インチ、上端 = 画像の上端（差 2 EMU まで）を確かめるよう強めて赤になる（delta spec「図の説明文の位置」、design.md「説明文は画像の右端に付いて動く」）
  - Review: solo / Risk: ui

## 3. 確認

- [ ] 3.1 2.1 の大きさのテストと 2.2 の説明文の位置のテストを `harness:mutation-check` で確かめる
  - Verify: 1 ドットの上限 0.075 を 0.15 に変えた複製で 8×8・16×16 のテストが赤になり、長辺の上限 4.6 を外した複製で 200×200 のテストが赤になり、説明文の位置をいまの固定位置に戻した複製で 2.2 のテストが赤になる。変えない複製（対照）では緑。結果を ledger に記す
  - Review: batch A / Risk: none

- [ ] 3.2 すべてのコマンドを通し、見本の PPTX を作る
  - Verify: `uv run pytest` がすべて緑、`uv run ruff check . && uv run ruff format --check .` が通る。`uv run plugin/skills/slide/scripts/build.py examples/sample.md <一時フォルダ>/sample.pptx` が終了コード 0 で、ロボットの画像が 0.6 インチ四方、歯車が 1.2 インチ四方である（python-pptx で読んで確かめる）。PR の本文に、PO が受け入れで PowerPoint で開くファイルの作り方を書く
  - Review: batch A / Risk: none

## シナリオと確認するタスク

- pixel-art「格子ファイルの書式と大きさ」: 正しい格子・知らない文字・行の長さが揃わない → 既存の `tests/test_grid.py`（1.1 で残す）。大きな格子 → 1.1
- slide-generation「ドット絵の表示の大きさ」: 7 つのシナリオすべて → 2.1（3.1 で mutation check）
- slide-generation「図の説明文の位置」: 小さな画像の説明文 → 2.2（3.1 で mutation check）

## 実装中の判断

### 2026-10-09 200×200 の PNG は 1200 ピクセル四方
- Ruling: 2.1 の Test first の「1000 ピクセル四方（拡大率 5）」を「1200 ピクセル四方（拡大率 6）」に直す。design.md の式 `min(64, max(1, ceil(1024 / n)))` を正とする。
- Reason: `ceil(1024 / 200)` は 6 で、5 はタスク文の計算の誤り。式は design.md のルーリングで決めたもので、拡大率 5 では長辺が 1000 ピクセルとなり 1024 ピクセルに届かない。
- Cost if wrong: 200 ドットの格子の PNG が 1 辺 200 ピクセル大きくなるだけで、見た目は変わらない。

## Proposals
