# Lessons

Read this when tests or CI fail in an unexpected way, when writing a new guardian test, or when touching CI.

## 1. Defects that only real data or real processes showed

<!-- For each: the change, what broke, why the unit tests could not see it, and the fix. -->

- **add-slide-plugin: 行数の上限内でも、スライドの下にはみ出した。** 箇条書き 5 項目×2 行と表 7 行×2 行は、要素ごとの行数の上限に収まっていた。それでも PowerPoint で開くと、枠とスライドの下端を越えた。テストは要素ごとの行数しか見ておらず、メイリオの行の高さ（1.5em）を足し合わせた高さを誰も計算していなかった。最終レビューが寸法を計算し、PowerPoint で開いて確かめた。スライドごとの高さの判定を足して直した（design.md「枠の高さも判定する」）。
- **add-slide-plugin: Agent がプラグインの外から `writing.md` を探していた。** Agent は作業フォルダを起点に `Glob` で探していたが、マーケットプレイスから入れたプラグインは利用者のプロジェクトの外に置かれる。リポジトリの中で動かすと、同じ名前のファイルが見つかって成功してしまう。Skill がフォルダの絶対パスを渡す形に直し、実機の確認（6.2）はリポジトリの外のフォルダで行った。

## 1a. Harness and environment surprises

- `uv lock` は、`HARNESS_*` を `.claude/settings.json` に置く前に実行したため、lockfile を変える導入の確認が出ずに通った。PO が後から承認した。スタックを入れる最初の変更では、設定を置くタスクを lockfile の作成より先に行う。
- サブエージェントの `git commit` が 1Password の署名で失敗した（`failed to fill whole buffer`）。再試行せずにステージしたまま止め、PO が `! git commit` で通した。
- 実装役が、約 20 KB の `manuscript.py` を書き直す途中で 15 分間何も出さずに止まり、2 度続いた。新しい実装役に、小さな Edit で直すことと、コマンドに時間制限を付けることを指示すると止まらなかった。
- 変異確認で同じ秒のうちに壊して戻すと、古い `.pyc` が残り、元に戻した後もテストが赤のままに見えた。`PYTHONDONTWRITEBYTECODE=1` で防げる。
- PowerPoint for Mac を AppleScript で操作して PNG に書き出すと、社内の秘密度ラベルの確認で止まり、タイムアウトした。開いて画面を撮るだけなら動く。
- CI の workflow は `pull_request` と `main` への push でしか動かない。feature ブランチの push だけでは job `check` の結果が出ず、PR を開いて初めて CI の証拠が得られる。

## 2. Green is not guardian

<!-- For each: the test that stayed green under a mutation, why it did, and how it was fixed. -->
