import pytest

from slidekit.layout import Diagram
from slidekit.manuscript import (
    DiagramBlock,
    DiagramFigure,
    ImageBlock,
    ManuscriptError,
    parse,
)

SIMPLE = "| A | B |\nA -> B\n"
EMPHASIS = "| A | B |\nA -> B (強調)\n"
FIVE_ROWS = "".join(f"| {c} |\n" for c in "ABCDE")  # 高さ 4.4 インチ


def write(tmp_path, **files):
    for name, text in files.items():
        (tmp_path / name.replace("_flow", ".flow")).write_text(text, encoding="utf-8")


def parse_ok(tmp_path, body: str):
    return parse("# 題\n---\n" + body, tmp_path).slides[1]


def problems_of(tmp_path, body: str):
    with pytest.raises(ManuscriptError) as e:
        parse("# 題\n---\n" + body, tmp_path)
    return [(p.line, p.message) for p in e.value.problems]


def plain(t) -> str:
    return "".join(r.text for r in t)


# 本文は 3 行目から始まる: 見出し 3、画像 4、注記 5


def test_flow_figure_becomes_a_diagram_figure_with_the_note(tmp_path):
    write(tmp_path, 構成_flow=SIMPLE)
    s = parse_ok(tmp_path, "## 今の構成\n![今の構成](構成.flow)\n保存先は直接参照している。\n")
    assert isinstance(s, DiagramFigure)
    assert (s.heading, s.alt, s.ref) == ("今の構成", "今の構成", "構成.flow")
    assert isinstance(s.diagram, Diagram) and len(s.diagram.boxes) == 2
    assert plain(s.note) == "保存先は直接参照している。"


def test_flow_figure_without_a_note_has_none(tmp_path):
    write(tmp_path, 構成_flow=SIMPLE)
    s = parse_ok(tmp_path, "## 構成\n![構成](構成.flow)\n")
    assert isinstance(s, DiagramFigure) and s.note is None


def test_two_column_flow_images_become_diagram_blocks(tmp_path):
    write(tmp_path, 今の形_flow=SIMPLE, 案の形_flow=SIMPLE)
    s = parse_ok(tmp_path, "## 比べる\n![今](今の形.flow)\n|||\n![案](案の形.flow)\n")
    assert isinstance(s.left, DiagramBlock) and isinstance(s.right, DiagramBlock)
    assert (s.left.alt, s.left.ref) == ("今", "今の形.flow")


def test_two_column_flow_beside_an_icon_keeps_the_icon_a_dot_picture(tmp_path):
    write(tmp_path, 構成_flow=SIMPLE)
    s = parse_ok(tmp_path, "## 比べる\n![図](構成.flow)\n|||\n![歯車](icon:gear)\n")
    assert isinstance(s.left, DiagramBlock) and isinstance(s.right, ImageBlock)


def test_note_of_four_lines_is_rejected_at_the_note_line(tmp_path):
    write(tmp_path, 構成_flow=SIMPLE)
    body = "## 構成\n![構成](構成.flow)\n" + "あ" * 160 + "\n"
    assert [line for line, _ in problems_of(tmp_path, body)] == [5]
    ok = "## 構成\n![構成](構成.flow)\n" + "あ" * 150 + "\n"  # 3 行
    assert isinstance(parse_ok(tmp_path, ok), DiagramFigure)


def test_gloss_on_the_note_is_rejected_at_the_gloss_line(tmp_path):
    write(tmp_path, 構成_flow=SIMPLE)
    body = "## 構成\n![構成](構成.flow)\n注記。\n^ note\n"
    assert [line for line, _ in problems_of(tmp_path, body)] == [6]


def test_note_height_is_taken_from_the_diagram_max_height(tmp_path):
    write(tmp_path, 縦_flow=FIVE_ROWS)
    assert isinstance(parse_ok(tmp_path, "## 縦\n![縦](縦.flow)\n"), DiagramFigure)
    got = problems_of(tmp_path, "## 縦\n![縦](縦.flow)\n注記。\n")
    assert [line for line, _ in got] == [4]
    assert "4.4" in got[0][1]


def test_flow_emphasis_and_note_emphasis_are_rejected_at_the_note_line(tmp_path):
    write(tmp_path, 構成_flow=EMPHASIS)
    assert isinstance(parse_ok(tmp_path, "## 構成\n![構成](構成.flow)\n注記。\n"), DiagramFigure)
    body = "## 構成\n![構成](構成.flow)\nここが **要点** だ。\n"
    assert [line for line, _ in problems_of(tmp_path, body)] == [5]


def test_one_emphasis_on_each_side_is_rejected_at_the_right_image_line(tmp_path):
    write(tmp_path, 左_flow=EMPHASIS, 右_flow=EMPHASIS)
    body = "## 比べる\n![左](左.flow)\n|||\n![右](右.flow)\n"
    assert [line for line, _ in problems_of(tmp_path, body)] == [6]


def test_flow_emphasis_beside_plain_text_is_accepted(tmp_path):
    write(tmp_path, 左_flow=EMPHASIS)
    s = parse_ok(tmp_path, "## 比べる\n![左](左.flow)\n|||\n- 一\n- 二\n")
    assert isinstance(s.left, DiagramBlock)


def test_flow_file_violation_is_attached_to_the_image_line_with_its_line_number(tmp_path):
    write(tmp_path, 構成_flow="| A | B |\nA -> B\n読めない行\n")
    got = problems_of(tmp_path, "## 構成\n![構成](構成.flow)\n")
    assert [line for line, _ in got] == [4]
    assert got[0][1].startswith("構成図ファイル 構成.flow の 3 行目:")


def test_violation_without_a_flow_line_omits_the_line_number(tmp_path):
    write(tmp_path, 構成_flow="| " + " | ".join("ABCDEFGHI") + " |\n")
    got = problems_of(tmp_path, "## 構成\n![構成](構成.flow)\n")
    assert [line for line, _ in got] == [4]
    assert got[0][1].startswith("構成図ファイル 構成.flow:")
    assert "行目" not in got[0][1]


def test_all_violations_of_a_flow_file_are_reported(tmp_path):
    write(tmp_path, 構成_flow="| A | B |\n読めない\nもう一つ\n")
    got = problems_of(tmp_path, "## 構成\n![構成](構成.flow)\n")
    assert len(got) == 2


def test_missing_flow_file_is_rejected_with_its_name(tmp_path):
    got = problems_of(tmp_path, "## 構成\n![構成](ない.flow)\n")
    assert [line for line, _ in got] == [4]
    assert "ない.flow" in got[0][1]
