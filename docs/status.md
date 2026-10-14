# Current status

Last updated: 2026-10-14 (add-flow-diagram をアーカイブした). Update this file in the archive commit of every change.

Last retro: 2026-10-14 (v0.5.0 の導入日を起点にした。the periodic retro of `harness:workflow` reads and sets this line).

This file holds the current state only, no history: replace lines, do not append. History is in `openspec/changes/archive/` (grep it), rulings in each change's `design.md`. Budget: 20,000 bytes (about 5k tokens), read at the start of every design and implementation session; CI warns above it.

## Phase

最初の版を公開した。プラグイン `less-is-more-slide`（Skill `slide`、Agent `writer`・`critic`）が `main` にある（PR #4）。ドット絵の表示の大きさをドット数から決める変更（目標 2.4 インチ、1 ドット 0.05〜0.075 インチ、長辺は最大 4.6 インチ、格子の上限 64 の撤廃）も入った（PR #7）。英語の本文に日本語などの「添え訳」をつける書式（`^ ` の行、本文の 60% の大きさ、色 `#767676`）も入った（PR #10）。構成図ファイル（`.flow`）から箱・範囲の枠・矢印の構成図を描く書式が入り、図と左右 2 列のレイアウトから参照できる。範囲の枠の色 `#BDBDBD` が加わり、プラグインの版は 0.3.0 になった（PR #16）。

- 開発のコマンドは `AGENTS.md` のコマンド表にある。
  - テスト: `uv run pytest`
  - lint: `uv run ruff check . && uv run ruff format --check .`
- spec は `openspec/specs/` にある: `slide-generation`、`pixel-art`、`slide-plugin`、`flow-diagram`。

## In progress

なし。

## PO to-dos

- add-slide-plugin の受け入れ: README の手順で、Claude Code と Copilot CLI の両方にマーケットプレイスからプラグインを入れる。`examples/sample.md` から作った PPTX を PowerPoint で開き、はみ出しがないか、「人が作った」ように見えるか、アイコン（cloud・people・gear）を描き直すかを判断する。
- add-gloss の受け入れ（PR #10 の本文に手順）: `examples/bilingual.md` から作った PPTX を PowerPoint で開き、見出しと添え訳が重ならないか、添え訳の灰色が投影で読めるか、表の 11pt が投影で読めるかを見る。添え訳のない `examples/sample.md` の見た目が変わらないことも確かめる。
- add-flow-diagram の受け入れ（PR #16 はマージ済み）: `examples/design-review.md` から作った PPTX を PowerPoint で開き、7 つの構成図が人が作ったように見えるか、ラベルや線が重ならないかを見る。7 つの図は設計の対話の図の中身が残っていなかったため、spec の Scenario から組み立てた（[design.md](../openspec/changes/archive/2026-10-14-add-flow-diagram/design.md) の「設計の対話の 7 つの図は spec の Scenario から組み立てる」）。設計の対話の図と違えば、`.flow` の中身を渡す。
- Copilot CLI の対話モードで `harness:adopt` の手順 8 の検証を行う（プラグイン v0.5.0 は導入済み。手で登録したマーケットプレイスは版を固定していない）。
## Next candidates

1. 受け入れで見つかった問題の修正。
2. 表・一言・中扉の拡張（`extend-table-statement-section`。add-flow-diagram の見本の原稿にスライドを足す）。
3. 構成図の配置の限界の扱い: 1 つの箱から 3 つに分かれる形の水平な矢印にラベルを付けられない（D6/D7）、1 列空けた直線の × の文は 2 文字以上だと置けない（add-flow-diagram の最終レビューの Minor）。
4. 同梱アイコン 14 個を 32×32 以上で描き直す（[pixel-art-display-size の design.md](../openspec/changes/archive/2026-10-09-pixel-art-display-size/design.md) の合意事項）。
5. 過去の変更の Proposals からの改善（[`docs/changes.md`](changes.md) の Handed on。凍結した履歴で、追記はしない）。
6. ハーネスの `ask-gate.sh` に `uv lock` の規則を足す提案（[`docs/harness/lessons.md`](harness/lessons.md)）。

## Harness versions

<!-- Filled by harness:adopt and updated on every harness update. -->

| Component | Version |
|---|---|
| agentic-harness | v0.5.0 |
| OpenSpec CLI / skills | 1.14.1（`/opsx:propose`・`archive`・`update`・`sync`、`.agents/skills` に同じ 4 つ） |
| Claude Code | 2.1.299 |
| Copilot CLI | 1.0.94（`harness@agentic-harness` v0.5.0。マーケットプレイスは手で登録したもので、版を固定していない） |

### 検証結果（`harness:adopt` 手順 8、2026-10-14、v0.5.0）

| 項目 | 結果 |
|---|---|
| `rm -rf ./harness-guard-probe` | 拒否された: `BLOCKED by harness guard (rm-rf)`（0.5.0 の `guard.sh`） |
| `git push origin main` | 確認が出て、PO が拒否した |
| プラグイン | `harness@agentic-harness` 0.5.0（project スコープ）が有効 |
| スキル | `adopt`・`design`・`execute`・`mutation-check`・`workflow` の 5 つ。`.claude/skills` はない（`openspec-*` のスキルはない） |
| `.claude/commands/opsx/` | `propose.md`・`archive.md`・`update.md`・`sync.md` のみ |
| エージェント | `harness:implementer`・`harness:reviewer-intermediate`・`harness:reviewer` |
| `.claude/settings.json` | プラグインの更新後も差分なし |
| ruleset | `default-branch` |
| Copilot CLI | `copilot plugin list` で v0.5.0 を確認。対話モードでの検証は未実施 |

更新の注意: `claude plugin update` の前に、ユーザー側に登録されたマーケットプレイスの ref を新しいタグに付け替える（`claude plugin marketplace add 'joe-yama/agentic-harness@<tag>'`）。プロジェクトの `.claude/settings.json` の ref を変えるだけでは、登録済みのものは古いタグのまま。
