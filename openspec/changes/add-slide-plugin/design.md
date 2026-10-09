# Design

## Context

リポジトリにはハーネスしかなく、言語もテストの仕組みもまだない（`docs/status.md`）。動機と範囲は proposal.md、振る舞いは 3 つの delta spec を参照。PO と 2026-10-09 の設計対話で合意した事項は「合意事項」に 1 行ずつ記す。

## Goals / Non-Goals

**Goals:**

- 見た目の自由度を生成器が奪うことで、装飾が「入らない」ではなく「入れられない」状態を作る。
- 機械的に判定できる規則はテストで守り、判定できない文章の癖は点検役 Agent に任せる。

**Non-Goals:**

- PPTX を画像に描画して目で確かめる仕組み（LibreOffice 等）。はみ出しは文字幅の見積もりで防ぐ。
- 原稿から配色・書体・大きさを変える手段。テーマの切り替え。
- 発表者ノート、番号付きリスト、グラフ、コード片、写真。

## 合意事項（2026-10-09 設計対話、PO 回答）

- 出力は PPTX（python-pptx）。
- エージェントは原稿だけを書き、制約付きの生成器が PPTX を作る。
- 配色は白地・ほぼ黒・灰色・強調色 1 色の固定。
- 書体はメイリオに固定。
- ドット絵は文字の格子 → PNG、加えて既製アイコン集を同梱する。
- 配布は Skill ＋ Agent のプラグイン（Claude Code と Copilot CLI）。
- Agent は作成役と点検役の 2 つ。
- レイアウトは表紙・一言・箇条書き・図に、表と左右 2 列を加えた 6 種。
- 規則違反は生成を拒否する。
- 実行は `uv run`（PEP 723 のインライン依存）。

## Decisions

### ファイル配置

```
.claude-plugin/marketplace.json          マーケットプレイス（プラグイン 1 つ、source は ./plugin）
plugin/.claude-plugin/plugin.json        プラグインのマニフェスト（name: less-is-more-slide）
plugin/skills/slide/SKILL.md             Skill 本体（手順と最短の書式）
plugin/skills/slide/references/format.md 原稿の書式の全容（6 レイアウト、強調、画像、制限値）
plugin/skills/slide/references/writing.md 書き方の規則と AI っぽさの一覧（作成役と点検役が共有）
plugin/skills/slide/scripts/build.py     生成器の CLI（PEP 723: python-pptx）
plugin/skills/slide/scripts/pixel.py     ドット絵の CLI（標準ライブラリだけ）
plugin/skills/slide/scripts/slidekit/    共通モジュール（下記 Interface）
plugin/skills/slide/icons/<name>.txt     同梱アイコン 14 個
plugin/agents/writer.md, critic.md       2 つの Agent
examples/sample.md, examples/robot.txt   見本原稿（6 レイアウトすべて、格子ファイルの参照を含む）
tests/                                   pytest
pyproject.toml, uv.lock                  開発用（依存グループ dev: python-pptx, pytest, ruff）
README.md, LICENSE                       利用者向けの説明、MIT
```

プラグインをリポジトリ直下ではなく `plugin/` に置くのは、直下の `.claude/` や `AGENTS.md` などハーネスのファイルを利用者に配らないため。

### モジュールの境界

- `slidekit/palette.py`: 4 色の定数と、格子の文字 → 色の対応。色を書くのはここだけ。
- `slidekit/grid.py`: 格子の解析・検証、アイコンの解決（`icon:<name>` と相対パス）。
- `slidekit/png.py`: 格子 → PNG のバイト列（`zlib` と `struct` だけで RGBA、フィルタなし）。
- `slidekit/fit.py`: 文字幅の見積もりと行数。
- `slidekit/manuscript.py`: 原稿の解析と全規則の検証。違反はすべて集めてから例外にする（最初の 1 件で止めない）。
- `slidekit/render.py`: 検証済みの原稿 → PPTX。ここでは検証しない。
- `build.py` / `pixel.py`: 引数の解釈、エラーの出力、終了コード。`sys.path` に自分のフォルダを足して `slidekit` を読む（PEP 723 のスクリプトは単体ファイルとして実行されるため）。

### 寸法と文字の大きさ

画面は 13.333 × 7.5 インチ。左右の余白 0.9 インチ、上の余白 0.6 インチ。本文領域の幅は 11.53 インチ。

