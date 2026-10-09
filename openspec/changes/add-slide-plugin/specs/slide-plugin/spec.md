# Spec Delta

## Purpose

スライド生成器とドット絵ツールを、Claude Code と GitHub Copilot CLI の利用者が 1 つのプラグインとして導入し、Skill と 2 つの Agent（作成役と点検役）で「人が作った」と信じられるスライドを作れるようにする。

## ADDED Requirements

### Requirement: プラグインとしての配布
このリポジトリは、プラグイン `less-is-more-slide` を 1 つだけ載せたマーケットプレイスとして、Claude Code と Copilot CLI の両方から導入できなければならない SHALL。プラグインは Skill `slide`、Agent `writer`、Agent `critic` を持つ SHALL。

#### Scenario: マニフェスト
- **WHEN** マーケットプレイスとプラグインのマニフェストを読む
- **THEN** どちらも JSON として正しく、マーケットプレイスはプラグイン `less-is-more-slide` を 1 つだけ載せ、プラグインには名前・版・説明・ライセンスがある

#### Scenario: Claude Code に導入する
- **WHEN** Claude Code でこのリポジトリをマーケットプレイスとして追加し、プラグインを導入する
- **THEN** Skill `less-is-more-slide:slide` と Agent `less-is-more-slide:writer`、`less-is-more-slide:critic` が使える

#### Scenario: Copilot CLI に導入する
- **WHEN** Copilot CLI でこのリポジトリからプラグインを導入する
- **THEN** `copilot plugin list` に `less-is-more-slide` が出て、Skill `slide` と 2 つの Agent が使える

### Requirement: uv だけで動くこと
Skill に同梱する生成器とドット絵ツールは、利用者の環境に uv があれば、ほかに何も手で入れずに Skill の手順どおりのコマンドで動かなければならない SHALL。

#### Scenario: 開発環境の外で動かす
- **WHEN** このリポジトリの開発用の仮想環境を使わず、Skill に書かれたコマンドで同梱の見本原稿から PPTX を作る
- **THEN** 終了コード 0 で PPTX ができる

### Requirement: Skill の内容
Skill `slide` は、原稿の書式（6 種のレイアウト、強調、画像の参照）、生成器とドット絵ツールのコマンド、文章と構成の書き方の規則（AI っぽさの一覧を含む）、作成役と点検役の使い方を書く SHALL。Skill に書いたコマンドと原稿の例は、書いてあるとおりに動かなければならない SHALL。

#### Scenario: Skill の例がそのまま通る
- **WHEN** Skill に載っている原稿の例を、Skill に載っているコマンドで生成する
- **THEN** 終了コード 0 で PPTX ができる

#### Scenario: 6 種のレイアウトがすべて載っている
- **WHEN** Skill を読む
- **THEN** 表紙、一言、箇条書き、図、表、左右 2 列の書き方がそれぞれ載っている

### Requirement: 作成役 Agent
Agent `writer` は、主題と材料を受け取り、Skill `slide` の規則で原稿を書き、生成器で PPTX を作る SHALL。生成器が拒否したら理由に沿って原稿を直し、成功するまで生成し直す SHALL。PPTX を直接編集したり、生成器以外の方法でスライドを作ったりしてはならない SHALL NOT。最後に原稿と PPTX のパスを返す SHALL。

#### Scenario: 主題からスライドを作る
- **WHEN** 作成役に主題と 3 行の材料を渡す
- **THEN** 原稿と PPTX ができ、作成役の返答に両方のパスがある

### Requirement: 点検役 Agent
Agent `critic` は、原稿を読むだけで書き換えない SHALL（使える道具は読み取りだけ）。Skill の AI っぽさの一覧と書き方の規則に照らし、指摘ごとにスライド番号、該当する文の引用、当たる規則、書き直しの案を返す SHALL。指摘がなければ、ないとだけ返す。

#### Scenario: 道具が読み取りだけ
- **WHEN** 点検役の定義を読む
- **THEN** 使える道具に、ファイルを書き換える道具とコマンドを実行する道具がない

#### Scenario: 仕込んだ AI っぽさを見つける
- **WHEN** AI っぽさの一覧から 5 種を 1 つずつ仕込んだ原稿を点検役に渡す
- **THEN** 少なくとも 4 種について、スライド番号と引用と書き直しの案を持つ指摘が返る

### Requirement: 利用者向けの説明
リポジトリの README は、Claude Code と Copilot CLI それぞれでの導入コマンド、uv が必要なこと、使い方の最短の例、見本原稿の場所を書く SHALL。

#### Scenario: README の導入手順
- **WHEN** README を読む
- **THEN** Claude Code と Copilot CLI それぞれの導入コマンドと、uv が必要なことが書いてある
