import pytest

from slidekit.flow import FlowError, parse_flow


def problems(text: str) -> list[tuple[int | None, str]]:
    with pytest.raises(FlowError) as e:
        parse_flow(text)
    return [(p.line, p.message) for p in e.value.problems]


def lines_of(text: str) -> list[int | None]:
    return [line for line, _ in problems(text)]


# --- 行の種類 ---


def test_unreadable_line_is_rejected_with_line_number():
    text = "| 店舗 | 受付 |\n\n店舗から受付へ\n"
    assert lines_of(text) == [3]


def test_emoji_in_flow_file_is_rejected_with_line_number():
    text = "| 店舗 | 受付 |\n店舗 -> 受付: 🚀\n"
    got = problems(text)
    assert got[0][0] == 2
    assert "🚀" in got[0][1]


def test_link_in_flow_file_is_rejected():
    text = "| 店舗 | 受付 |\n- 店舗: [a](b)\n"
    assert lines_of(text) == [2]


# --- 配置の行 ---


def test_placement_makes_boxes_with_positions():
    spec = parse_flow("| 店舗 | 受付 API | |\n| | 保存先 | 集計 |\n")
    assert spec.columns == 3
    got = {(b.name, b.col, b.row_top, b.row_bottom) for b in spec.boxes}
    assert got == {
        ("店舗", 0, 0, 0),
        ("受付 API", 1, 0, 0),
        ("保存先", 1, 1, 1),
        ("集計", 2, 1, 1),
    }
    # 配置の行の順に左上から
    assert [b.name for b in spec.boxes] == ["店舗", "受付 API", "保存先", "集計"]
    assert [b.line_no for b in spec.boxes] == [1, 1, 2, 2]


def test_same_name_stacked_spans_rows():
    spec = parse_flow("| 保存先 | 集計 a |\n| 保存先 | 集計 b |\n")
    assert len(spec.boxes) == 3
    box = next(b for b in spec.boxes if b.name == "保存先")
    assert (box.col, box.row_top, box.row_bottom) == (0, 0, 1)


def test_separated_same_name_is_rejected_at_later_row():
    text = "| 店舗 | a |\n| | b |\n| 店舗 | c |\n"
    assert lines_of(text) == [3]


def test_same_name_in_other_column_is_rejected():
    assert lines_of("| 店舗 | 店舗 |\n") == [1]


def test_column_count_mismatch_is_rejected_at_row():
    assert lines_of("| a | b | c |\n| d | e |\n") == [2]


@pytest.mark.parametrize(
    "name", ["受付(新)", "a,b", "a:b", "a[b]", "a->b", "a**b**", "a<br>b", "a)b"]
)
def test_forbidden_characters_in_name(name):
    got = problems(f"| {name} | 次 |\n")
    assert [line for line, _ in got] == [1]


def test_placement_rows_must_be_contiguous():
    text = "| a | b |\n- a: x\n| c | d |\n"
    got = problems(text)
    assert (3, "配置の行は続けて書いてください") in got


def test_blank_line_between_placement_rows_is_allowed():
    spec = parse_flow("| a | b |\n\n| c | d |\n")
    assert len(spec.boxes) == 4


def test_missing_placement_is_rejected_without_line():
    assert (None, "配置の行がありません") in problems("- a: x\n")


# --- 4 種の行をまとめて読む ---


def test_four_kinds_of_lines():
    text = (
        "| 店舗 | 受付 |\n"
        "| 倉庫 | 集計 |\n"
        "- 店舗: 東口\n"
        "[社内] 受付, 集計\n"
        "店舗 -> 受付\n"
        "倉庫 -> 集計\n"
    )
    spec = parse_flow(text)
    assert len(spec.boxes) == 4
    assert len(spec.groups) == 1
    assert len(spec.arrows) == 2


# --- 箱の中の行 ---

BOXES = "| 保存先 | 受付 |\n"