| 要素 | 大きさ | 色 | 行数の上限 | 枠の幅 |
|---|---|---|---|---|
| 表紙のタイトル | 40pt | ほぼ黒 | 2 | 本文領域 |
| 表紙の文（各行） | 20pt | 灰色 | 1 | 本文領域 |
| 見出し | 30pt | ほぼ黒 | 1 | 本文領域 |
| 一言 | 40pt | ほぼ黒 | 3 | 本文領域 |
| 箇条書きの項目 | 24pt | ほぼ黒 | 2 | 本文領域から字下げ 0.4 インチを引いた幅 |
| 図の説明文 | 20pt | ほぼ黒 | 3 | 5.2 インチ（画像の右） |
| 表のセル | 18pt | ほぼ黒（見出し行は灰色） | 2 | 本文領域 ÷ 列数 − 0.2 インチ |
| 2 列の箇条書き項目 | 22pt | ほぼ黒 | 2 | 5.5 インチ − 0.4 インチ |
| 2 列の文 | 22pt | ほぼ黒 | 3 | 5.5 インチ |
| ページ番号 | 12pt | 灰色 | — | 右下 |

- 文字幅の見積もり: `unicodedata.east_asian_width` が `W` か `F` の文字は 1.0em、それ以外は 0.6em（メイリオの半角は約 0.55em。安全側に寄せる）。行数は「合計幅 ÷ 枠の幅（em）」の切り上げ。和文はどこでも折り返せるので語単位の折り返しは考えない。
- 箇条書きの記号は `・`（PowerPoint の箇条書き書式で付け、本文の文字にはしない）。
- 縦位置: 見出しは上端から 0.6 インチ、本文は 1.8 インチから。一言は縦の中央。左右 2 列は列幅 5.5 インチ、間 0.53 インチ。
- 図: 画像は本文領域の左、最大 4.6 インチ四方に縦横比を保って収める。説明文は画像の右。
- 画像の埋め込み: 整数の拡大率 `min(64, max(16, ceil(1024 / 長辺のドット数)))` で PNG を作る。長辺が 16 ドット以上なら 1024 ピクセル以上になり、それより小さい格子は上限 64 で止まる（8 ドットなら 512 ピクセル）。PowerPoint が拡大するときのにじみを目立たなくするため。

### PowerPoint 文書としての作り

- python-pptx の既定テンプレートを使い、画面の大きさを 16:9 に設定する。見出しのあるスライドと表紙は「タイトルのみ」レイアウトのタイトルプレースホルダに見出しを入れ、位置・大きさ・書式は明示的に指定する。一言は「白紙」レイアウトに文字の枠を置く。使わないプレースホルダは消す。
- テーマ（`ppt/theme/theme1.xml`）の見出し・本文の書体を、欧文・和文ともメイリオに書き換える。利用者が後から足した文字もメイリオになる。
- すべての文字の段落で書体（`latin` と `ea`）・大きさ・色を明示する。テーマ色には頼らない。
- 表は表スタイルを「スタイルなし、表のグリッドなし」（`{2D5ABB26-0587-4C30-8999-92F81FD0307C}`）にし、先頭行・縞模様の指定を外し、見出し行の下辺と最終行の下辺だけに灰色 1pt の線を引く。セルの塗りはなし。
- 文書のプロパティ: タイトル＝表紙のタイトル。作成者・最終更新者・件名・キーワード・説明・分類は空。作成日時と更新日時は生成した時刻。`docProps/` のどの部品にも `python-pptx` の文字を残さない。
- 画像の代替テキストは `![説明](...)` の説明。

### 原稿の解析

- スライドの判定は spec の順（表紙 → 一言 → 箇条書き → 図 → 表 → 2 列 → どれでもなければ拒否）。2 列は `|||` の行があることで判定する。
- 強調は `**…**` だけを受け付ける。拒否する書式: 行頭の `###`〜`######`、`>`、`数字.`、` ``` `、`<` で始まる HTML、インラインの `` ` ``、`[…](…)`、`__…__`、`~~…~~`、対になった `*…*`。対にならない単独の `*`（例: `5*3`）は文字として扱う。
- 絵文字は Unicode 15.1 の `emoji-data.txt` の Extended_Pictographic の範囲を表として持ち、U+FE0F と合わせて判定する。エラーにはその文字と符号位置（`U+1F680` など）を出す。
- エラーの書式: `<コマンドに渡された原稿のパス>:<行番号>: <理由>`。格子ファイルの違反を図の参照から見つけた場合は、参照した原稿の行番号を使い、理由に格子ファイルのパスと格子の行・文字の位置を含める。

### Interface（テストと他タスクが使う名前）

