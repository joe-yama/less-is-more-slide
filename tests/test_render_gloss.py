"""添え訳の描画（表紙・一言・見出し）。delta spec「添え訳の見た目」「添え訳の配置」。"""

import re
import zipfile
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.util import Inches

from slidekit.manuscript import parse
from slidekit.render import render

FIXTURES = Path(__file__).parent / "fixtures"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
TOL = 2  # EMU


def slides_of(tmp_path: Path, text: str):
    out = tmp_path / "out.pptx"
    render(parse(text, FIXTURES), out)
    return list(Presentation(str(out)).slides)


def box(slide, name: str):
    found = [s for s in slide.shapes if s.name == name]
    assert len(found) == 1, [s.name for s in slide.shapes]
    return found[0]


def near(actual: int, inches: float) -> bool:
    return abs(actual - int(Inches(inches))) <= TOL


def bottom(shape) -> int:
    return shape.top + shape.height


def check_gloss_paragraph(p, text: str, pt: int) -> None:
    assert p.text == text
    assert p.alignment is not None and p.alignment.name == "LEFT"
    assert p.space_before == 0
    assert len(p.runs) == 1
    f = p.runs[0].font
    assert f.size.pt == pt
    assert f.bold is False
    assert str(f.color.rgb) == "767676"
    assert f.name == "メイリオ"
    ea = p.runs[0]._r.rPr.find(f"{{{NS_A}}}ea")
    assert ea is not None and ea.get("typeface") == "メイリオ"


def test_heading_gloss(tmp_path):
    s = slides_of(tmp_path, "# T\n---\n## Results\n^ 結果\n- a\n^ あ\n")[1]
    head = s.shapes.title
    assert near(head.height, 0.625)
    gloss = box(s, "見出しの添え訳")
    assert near(gloss.top, 1.225)
    assert near(gloss.height, 0.375)
    assert near(gloss.left, head.left / 914400)
    assert bottom(gloss) < int(Inches(1.8))
    check_gloss_paragraph(gloss.text_frame.paragraphs[0], "結果", 18)


def test_heading_without_gloss_keeps_geometry(tmp_path):
    s = slides_of(tmp_path, "# T\n---\n## Results\n- a\n")[1]
    assert near(s.shapes.title.height, 0.9)
    assert not [x for x in s.shapes if x.name == "見出しの添え訳"]


@pytest.mark.parametrize("gloss_lines", [1, 2])
def test_cover_title_gloss(tmp_path, gloss_lines):
    # 24pt の枠は 11.53 インチ = 約 34 字。2 行にするには全角 35 字以上
    gloss = "あ" * (10 if gloss_lines == 1 else 40)
    s = slides_of(tmp_path, f"# Title\n^ {gloss}\nLine\n")[0]
    g = gloss_lines * 24 * 1.5 / 72
    title = s.shapes.title
    gbox = box(s, "表紙のタイトルの添え訳")
    assert near(bottom(gbox), 3.8)
    assert near(gbox.top, 3.8 - g)
    assert near(gbox.height, g)
    assert abs(bottom(title) - gbox.top) <= TOL
    assert near(title.top, 1.6 - g)
    check_gloss_paragraph(gbox.text_frame.paragraphs[0], gloss, 24)


def test_cover_line_gloss(tmp_path):
    s = slides_of(tmp_path, "# Title\nFirst\n^ 一\nSecond\n")[0]
    sentence = box(s, "表紙の文")
    assert near(sentence.height, 2.4)
    ps = sentence.text_frame.paragraphs
    assert [p.text for p in ps] == ["First", "一", "Second"]
    check_gloss_paragraph(ps[1], "一", 12)
    assert ps[0].runs[0].font.size.pt == 20


def test_cover_without_gloss_keeps_geometry(tmp_path):
    s = slides_of(tmp_path, "# Title\nFirst\n")[0]
    assert near(box(s, "表紙の文").height, 1.8)
    assert near(s.shapes.title.top, 1.6)
    assert near(s.shapes.title.height, 2.2)
    assert not [x for x in s.shapes if x.name == "表紙のタイトルの添え訳"]


