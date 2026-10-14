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