def test_box_lines_in_order_with_emphasis_runs():
    text = BOXES + "- 保存先: key=V1/\n- 保存先: **key=V/**\n- 保存先: key=V3/\n- 保存先: …\n"
    spec = parse_flow(text)
    box = next(b for b in spec.boxes if b.name == "保存先")
    assert [tuple((r.text, r.emphasis) for r in t) for t in box.lines] == [
        (("key=V1/", False),),
        (("key=V/", True),),
        (("key=V3/", False),),
        (("…", False),),
    ]


def test_fifth_box_line_is_rejected_at_fifth():
    text = BOXES + "".join(f"- 保存先: {i}\n" for i in range(5))
    assert lines_of(text) == [6]


def test_box_line_for_unknown_name():
    assert lines_of(BOXES + "- 倉庫: 3 階\n") == [2]


def test_box_line_without_colon_is_rejected():
    assert lines_of(BOXES + "- 保存先\n") == [2]


def test_box_line_rejects_line_break():
    assert lines_of(BOXES + "- 保存先: a<br>b\n") == [2]


# --- 範囲の枠 ---

TWO = "| a | b | c |\n"


def test_group_members():
    spec = parse_flow(TWO + "[社内] a, b\n")
    assert spec.groups[0].label == "社内"
    assert spec.groups[0].members == ["a", "b"]
    assert spec.groups[0].line_no == 2


def test_group_empty_label_is_rejected():
    assert lines_of(TWO + "[] a, b\n") == [2]


def test_group_unknown_member_is_rejected():
    assert lines_of(TWO + "[社内] a, z\n") == [2]


def test_group_second_with_same_label_is_rejected():
    assert lines_of(TWO + "[社内] a\n[社内] b\n") == [3]


def test_group_without_members_is_rejected():
    assert lines_of(TWO + "[社内]\n") == [2]


# --- 矢印の行 ---


def arrow(line: str):
    return parse_flow(TWO + line + "\n").arrows[0]


def test_plain_arrow():
    a = arrow("a -> b")
    assert (a.src, a.dst, a.emphasis, a.dashed, a.route, a.label, a.cross, a.line_no) == (
        "a",
        "b",
        False,
        False,
        "straight",
        None,
        False,
        2,
    )


def test_arrow_attributes_and_cross_label():
    a = arrow("a -> b (強調, 破線, 下回り): × 直接の参照はやめる")
    assert a.emphasis and a.dashed and a.route == "under" and a.cross
    assert a.label == ["直接の参照はやめる"]


def test_arrow_over_route():
    assert arrow("a -> b (上回り)").route == "over"


def test_arrow_label_two_lines():
    assert arrow("a -> b: ここで<br>社外に渡る").label == ["ここで", "社外に渡る"]


def test_arrow_label_plain():
    a = arrow("a -> b: 直接参照")
    assert a.label == ["直接参照"] and not a.cross


def test_cross_on_non_emphasis_arrow_is_rejected():
    assert lines_of(TWO + "a -> b: × 使わない\n") == [2]


def test_unknown_attribute_lists_available_ones():
    got = problems(TWO + "a -> b (太線)\n")
    assert got[0][0] == 2
    for attr in ("強調", "破線", "上回り", "下回り"):
        assert attr in got[0][1]


def test_over_and_under_together_is_rejected():
    assert lines_of(TWO + "a -> b (上回り, 下回り)\n") == [2]


def test_arrow_unknown_name_is_rejected():
    assert lines_of(TWO + "a -> z\n") == [2]
    assert lines_of(TWO + "z -> a\n") == [2]


def test_arrow_to_itself_is_rejected():
    assert lines_of(TWO + "a -> a\n") == [2]


def test_second_arrow_for_same_pair_is_rejected():
    assert lines_of(TWO + "a -> b\nb -> a\na -> b: x\n") == [4]


def test_three_line_label_is_rejected():
    assert lines_of(TWO + "a -> b: 1<br>2<br>3\n") == [2]


def test_emphasis_in_label_is_rejected():
    assert lines_of(TWO + "a -> b: **x**\n") == [2]


def test_other_html_tag_in_label_is_rejected():
    assert lines_of(TWO + "a -> b: <b>x</b>\n") == [2]


def test_arrow_line_numbers_are_reported_for_every_violation():
    assert lines_of(TWO + "a -> z\nb -> b\n") == [2, 3]