def test_statement_gloss(tmp_path):
    s = slides_of(tmp_path, "# T\n---\nHello\n^ こんにちは\n")[1]
    ps = box(s, "一言").text_frame.paragraphs
    assert [p.text for p in ps] == ["Hello", "こんにちは"]
    check_gloss_paragraph(ps[1], "こんにちは", 24)
    assert ps[0].runs[0].font.size.pt == 40


def test_statement_without_gloss_has_one_paragraph(tmp_path):
    s = slides_of(tmp_path, "# T\n---\nHello\n")[1]
    assert len(box(s, "一言").text_frame.paragraphs) == 1


# --- 4.2 箇条書き・2 列・図の説明文・表のセル ---


def check_item_gloss(p, text: str, pt: int) -> None:
    check_gloss_paragraph(p, text, pt)
    ppr = p._p.pPr
    assert ppr is not None
    assert ppr.find(f"{{{NS_A}}}buNone") is not None
    assert ppr.find(f"{{{NS_A}}}buChar") is None
    assert int(ppr.get("marL")) == int(Inches(0.4))
    assert int(ppr.get("indent")) == 0


def text_left(p) -> int:
    """段落の本文（2 行目以降ではなく、1 行目の文字）の左端。行頭の記号があれば、記号の右。"""
    ppr = p._p.pPr
    marl = int(ppr.get("marL", 0))
    has_bullet = ppr.find(f"{{{NS_A}}}buChar") is not None
    return marl if has_bullet else marl + int(ppr.get("indent", 0))


def test_bullet_item_gloss(tmp_path):
    s = slides_of(tmp_path, "# T\n---\n## H\n- a\n^ あ\n- b\n- c\n^ し\n")[1]
    ps = box(s, "箇条書き").text_frame.paragraphs
    assert [p.text for p in ps] == ["a", "あ", "b", "c", "し"]
    check_item_gloss(ps[1], "あ", 14)
    check_item_gloss(ps[4], "し", 14)
    assert text_left(ps[1]) == text_left(ps[0]) == int(Inches(0.4))
    assert ps[0]._p.pPr.find(f"{{{NS_A}}}buChar") is not None
    assert ps[2].space_before.pt == 12  # 次の項目の前の間隔は変わらない
    assert ps[3].space_before.pt == 12


def test_bullets_without_gloss_have_one_paragraph_per_item(tmp_path):
    s = slides_of(tmp_path, "# T\n---\n## H\n- a\n- b\n")[1]
    assert len(box(s, "箇条書き").text_frame.paragraphs) == 2


def test_two_column_gloss(tmp_path):
    text = "# T\n---\n## H\n- a\n^ あ\n- b\n|||\nText\n^ 文\n"
    s = slides_of(tmp_path, text)[1]
    bullets = box(s, "箇条書き").text_frame.paragraphs
    assert [p.text for p in bullets] == ["a", "あ", "b"]
    check_item_gloss(bullets[1], "あ", 13)
    assert bullets[2].space_before.pt == 10
    para = box(s, "文").text_frame.paragraphs
    assert [p.text for p in para] == ["Text", "文"]
    check_gloss_paragraph(para[1], "文", 13)


def test_two_column_right_bullets_gloss(tmp_path):
    s = slides_of(tmp_path, "# T\n---\n## H\nText\n|||\n- a\n^ あ\n")[1]
    ps = box(s, "箇条書き").text_frame.paragraphs
    check_item_gloss(ps[1], "あ", 13)


def test_figure_caption_gloss(tmp_path):
    s = slides_of(tmp_path, "# T\n---\n## H\n![x](icon:gear)\nCaption\n^ 説明\n")[1]
    ps = box(s, "図の説明").text_frame.paragraphs
    assert [p.text for p in ps] == ["Caption", "説明"]
    check_gloss_paragraph(ps[1], "説明", 12)


