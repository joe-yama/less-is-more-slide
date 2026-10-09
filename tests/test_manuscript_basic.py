from pathlib import Path

import pytest

from slidekit.manuscript import Bullets, Cover, ManuscriptError, Run, Statement, parse


def parse_ok(text: str):
    return parse(text, Path("."))


def problems_of(text: str):
    with pytest.raises(ManuscriptError) as e:
        parse(text, Path("."))
    return e.value.problems


def lines_of(text: str) -> list[int]:
    return [p.line for p in problems_of(text)]


def plain(t) -> str:
    return "".join(r.text for r in t)


# --- 原稿の区切りと表紙 ---


def test_cover_with_title_and_one_line():
    deck = parse_ok("# 四半期の振り返り\n営業部 山田\n")
    cover = deck.slides[0]
    assert isinstance(cover, Cover)
    assert cover.title == "四半期の振り返り"
    assert [plain(t) for t in cover.lines] == ["営業部 山田"]


def test_cover_with_title_only_and_with_three_lines():
    assert parse_ok("# 題\n").slides[0].lines == []
    assert len(parse_ok("# 題\na\nb\nc\n").slides[0].lines) == 3


def test_cover_with_four_lines_is_rejected_at_the_fourth():
    assert lines_of("# 題\na\nb\nc\nd\n") == [5]


def test_cover_without_title_is_rejected_with_reason():
    problems = problems_of("営業部 山田\n")
    assert [p.line for p in problems] == [1]
    assert "タイトル" in problems[0].message


def test_second_h1_in_cover_slide_is_rejected():
    assert lines_of("# 題\n# 別の題\n") == [2]


def test_h1_outside_the_cover_is_rejected():
    assert lines_of("# 題\n---\n# 二枚目\n") == [3]


def test_blank_lines_are_ignored_and_slides_split_on_separator():
    deck = parse_ok("# 題\n\n\n---\n\n結論から言う。\n\n---\n## 見出し\n\n- a\n\n- b\n")
    assert len(deck.slides) == 3
    assert [plain(i) for i in deck.slides[2].items] == ["a", "b"]


def test_empty_slide_is_rejected():
    # 空のスライドは、それを始める `---` の行で報告する
    assert lines_of("# 題\n---\n---\n結論\n") == [2]
    assert lines_of("# 題\n---\n結論\n---\n") == [4]


def test_crlf_line_endings():
    deck = parse_ok("# 題\r\n---\r\n結論\r\n")
    assert isinstance(deck.slides[1], Statement)


# --- 一言 ---


def test_statement_slide():
    deck = parse_ok("# 題\n---\n結論から言うと、来期は値上げしない。\n")
    s = deck.slides[1]
    assert isinstance(s, Statement)
    assert plain(s.text) == "結論から言うと、来期は値上げしない。"


def test_statement_with_two_lines_and_no_heading_is_rejected():
    assert lines_of("# 題\n---\n一行目\n二行目\n") == [3]


def test_statement_cannot_be_a_bullet():
    assert lines_of("# 題\n---\n- 項目\n") == [3]


# --- 箇条書き ---


def test_bullets_slide():
    deck = parse_ok("# 題\n---\n## 今期やったこと\n- 一つ目\n- 二つ目\n- 三つ目\n")
    s = deck.slides[1]
    assert isinstance(s, Bullets)
    assert s.heading == "今期やったこと"
    assert [plain(i) for i in s.items] == ["一つ目", "二つ目", "三つ目"]


def test_one_and_five_bullets_are_accepted():
    parse_ok("# 題\n---\n## 見出し\n- a\n")
    parse_ok("# 題\n---\n## 見出し\n- a\n- b\n- c\n- d\n- e\n")


def test_sixth_bullet_is_rejected_at_its_own_line():
    text = "# 題\n---\n## 見出し\n- a\n- b\n- c\n- d\n- e\n- f\n"
    assert lines_of(text) == [9]


def test_nested_bullet_is_rejected():
    assert lines_of("# 題\n---\n## 見出し\n- a\n  - b\n") == [5]


