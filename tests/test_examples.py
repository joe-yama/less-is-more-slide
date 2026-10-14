import subprocess
import sys
import zipfile
from pathlib import Path

from slidekit.manuscript import (
    Bullets,
    Cover,
    DiagramBlock,
    DiagramFigure,
    Figure,
    Statement,
    Table,
    TwoColumn,
    parse,
)
from slidekit.render import render

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
SAMPLE = EXAMPLES / "sample.md"
BUILD = ROOT / "plugin" / "skills" / "slide" / "scripts" / "build.py"


def test_sample_uses_all_six_layouts():
    deck = parse(SAMPLE.read_text(encoding="utf-8"), EXAMPLES)
    kinds = {type(s) for s in deck.slides}
    assert kinds == {Cover, Statement, Bullets, Figure, Table, TwoColumn}


def test_sample_references_a_grid_file():
    text = SAMPLE.read_text(encoding="utf-8")
    assert "(robot.txt)" in text
    assert (EXAMPLES / "robot.txt").is_file()


def test_sample_builds(tmp_path):
    out = tmp_path / "sample.pptx"
    r = subprocess.run(
        [sys.executable, str(BUILD), str(SAMPLE), "-o", str(out)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert out.stat().st_size > 0


def test_sample_has_no_gloss_color(tmp_path):
    out = tmp_path / "sample.pptx"
    render(parse(SAMPLE.read_text(encoding="utf-8"), EXAMPLES), out)
    with zipfile.ZipFile(out) as z:
        for n in z.namelist():
            if n.endswith(".xml"):
                assert "767676" not in z.read(n).decode("utf-8").upper(), n


def test_bilingual_builds(tmp_path):
    out = tmp_path / "bilingual.pptx"
    r = subprocess.run(
        [sys.executable, str(BUILD), str(EXAMPLES / "bilingual.md"), "-o", str(out)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert out.stat().st_size > 0


def test_bilingual_uses_all_six_layouts():
    deck = parse((EXAMPLES / "bilingual.md").read_text(encoding="utf-8"), EXAMPLES)
    assert {type(s) for s in deck.slides} == {Cover, Statement, Bullets, Figure, Table, TwoColumn}
    assert 5 <= len(deck.slides) <= 7


def test_design_review_builds_with_eight_diagrams(tmp_path):
    src = EXAMPLES / "design-review.md"
    out = tmp_path / "design-review.pptx"
    r = subprocess.run(
        [sys.executable, str(BUILD), str(src), "-o", str(out)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    deck = parse(src.read_text(encoding="utf-8"), EXAMPLES)
    figures = [s for s in deck.slides if isinstance(s, DiagramFigure)]
    columns = [s for s in deck.slides if isinstance(s, TwoColumn)]
    assert len(figures) == 6
    assert len(columns) == 1
    assert isinstance(columns[0].left, DiagramBlock)
    assert isinstance(columns[0].right, DiagramBlock)
    assert sum(1 for f in figures if f.note is not None) >= 2