def test_table_cell_gloss(tmp_path):
    text = (
        "# T\n---\n## H\n| a | b | c |\n^ | あ | | し |\n|---|---|---|\n"
        "| 1 | 2 | 3 |\n^ | | に | |\n| 4 | 5 | 6 |\n"
    )
    s = slides_of(tmp_path, text)[1]
    table = box(s, "表").table
    head = [table.cell(0, c).text_frame.paragraphs for c in range(3)]
    assert [len(p) for p in head] == [2, 1, 2]
    check_gloss_paragraph(head[0][1], "あ", 11)
    check_gloss_paragraph(head[2][1], "し", 11)
    row1 = [table.cell(1, c).text_frame.paragraphs for c in range(3)]
    assert [len(p) for p in row1] == [1, 2, 1]
    check_gloss_paragraph(row1[1][1], "に", 11)
    row2 = [table.cell(2, c).text_frame.paragraphs for c in range(3)]
    assert [len(p) for p in row2] == [1, 1, 1]


# --- 確認用の原稿（examples/bilingual.md）---

EXAMPLES = Path(__file__).parent.parent / "examples"
BILINGUAL = EXAMPLES / "bilingual.md"
FIVE_COLORS = {"FFFFFF", "1A1A1A", "6B6B6B", "B23A2E", "767676"}


def expected_glosses() -> list[str]:
    out = []
    for ln in BILINGUAL.read_text(encoding="utf-8").splitlines():
        if not ln.startswith("^ "):
            continue
        body = ln[2:].strip()
        if body.startswith("|"):
            out += [c.strip() for c in body.strip("|").split("|") if c.strip()]
        else:
            out.append(body)
    return out


def paragraphs_with_color(prs, rgb: str) -> tuple[list[str], list[str]]:
    """(rgb の文字だけの段落の文字, rgb と別の色を混ぜた段落の文字)"""
    only, mixed = [], []
    for slide in prs.slides:
        frames = []
        for sh in slide.shapes:
            if sh.has_text_frame:
                frames.append(sh.text_frame)
            elif sh.has_table:
                frames += [c.text_frame for row in sh.table.rows for c in row.cells]
        for tf in frames:
            for p in tf.paragraphs:
                cols = {str(r.font.color.rgb) for r in p.runs}
                if rgb in cols:
                    (only if cols == {rgb} else mixed).append(p.text)
    return only, mixed


@pytest.fixture(scope="module")
def bilingual_pptx(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("bilingual") / "bilingual.pptx"
    render(parse(BILINGUAL.read_text(encoding="utf-8"), EXAMPLES), out)
    return out


def test_bilingual_uses_only_the_five_colors(bilingual_pptx):
    used = set()
    with zipfile.ZipFile(bilingual_pptx) as z:
        for n in z.namelist():
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", n):
                xml = z.read(n).decode("utf-8")
                used |= {c.upper() for c in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', xml)}
    assert "767676" in used
    assert used <= FIVE_COLORS


def test_bilingual_gloss_color_is_only_on_gloss_paragraphs(bilingual_pptx):
    only, mixed = paragraphs_with_color(Presentation(str(bilingual_pptx)), "767676")
    assert not mixed
    assert sorted(only) == sorted(expected_glosses())


def test_bilingual_draws_a_gloss_for_every_target(bilingual_pptx):
    kinds = {type(s) for s in parse(BILINGUAL.read_text(encoding="utf-8"), EXAMPLES).slides}
    assert len(kinds) == 6
    # 原稿の添え訳の数: 表紙 3、一言 1、見出し 4（箇条書き・図・表・2 列）、箇条書き 3、図 1、表 3（見出し行 3 + 本文 6）、2 列 3
    assert len(expected_glosses()) == 3 + 1 + 4 + 3 + 1 + 9 + 3
    only, _ = paragraphs_with_color(Presentation(str(bilingual_pptx)), "767676")
    assert len(only) == len(expected_glosses())
