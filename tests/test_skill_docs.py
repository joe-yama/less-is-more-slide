import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from slidekit.flow import parse_flow
from slidekit.layout import layout_flow
from slidekit.manuscript import (
    Bullets,
    Cover,
    DiagramFigure,
    Figure,
    Section,
    Statement,
    Table,
    TwoColumn,
    parse,
)

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "plugin" / "skills" / "slide"
SKILL = SKILL_DIR / "SKILL.md"
FORMAT = SKILL_DIR / "references" / "format.md"
WRITING = SKILL_DIR / "references" / "writing.md"
BUILD = SKILL_DIR / "scripts" / "build.py"
SEVEN = {Cover, Section, Statement, Bullets, Figure, Table, TwoColumn}

FENCE = re.compile(r"^```(\w*)\n(.*?)^```", re.DOTALL | re.MULTILINE)
# 表紙から始まらない例には、確かめるときだけこの表紙を前に足す
COVER = "# 題\n\n---\n\n"


def blocks(path: Path, lang: str) -> list[str]:
    return [body for tag, body in FENCE.findall(path.read_text(encoding="utf-8")) if tag == lang]


def full_manuscript(block: str) -> str:
    return block if block.startswith("# ") else COVER + block


def manuscripts(path: Path) -> list[str]:
    return [full_manuscript(b) for b in blocks(path, "markdown")]


def place_flow(path: Path, folder: Path) -> None:
    """文書の最初の flow の例を、原稿の例が参照する 構成.flow として置く。"""
    flows = blocks(path, "flow")
    if flows:
        (folder / "構成.flow").write_text(flows[0], encoding="utf-8")


def kinds_in(path: Path, folder: Path) -> set[type]:
    place_flow(path, folder)
    kinds: set[type] = set()
    for m in manuscripts(path):
        kinds |= {type(s) for s in parse(m, folder).slides}
    return kinds


@pytest.fixture
def workdir(tmp_path):
    shutil.copy(ROOT / "examples" / "robot.txt", tmp_path / "robot.txt")
    return tmp_path


