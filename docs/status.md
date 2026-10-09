# Current status

Last updated: 2026-10-09 (pixel-art-display-size をアーカイブした). Update this file after every archive.

## Phase

最初の版を公開した。プラグイン `less-is-more-slide`（Skill `slide`、Agent `writer`・`critic`）が `main` にある（PR #4）。ドット絵の表示の大きさをドット数から決める変更（目標 2.4 インチ、1 ドット 0.05〜0.075 インチ、長辺は最大 4.6 インチ、格子の上限 64 の撤廃）も入った（PR #7）。

- 開発のコマンドは `AGENTS.md` のコマンド表にある。
  - テスト: `uv run pytest`
  - lint: `uv run ruff check . && uv run ruff format --check .`
- spec は `openspec/specs/` にある: `slide-generation`、`pixel-art`、`slide-plugin`。

## In progress

なし。

## PO to-dos

- add-slide-plugin の受け入れ: README の手順で、Claude Code と Copilot CLI の両方にマーケットプレイスからプラグインを入れる。`examples/sample.md` から作った PPTX を PowerPoint で開き、はみ出しがないか、「人が作った」ように見えるか、アイコン（cloud・people・gear）を描き直すかを判断する。
- Copilot CLI を 1.0.91 以上に更新し、対話モードでこのリポジトリを信頼して `harness` プラグインを導入する（`.github/copilot/settings.json` 経由）。`copilot plugin list` で `harness` を確かめ、`harness:adopt` の手順 8 の Copilot CLI の検証を行う。
## Next candidates

1. 受け入れで見つかった問題の修正。
2. 同梱アイコン 14 個の描き直し。いまは 16×16 で 1.2 インチに表示される。32×32 以上で描けば 2.4 インチになる（pixel-art-display-size の design.md 合意事項）。
3. add-slide-plugin と pixel-art-display-size の Proposals（`docs/changes.md` の Handed on）からの改善。python-pptx の版の固定、出力のファイルの権限、レイアウトの 16:9 化、テストのコメントの直しなど。
4. ハーネスの `ask-gate.sh` に `uv lock` の規則を足す提案（`docs/harness/lessons.md`）。

## Harness versions

<!-- Filled by harness:adopt and updated on every harness update. -->

| Component | Version |
|---|---|
| agentic-harness | v0.4.0 |
| OpenSpec CLI / skills | 1.14.1（`/opsx:propose`・`archive`・`update`・`sync`、`.agents/skills` に同じ 4 つ） |
| Claude Code | 2.1.295 |
| Copilot CLI | 1.0.90（`harness` プラグインは未導入） |

### 検証結果（`harness:adopt` 手順 8、2026-10-09）

| 項目 | 結果 |
|---|---|
| `rm -rf ./harness-guard-probe` | 拒否された: `BLOCKED by harness guard (rm-rf)` |
| `git push origin main` | PO への確認が出た（`harness ask-gate (protected-push)`）。PO が誤って承認したが、`main` は `origin/main` と同一で、結果は `Everything up-to-date`（送られた変更はない） |
| `/plugin` | `harness@agentic-harness` 0.4.0（project スコープ）が有効 |
| スキル | `harness:design`・`harness:execute` ほか 5 つが表示される。`openspec-*` のスキルはない |
| `.claude/commands/opsx/` | `propose.md`・`archive.md`・`update.md`・`sync.md` のみ |
| エージェント | `harness:implementer`・`harness:reviewer` |
| `.claude/settings.json` | プラグインの導入後も差分なし |
| ruleset | `default-branch` |
| Copilot CLI | 未検証（プラグイン未導入） |
