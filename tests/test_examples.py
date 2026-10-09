import subprocess
import sys
from pathlib import Path

from slidekit.manuscript import (
    Bullets,
    Cover,
    Figure,
    Statement,
    Table,
    TwoColumn,
    parse,
)

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