- `slidekit.palette`: `PAPER = "FFFFFF"`, `INK = "1A1A1A"`, `GRAY = "6B6B6B"`, `ACCENT = "B23A2E"`, `GRID_COLORS: dict[str, str | None]`（`.` は `None`）。
- `slidekit.grid`: `Problem(line: int, col: int | None, message: str)`、`GridError(Exception)`（`.problems: list[Problem]`）、`Grid(width: int, height: int, rows: list[str])`、`parse_grid(text: str) -> Grid`、`icon_names() -> list[str]`、`resolve(ref: str, base_dir: Path) -> Grid`。
- `slidekit.png`: `encode_png(grid: Grid, scale: int) -> bytes`。
- `slidekit.fit`: `text_width_em(text: str) -> float`、`line_count(text: str, font_pt: float, box_width_in: float) -> int`。
- `slidekit.manuscript`: `ManuscriptError(Exception)`（`.problems: list[Problem]`、`Problem` は grid と共用）、`parse(text: str, base_dir: Path) -> Deck`。`Deck` と各スライドの型は実装が決める（render だけが使う）。
- `slidekit.render`: `render(deck: Deck, out_path: Path) -> None`。
- `build.py`: `main(argv: list[str]) -> int`。使い方 `build.py <原稿.md> -o <出力.pptx>`。出力は一時ファイルに書いてから置き換える。
- `pixel.py`: `main(argv: list[str]) -> int`。使い方 `pixel.py <格子.txt | icon:名前> -o <出力.png> [--scale N]`、`pixel.py --list`。
- Skill に書くコマンドの形: `uv run <Skill のフォルダ>/scripts/build.py <原稿.md> -o <出力.pptx>`。

### Agent

- `writer`: tools は Read, Write, Edit, Bash, Glob, Grep。frontmatter で Skill `slide` を読み込み、本文でも「Skill `slide` を読み、`references/format.md` と `references/writing.md` に従う」と書く。原稿は利用者が指定した場所（指定がなければ作業フォルダ）に `<主題>.md` として置き、PPTX を同じ名前で隣に作る。
- `critic`: tools は Read, Glob, Grep だけ。`references/writing.md` の一覧の項目番号で指摘する。返答の形は「スライド番号 / 引用 / 規則の番号と名前 / 書き直しの案」の表。
- Skill の手順: 主題・聞き手・枚数・材料を確かめる → 作成役 → 点検役 → 指摘があれば作成役に戻す（点検は最大 2 回）→ パスを報告。サブエージェントを使えない環境では、同じ手順を自分で行う。

### AI っぽさの一覧（`references/writing.md` の骨子）

1. 絵文字・装飾記号（✨ ✅ 🚀、【】や ▶ の多用）
2. 誇張語・決まり文句（「〜を実現」「革新的」「シームレス」「包括的」「次世代」「新たな地平」「鍵となる」）
3. 何でも 3 つ（3 項目の箇条書きや 3 つの形容詞の並びが続く）
4. コロン見出しと疑問形見出しの多用（「X：Y で実現する Z」「なぜ〜なのか？」）
5. 揃いすぎ（全項目が同じ長さ・同じ文型・すべて体言止め）
6. 具体のなさ（数字・固有名詞・日付がない言い切り）
7. 定型のスライド（「本日のアジェンダ」「まとめ」「ご清聴ありがとうございました」「Q&A」）
8. 対比の決まり型（「〜だけでなく〜も」「〜ではなく〜だ」の連発）
9. 強調の乱用と詰め込み（1 枚に複数の主張）
10. 飾りの図（内容を説明しないアイコン）
11. カタカナ語の乱用（ソリューション、インサイト、エンパワー、レバレッジ）
12. 前置きと決まった言い回し（「〜について見ていきましょう」「重要なのは〜です」）

書き方の規則（前向きの規則）: 1 枚 1 主張、見出しは結論の文、具体の数字と固有名詞、項目数は内容で決める（2 でも 4 でもよい）、社内で普段使う言葉で書く。

### 開発の仕組み

- `pyproject.toml`: `requires-python = ">=3.11"`、依存グループ `dev` に python-pptx・pytest・ruff。pytest の `pythonpath` に `plugin/skills/slide/scripts` を入れる。ruff の対象は `plugin/` と `tests/`、行の長さ 100。
- コマンド: テスト `uv run pytest`、lint（1 ファイル）`uv run ruff check`、全体の lint `uv run ruff check . && uv run ruff format --check .`。
- CI の job `check` に、uv の導入（`astral-sh/setup-uv` を SHA で固定）、`uv sync --locked`、全体の lint、`uv run pytest`、開発環境を使わない見本の生成（`uv run --no-project plugin/skills/slide/scripts/build.py examples/sample.md -o <一時ファイル>`）を足す。job 名は変えない。

### 新しい依存（PO への提示）