@pytest.mark.parametrize("path", [SKILL, FORMAT], ids=["SKILL.md", "format.md"])
def test_every_manuscript_example_builds(path, workdir):
    examples = manuscripts(path)
    place_flow(path, workdir)
    assert examples, f"{path.name} に原稿の例（```markdown）がない"
    for i, text in enumerate(examples):
        src = workdir / f"ex{i}.md"
        src.write_text(text, encoding="utf-8")
        out = workdir / f"ex{i}.pptx"
        r = subprocess.run(
            [sys.executable, str(BUILD), str(src), "-o", str(out)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert r.returncode == 0, f"{path.name} の {i + 1} 番目の例:\n{text}\n{r.stderr}"
        assert out.stat().st_size > 0


@pytest.mark.parametrize("path", [SKILL, FORMAT], ids=["SKILL.md", "format.md"])
def test_all_seven_layouts_are_shown(path, tmp_path):
    assert kinds_in(path, tmp_path) - {DiagramFigure} == SEVEN


def parsed_slides(path: Path, folder: Path) -> list:
    place_flow(path, folder)
    return [s for m in manuscripts(path) for s in parse(m, folder).slides]


def test_format_shows_statement_note_break_and_column_emphasis(tmp_path):
    slides = parsed_slides(FORMAT, tmp_path)
    assert any(isinstance(s, Statement) and s.notes for s in slides)
    assert any(isinstance(s, Table) and s.emphasis_col is not None for s in slides)
    assert any("<br>" in b for b in blocks(FORMAT, "markdown"))
    assert any(isinstance(s, Statement) and "\n" in s.text[0].text for s in slides)


def test_format_documents_the_new_layouts_and_rules():
    text = FORMAT.read_text(encoding="utf-8")
    assert "## 7 種のレイアウト" in text
    assert "### 中扉" in text
    for key in ("<br>", "補足", "16pt", "列の強調", "中扉"):
        assert key in text, key


def test_writing_has_the_break_and_note_rules():
    text = WRITING.read_text(encoding="utf-8")
    assert "意味の切れ目で `<br>` を入れる" in text
    assert "補足は、一言の理由か条件を 1〜2 行で書く" in text


def test_skill_commands_use_the_design_form():
    text = SKILL.read_text(encoding="utf-8")
    commands = [
        ln.strip()
        for tag, body in FENCE.findall(text)
        if tag == "sh"
        for ln in body.splitlines()
        if "scripts/" in ln
    ]
    assert any("build.py" in c for c in commands)
    assert any("pixel.py" in c for c in commands)
    for c in commands:
        assert re.fullmatch(r"uv run <Skill のフォルダ>/scripts/(build|pixel)\.py .+", c), c
    assert any(re.search(r"build\.py \S+ -o \S+", c) for c in commands)
    assert "Skill のフォルダ" in text


AI_TELLS = [
    "絵文字",
    "誇張",
    "3 つ",
    "コロン",
    "揃いすぎ",
    "具体のなさ",
    "定型",
    "対比",
    "強調の乱用",
    "飾りの図",
    "カタカナ",
    "前置き",
]


def test_writing_lists_the_twelve_ai_tells():
    text = WRITING.read_text(encoding="utf-8")
    numbered = re.findall(r"^#+ (\d+)\. (.+)$", text, re.MULTILINE)
    assert [int(n) for n, _ in numbered] == list(range(1, 13))
    for (_, title), key in zip(numbered, AI_TELLS, strict=True):
        assert key in title, (title, key)


def test_skill_tells_the_caller_to_pass_the_skill_folder_path():
    text = SKILL.read_text(encoding="utf-8")
    assert "絶対パス" in text
    for agent in ("writer", "critic"):
        line = next(ln for ln in text.splitlines() if f"Agent `{agent}`" in ln)
        assert "Skill のフォルダの絶対パス" in line, agent


def test_skill_example_has_a_gloss_line():
    assert any(ln.startswith("^ ") for b in blocks(SKILL, "markdown") for ln in b.splitlines())


def test_format_documents_the_gloss():
    text = FORMAT.read_text(encoding="utf-8")
    assert "## 添え訳" in text
    section = text.split("## 添え訳", 1)[1].split("\n## 強調", 1)[0]
    assert any(ln.startswith("^ ") for b in blocks(FORMAT, "markdown") for ln in b.splitlines())
    assert "^ | " in section  # 表の書き方
    for key in ("767676", "14pt", "11pt", "2 行", "1 行", "拒否", "**", "すぐ次の行"):
        assert key in section, key


def test_writing_requires_the_gloss_to_match_the_body():
    text = WRITING.read_text(encoding="utf-8")
    assert "添え訳は本文と同じ意味にし、情報を足したり削ったりしない" in text


@pytest.mark.parametrize("path", [SKILL, FORMAT], ids=["SKILL.md", "format.md"])
def test_every_flow_example_passes_parse_and_layout(path):
    examples = blocks(path, "flow")
    assert examples, f"{path.name} に構成図の例（```flow）がない"
    for text in examples:
        layout_flow(parse_flow(text), 11.53, 4.9)


def test_format_documents_the_flow_diagram():
    text = FORMAT.read_text(encoding="utf-8")
    assert "## 構成図" in text
    section = text.split("## 構成図", 1)[1].split("\n## 添え訳", 1)[0]
    for key in ("配置の行", "箱の中の行", "範囲の枠", "矢印の行", "強調", "構成.flow"):
        assert key in section, key
    assert any("(構成.flow)" in b for b in blocks(FORMAT, "markdown"))
    # 配置の決まり方と、拒否される書き方
    assert "配置の決まり方" in section
    for key in ("0.6 インチ", "3.0 インチ", "上回り", "下回り"):
        assert key in section, key
    rejected = section.split("拒否される書き方", 1)[1]
    for key in (
        "`->`",
        "箱の内側を通る",
        "回り込み",
        "メンバーでない箱",
        "一部だけ重なる",
        "置ける場所がない",
        "上限を超える",
        "5 行目",
    ):
        assert key in rejected, key


def test_skill_summarizes_the_flow_diagram():
    text = SKILL.read_text(encoding="utf-8")
    assert "構成図" in text and ".flow" in text


def test_writing_has_the_flow_diagram_rules():
    text = WRITING.read_text(encoding="utf-8")
    assert "構成図は構成や流れを説明するときだけ使う" in text
    assert "構成図の強調は、言いたい点の 1 か所だけ" in text
    tell = text.split("### 10.", 1)[1].split("### 11.", 1)[0]
    assert "構成図" in tell