def test_heading_and_plain_sentence_suggests_statement_or_bullets():
    problems = problems_of("# 題\n---\n## 見出し\nただの文\n")
    assert [p.line for p in problems] == [4]
    assert "一言" in problems[0].message and "箇条書き" in problems[0].message


def test_heading_alone_is_rejected():
    assert lines_of("# 題\n---\n## 見出し\n") == [3]


def test_mixed_bullets_and_sentence_is_rejected():
    assert lines_of("# 題\n---\n## 見出し\n- a\nただの文\n") == [5]


# --- 未対応の書式 ---


@pytest.mark.parametrize(
    "bad",
    [
        "### 小見出し",
        "###### 小見出し",
        "> 引用",
        "1. 番号付き",
        "```",
        "<div>x</div>",
        "`code` を使う",
        "[資料](https://example.com)",
        "__強調__",
        "~~消す~~",
        "*強調*",
    ],
)
def test_unsupported_format_is_rejected_in_a_statement(bad):
    assert lines_of(f"# 題\n---\n{bad}\n") == [3]


def test_link_in_bullet_item_is_rejected():
    text = "# 題\n---\n## 見出し\n- [資料](https://example.com)\n"
    assert lines_of(text) == [4]


@pytest.mark.parametrize("bad", ["### 小見出し", "> 引用", "1. 番号", "<p>x</p>"])
def test_unsupported_line_in_a_bullet_slide_reports_one_problem(bad):
    assert lines_of(f"# 題\n---\n## 見出し\n- a\n{bad}\n") == [5]


def test_lone_asterisk_is_plain_text():
    deck = parse_ok("# 題\n---\n## 見出し\n- 5*3 は 15\n")
    assert plain(deck.slides[1].items[0]) == "5*3 は 15"


def test_ordinary_symbols_are_not_emoji():
    parse_ok("# 題\n---\n## 見出し\n- 売上 → 利益、※注記 〜 ①\n")


# --- 強調 ---


def test_emphasis_becomes_a_run_not_bold():
    deck = parse_ok("# 題\n---\n## 見出し\n- 売上が **3 割** 増えた\n")
    item = deck.slides[1].items[0]
    assert item == (Run("売上が "), Run("3 割", emphasis=True), Run(" 増えた"))
    assert not hasattr(item[1], "bold")


def test_two_emphases_in_a_slide_are_rejected_at_the_second():
    text = "# 題\n---\n## 見出し\n- **a**\n- **b**\n"
    assert lines_of(text) == [5]


def test_emphases_in_different_slides_are_fine():
    parse_ok("# 題\n---\n## 見出し\n- **a**\n---\n## 見出し\n- **b**\n")


def test_emphasis_in_heading_is_rejected():
    assert lines_of("# 題\n---\n## **大事** な話\n- a\n") == [3]


def test_unclosed_emphasis_is_rejected():
    assert lines_of("# 題\n---\n## 見出し\n- **a\n") == [4]


# --- 絵文字 ---


def test_emoji_in_heading_reports_line_and_codepoint():
    problems = problems_of("# 題\n---\n## 出発 🚀\n- a\n")
    assert [p.line for p in problems] == [3]
    assert "U+1F680" in problems[0].message
    assert "🚀" in problems[0].message


def test_variation_selector_is_rejected():
    problems = problems_of("# 題\n---\n結論️\n")
    assert "U+FE0F" in problems[0].message


def test_emoji_in_cover_is_rejected():
    assert lines_of("# 題 ✨\n") == [1]


# --- 複数の違反 ---


def test_all_violations_are_collected_in_line_order():
    text = (
        "# 題\n"  # 1
        "---\n"  # 2
        "## 出発 🚀\n"  # 3 絵文字
        "- a\n"  # 4
        "---\n"  # 5
        "## 多い\n"  # 6
        "- 1\n- 2\n- 3\n- 4\n- 5\n"  # 7-11
        "- 6\n"  # 12 6 項目目
        "---\n"  # 13
        "### 小見出し\n"  # 14
    )
    assert lines_of(text) == [3, 12, 14]


def test_image_line_in_cover_is_rejected_with_its_line_number():
    ps = problems_of("# 題\n![絵](icon:gear)\n")
    assert [p.line for p in ps] == [2]
    assert "表紙に画像は置けません" in ps[0].message
