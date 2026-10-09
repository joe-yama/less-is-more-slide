# Changes and rulings

The history of changes and the rulings made during them, newest first. The OpenSpec archive (`openspec/changes/archive/`) holds the artifacts; this file holds what a later change needs to know: what was decided on the PO's behalf and what was handed on.

## Entry format

```
## <change-name> (Issue #<n>, PR #<n>, <date>)

### <date> <ruling title>
- Ruling: <what was decided>
- Reason: <why, with the spec section or evidence>
- Cost if wrong: <what breaks and how it would be noticed>

Handed on: <Minor findings and proposals left for later, and where they are listed>
```

## add-slide-plugin (Issue #3, PR #4, 2026-10-09)

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

### 2026-10-09 枠の高さも判定する
- Ruling: 行数の上限に加えて、スライドごとに文字の高さの合計を枠の高さと比べ、収まらない原稿を拒否する。高さは「行数 × 文字の大きさ × 1.5 ÷ 72 インチ」（メイリオの行の高さ 1.5em）と項目の間の余白の合計とし、枠の高さと係数 1.5 は `fit.py` の `PT_*` の隣に置いて `render.py` と共有する。表紙の画像の行も拒否する。
- Reason: 最終レビューで、箇条書き 5 項目×2 行と表 7 行×2 行が、どちらも行数の上限内なのに枠とスライドの下端を越えると分かった（PowerPoint で開いて確かめた）。spec「枠からのはみ出しの拒否」は収まらない原稿の拒否を求めており、行数だけでは守れない。上限の数を下げる案より、内容の短い項目を多く書ける余地が残る。
- Cost if wrong: 高さの見積もりが実際より大きいと、収まる原稿まで拒否される。PO の受け入れで見本を開いて分かれば、係数を調整する。

### 2026-10-09 6.2 の実機確認はリポジトリの外で行う
- Ruling: 作成役と点検役の実機確認は、リポジトリの外の作業フォルダで行う。点検役の「5 種のうち 4 種以上」は、仕込んだ 2・3・4・7・12 番だけで数える。Copilot CLI で Agent が見えなければ `.agent.md` への名前の変更を試す（結果は不要だった）。
- Reason: リポジトリの中で動かすと、プラグインの外にある同じ名前のファイルが見つかり、マーケットプレイスから入れた状態を確かめられない（batch E レビュー）。
- Cost if wrong: マーケットプレイスから入れた環境でだけ起きる欠陥を見逃す。PO の受け入れで README の手順で入れて分かる。

Handed on: レビューの Minor 指摘と提案 31 件。アーカイブした `tasks.md` の Proposals（`openspec/changes/archive/2026-10-09-add-slide-plugin/tasks.md`）にある。主なものは次のとおり。
- python-pptx の版を `<2` に絞る（内部の API を使っているため）。
- 出力のファイルの権限が 0600 になる。
- 出力先のフォルダがないとトレースバックが出る（`build.py`・`pixel.py`）。
- 既定のテンプレートのレイアウトが 4:3 のまま残っている。
- cloud・people・gear のアイコンが粗い。
- Copilot CLI の点検役が引用を縮めることがある。

