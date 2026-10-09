# less-is-more-slide

Claude Code と GitHub Copilot CLI で、人が作ったように見える装飾のないスライド（PPTX）を作るプラグイン。

エージェントは原稿（Markdown の部分集合）だけを書き、制約付きの生成器が PPTX を作る。配色（白地・ほぼ黒・灰色・強調色 1 色）と書体（メイリオ）は固定で、装飾は入れられない。絵文字や枠からのはみ出しなど、規則に反する原稿は生成器が拒否する。

含まれるもの:

- Skill `slide`: 原稿の書式、生成器とドット絵ツール、書き方の規則（AI っぽさの一覧を含む）
- Agent `writer`: 主題と材料から原稿を書き、PPTX を作る
- Agent `critic`: 原稿を読むだけで、AI っぽさを指摘する

## 必要なもの

[uv](https://docs.astral.sh/uv/) が必要。生成器は uv が依存（python-pptx）を自動で入れて動かすので、ほかに手で入れるものはない。

## 導入

### Claude Code

```sh
claude plugin marketplace add joe-yama/less-is-more-slide
claude plugin install less-is-more-slide@less-is-more-slide
```

セッションの中なら `/plugin marketplace add joe-yama/less-is-more-slide` と `/plugin install less-is-more-slide@less-is-more-slide` でもよい。導入すると Skill `less-is-more-slide:slide` と Agent `less-is-more-slide:writer`、`less-is-more-slide:critic` が使える。

### GitHub Copilot CLI

```sh
copilot plugin marketplace add joe-yama/less-is-more-slide
copilot plugin install less-is-more-slide@less-is-more-slide
```

`copilot plugin list` に `less-is-more-slide` が出れば導入できている。

## 使い方

エージェントに主題と材料を渡して、スライドを頼む。たとえば次のように言う。

```text
slide Skill で、夜間バッチの移行報告のスライドを作って。材料は次の 3 行。
```

作成役が原稿（`.md`）と PPTX を作り、そのパスを返す。点検役に原稿を読ませると、AI っぽい箇所をスライド番号・引用・書き直しの案つきで指摘する。

生成器は単独でも使える。原稿から PPTX を作る最短の例:

```sh
uv run plugin/skills/slide/scripts/build.py examples/sample.md -o sample.pptx
```

## 見本

`examples/sample.md` は、表紙・一言・箇条書き・図・表・左右 2 列の 6 種のレイアウトをすべて使った見本の原稿。`examples/robot.txt` は、図から参照する格子ファイル（ドット絵）。

書式の全容は `plugin/skills/slide/references/format.md`、書き方の規則は `plugin/skills/slide/references/writing.md` を参照。

## ライセンス

MIT（`LICENSE`）。
