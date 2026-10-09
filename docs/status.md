# Current status

Last updated: 2026-10-09 (agentic-harness v0.4.0 を導入した). Update this file after every archive.

## Phase

設計前（ハーネスの導入のみ完了）。

## In progress

なし。

## PO to-dos

- Copilot CLI を 1.0.91 以上に更新し、対話モードでこのリポジトリを信頼して `harness` プラグインを導入する（`.github/copilot/settings.json` 経由）。`copilot plugin list` で `harness` を確かめ、`harness:adopt` の手順 8 の Copilot CLI の検証を行う。
- ask-gate の確認を、bypass permissions 以外のモード（default または auto）で一度確かめる。`git push origin main` で `harness ask-gate (protected-push)` の確認が出れば拒否する。

## Next candidates

1. スライド作成用の Skill と Agent、プラグインとしての公開（`harness:design` で設計する）。

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
| `git push origin main` | ask-gate は `permissionDecision: ask`（`harness ask-gate (protected-push)`）を返した。ただしセッションが bypass permissions モードだったため確認は出ずに実行された（`main` は `origin/main` と同一で、送られた変更はない）。hook のスクリプトに同じ入力を渡して判定を確認した |
| `/plugin` | `harness@agentic-harness` 0.4.0（project スコープ）が有効 |
| スキル | `harness:design`・`harness:execute` ほか 5 つが表示される。`openspec-*` のスキルはない |
| `.claude/commands/opsx/` | `propose.md`・`archive.md`・`update.md`・`sync.md` のみ |
| エージェント | `harness:implementer`・`harness:reviewer` |
| `.claude/settings.json` | プラグインの導入後も差分なし |
| ruleset | `default-branch` |
| Copilot CLI | 未検証（プラグイン未導入） |