| 依存 | 目的 | ライセンス | 保守状況 |
|---|---|---|---|
| python-pptx | PPTX の生成（利用者の実行時にも uv が入れる） | MIT | 1.0 系が継続して公開されている |
| pytest | テスト（開発時のみ） | MIT | 活発 |
| ruff | lint と整形（開発時のみ） | MIT | 活発（Astral） |
| astral-sh/setup-uv | CI で uv を入れる | MIT | 活発（Astral） |

`uv.lock` の作成は lockfile を変える導入なので PO に回る。

## Rulings

### 2026-10-09 プラグインは `plugin/` に置く
- Ruling: プラグイン本体を `plugin/` に置き、直下の `.claude-plugin/marketplace.json` から `./plugin` を参照する。
- Reason: 直下に置くとハーネスの `.claude/` などが配布物と混ざる。Claude Code と Copilot CLI はどちらも `.claude-plugin/` 形式のマーケットプレイスを読む（このリポジトリが使う agentic-harness が同じ形で両方に入っている）。
- Cost if wrong: Copilot CLI がサブフォルダの source を読めなければ導入できない。タスク 6.2 の実機確認で分かる。

### 2026-10-09 表紙の文の役割を決めない
- Ruling: 表紙の 0〜3 行の文は、副題・名前・日付を区別せずに同じ書式で並べる。文書の作成者のプロパティは空にする。
- Reason: 役割を区別すると原稿の書式が増える。spec は作成者に生成ツールの名前を残さないことだけを求めている。
- Cost if wrong: 作成者欄が空の PPTX を不自然と感じる人がいる。PO の受け入れで分かれば、作成者を原稿で指定する変更を出す。

### 2026-10-09 見出しと文だけのスライドは作れない
- Ruling: `## 見出し` ＋ 1 行の文は 6 種のどれでもないので拒否し、一言か箇条書きを勧める。
- Reason: PO が選んだレイアウトは 6 種で、増やすのは spec の変更になる。
- Cost if wrong: よくある形が書けず、作成役が 1 項目の箇条書きで代用する。点検役の指摘や PO の試用で分かる。

### 2026-10-09 ライセンスは MIT
- Ruling: `LICENSE` は MIT、著作者は joe-yama。
- Reason: 公開するプラグインにはライセンスが要る。PO の agentic-harness と揃える。
- Cost if wrong: 別のライセンスにしたい場合は公開前に差し替える。PR の確認で分かる。

### 2026-10-09 ハーネスの設定は PO が置く
- Ruling: `HARNESS_LINT_CMD`・`HARNESS_LINT_PATTERN`・`HARNESS_TEST_CMD` の値は実装役がスクラッチパッドに書き、`.claude/settings.json` と `.harness/env.json` への配置は PO が行う（タスク 1.3）。
- Reason: `CLAUDE.md` と `AGENTS.md` が、エージェントによるこれらのファイルの変更を禁じている。
- Cost if wrong: 配置されるまで編集ごとの lint と終了前のテストが動かない。CI の job `check` は動くので欠陥は PR で止まる。

### 2026-10-09 小さな格子の画像は 1024 ピクセルに届かなくてよい
- Ruling: 画像の拡大率は式 `min(64, max(16, ceil(1024 / 長辺のドット数)))` のとおりとし、長辺が 15 ドット以下の格子は 1024 ピクセル未満で埋め込む（8 ドットなら 512 ピクセル）。「画像の埋め込み」の文をこの式に合わせて直した。
- Reason: 元の文は「1024 ピクセル以上」と「上限 64」を同時に求めていて、15 ドット以下では両立しない。上限は pixel-art spec の拡大率の範囲（1〜64）と揃っている。にじみは画素が大きいほど目立たず、512 ピクセルでも 1 ドットが 64 画素四方になる。
- Cost if wrong: 小さな格子を大きく表示したときに輪郭がにじむ。PO の受け入れで PowerPoint で見て分かれば、上限を外す変更を出す。

## Risks / Trade-offs

- [文字幅の見積もりが実際の描画とずれ、PowerPoint ではみ出す] → 半角を 0.6em と安全側に見積もり、6.3 で見本を PowerPoint と Keynote で開いて PO が確かめる。
- [Copilot CLI が Agent の `tools` や Skill の読み込みを Claude Code と同じに扱わない] → 両方の CLI での実機確認を 6.2 に置く。点検役の本文にも「ファイルを書き換えない」と書く。
- [Extended_Pictographic に `©` `↔` など普通の記号が含まれ、拒否される] → 規則どおり拒否し、エラーに符号位置を出す。困る記号が見つかれば spec の変更で例外を足す。
- [AI っぽさは文章の判定で、点検役の精度は保証できない] → 一覧を具体的な語と型で書き、6.2 で仕込んだ原稿を使って確かめる。
