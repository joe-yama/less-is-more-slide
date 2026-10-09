import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

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
SKILL_DIR = ROOT / "plugin" / "skills" / "slide"
SKILL = SKILL_DIR / "SKILL.md"
FORMAT = SKILL_DIR / "references" / "format.md"
WRITING = SKILL_DIR / "references" / "writing.md"
BUILD = SKILL_DIR / "scripts" / "build.py"
SIX = {Cover, Statement, Bullets, Figure, Table, TwoColumn}

FENCE = re.compile(r"^```(\w*)\n(.*?)^```", re.DOTALL | re.MULTILINE)
# 表紙から始まらない例には、確かめるときだけこの表紙を前に足す
COVER = "# 題\n\n---\n\n"


def blocks(path: Path, lang: str) -> list[str]:
    return [body for tag, body in FENCE.findall(path.read_text(encoding="utf-8")) if tag == lang]


def full_manuscript(block: str) -> str:
    return block if block.startswith("# ") else COVER + block


def manuscripts(path: Path) -> list[str]:
    return [full_manuscript(b) for b in blocks(path, "markdown")]


def kinds_in(path: Path) -> set[type]:
    kinds: set[type] = set()
    for m in manuscripts(path):
        kinds |= {type(s) for s in parse(m, SKILL_DIR / "icons").slides}
    return kinds


@pytest.fixture
def workdir(tmp_path):
    shutil.copy(ROOT / "examples" / "robot.txt", tmp_path / "robot.txt")
    return tmp_path


@pytest.mark.parametrize("path", [SKILL, FORMAT], ids=["SKILL.md", "format.md"])
def test_every_manuscript_example_builds(path, workdir):
    examples = manuscripts(path)
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
def test_all_six_layouts_are_shown(path):
    assert kinds_in(path) == SIX


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
