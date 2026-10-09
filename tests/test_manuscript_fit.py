import math
from pathlib import Path

import pytest

from slidekit.manuscript import ManuscriptError, parse

BODY = 11.53  # design.md「寸法と文字の大きさ」の本文領域の幅（インチ）


def capacity(pt: float, width_in: float, max_lines: int) -> int:
    """全角文字が max_lines 行にちょうど収まる最大の文字数。"""
    return math.floor(width_in * 72 / pt * max_lines)


def lines_of(text: str) -> list[int]:
    with pytest.raises(ManuscriptError) as e:
        parse(text, Path("."))
    return [p.line for p in e.value.problems]


def zen(n: int) -> str:
    return "あ" * n


# 要素ごとに (名前, 原稿を作る関数, 問題の行, pt, 枠の幅, 行数の上限)。
# 原稿は 2 枚目以降が対象。cover は 1 枚目。
CASES = [
    ("表紙のタイトル", lambda t: f"# {t}\n", 1, 40, BODY, 2),
    ("表紙の文", lambda t: f"# 題\n{t}\n", 2, 20, BODY, 1),
    ("見出し", lambda t: f"# 題\n---\n## {t}\n- a\n", 3, 30, BODY, 1),
    ("一言", lambda t: f"# 題\n---\n{t}\n", 3, 40, BODY, 3),
    ("箇条書きの項目", lambda t: f"# 題\n---\n## 見出し\n- {t}\n", 4, 24, BODY - 0.4, 2),
    (
        "図の説明文",
        lambda t: f"# 題\n---\n## 見出し\n![x](icon:gear)\n{t}\n",
        5,
        20,
        5.2,
        3,
    ),
    (
        "表のセル（3 列）",
        lambda t: f"# 題\n---\n## 見出し\n| a | b | c |\n|---|---|---|\n| {t} | 1 | 2 |\n",
        6,
        18,
        BODY / 3 - 0.2,
        2,
    ),
    (
        "表の見出しセル（2 列）",
        lambda t: f"# 題\n---\n## 見出し\n| {t} | b |\n|---|---|\n| 1 | 2 |\n",
        4,
        18,
        BODY / 2 - 0.2,
        2,
    ),
    (
        "2 列の箇条書き項目",
        lambda t: f"# 題\n---\n## 見出し\n- {t}\n|||\n右\n",
        4,
        22,
        5.5 - 0.4,
        2,
    ),
    (
        "2 列の文",
        lambda t: f"# 題\n---\n## 見出し\n左\n|||\n{t}\n",
        6,
        22,
        5.5,
        3,
    ),
]


@pytest.mark.parametrize(("name", "make", "line", "pt", "width", "max_lines"), CASES)
def test_exact_limit_passes_and_one_more_is_rejected(name, make, line, pt, width, max_lines):
    n = capacity(pt, width, max_lines)
    parse(make(zen(n)), Path("."))
    assert lines_of(make(zen(n + 1))) == [line], name


def test_heading_of_15_fullwidth_chars_fits():
    parse(f"# 題\n---\n## {zen(15)}\n- a\n", Path("."))


def test_heading_of_60_fullwidth_chars_is_rejected_at_the_heading():
    assert lines_of(f"# 題\n---\n## {zen(60)}\n- a\n") == [3]


def test_halfwidth_text_counts_0_6em():
    # 30pt・枠 11.53in は 27.67em。半角 46 文字 = 27.6em は収まり、47 文字 = 28.2em は収まらない。
    parse(f"# 題\n---\n## {'a' * 46}\n- a\n", Path("."))
    assert lines_of(f"# 題\n---\n## {'a' * 47}\n- a\n") == [3]


def test_emphasis_markers_do_not_count_toward_width():
    n = capacity(24, BODY - 0.4, 2)
    parse(f"# 題\n---\n## 見出し\n- **{zen(n - 2)}**{zen(2)}\n", Path("."))


def test_overflow_is_collected_with_other_violations():
    text = f"# 題\n---\n## {zen(60)}\n- a\n---\n## 絵文字 🚀\n- a\n"
    assert lines_of(text) == [3, 6]


def test_every_overflowing_item_is_reported():
    n = capacity(24, BODY - 0.4, 2) + 1
    text = f"# 題\n---\n## 見出し\n- {zen(n)}\n- a\n- {zen(n)}\n"
    assert lines_of(text) == [4, 6]
