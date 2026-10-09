# Proposal

## Why

AI に作らせたスライドは、紫や青のグラデーション、色数の多いカード、絵文字、何でも 3 つの箇条書きといった「AI っぽさ」ですぐにそれと分かる。このリポジトリは "Less is more" を原則に、見た人が「人が作った」と信じるスライドを Claude Code と GitHub Copilot で作れる道具を、プラグインとして公開する。リポジトリにはまだ何もないため、最初の変更で道具一式を作る。

## What Changes

- **スライド生成器**を新設する。エージェントは Markdown の部分集合で書いた原稿だけを用意し、生成器が固定の配色（白地・ほぼ黒の文字・灰色・強調色 1 色）、固定の書体（メイリオ）、6 種のレイアウト（表紙、一言、箇条書き、図、表、左右 2 列）で PPTX を作る。グラデーション、影、装飾図形は指定する手段そのものを持たない。
- 生成器は、機械的に判定できる規則違反（絵文字、項目数の超過、枠からのはみ出し、未対応の書式、強調の多用など）を見つけたら、原稿の行番号と理由を出して**生成を拒否**する。
- **ドット絵ツール**を新設する。文字の格子で描いた絵を、スライドと同じ配色の PNG に変換する。よく使うアイコンの格子を同梱し、原稿から名前で参照できる。
- **プラグイン**（Claude Code と Copilot CLI の両対応）として、Skill 1 つと Agent 2 つ（原稿を書いて PPTX まで作る作成役、文章と構成の AI っぽさを別文脈で指摘する点検役）を公開する。
- 開発基盤（Python / uv、pytest、ruff、CI の job `check` の手順、`AGENTS.md` のコマンド表）を整える。

## Capabilities

### New Capabilities

- `slide-generation`: 原稿の書式、レイアウト、配色と書体、規則違反の拒否、PPTX の出力。
- `pixel-art`: 文字の格子から PNG への変換と、同梱アイコン。
- `slide-plugin`: Skill と 2 つの Agent、プラグインとしての配布、利用者向けの導入手順。

### Modified Capabilities

なし。

## Impact

- 新規: `plugin/`（プラグイン本体: Skill、scripts、アイコン、Agent）、`.claude-plugin/marketplace.json`、`tests/`、`examples/`、`pyproject.toml`、`uv.lock`、`README.md`、`LICENSE`。
- 変更: `.github/workflows/ci.yml`（job `check` に手順を追加、job 名は変えない）、`AGENTS.md`（コマンド表）、`.claude/settings.json` と `.harness/env.json`（PO が配置する）、`docs/status.md`。
- 依存: python-pptx（利用者の実行時）、pytest と ruff（開発時のみ）。利用者に必要なのは uv だけになる。
- 対象外: HTML / PDF / Marp での出力、グラフ、コード片、発表者ノート、PPTX から画像へのプレビュー描画、ブラウザの描画エディタ、`gh skill install` での単体配布、マーケットプレイスへの登録。
