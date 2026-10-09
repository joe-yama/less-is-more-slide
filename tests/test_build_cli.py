import subprocess
import sys
from pathlib import Path

from pptx import Presentation

import build

GOOD = "# 四半期の振り返り\n営業部 山田\n---\n結論から言うと、来期は値上げしない。\n"
BAD = (
    "# 題\n"
    "---\n"  # 2
    "## 見出し\n"  # 3
    "- 😀 絵文字\n"  # 4
    "- 二\n- 三\n- 四\n- 五\n- 六\n"  # 5-9: 6 項目目は 9 行目
)


def test_success_writes_pptx_and_exits_0(tmp_path):
    src = tmp_path / "a.md"
    src.write_text(GOOD, encoding="utf-8")
    out = tmp_path / "a.pptx"
    assert build.main([str(src), "-o", str(out)]) == 0
    assert len(Presentation(str(out)).slides) == 2


def test_violations_one_line_each_with_path_and_line(tmp_path, capsys):
    src = tmp_path / "bad.md"
    src.write_text(BAD, encoding="utf-8")
    out = tmp_path / "bad.pptx"
    assert build.main([str(src), "-o", str(out)]) == 1
    lines = capsys.readouterr().err.splitlines()
    assert len(lines) >= 2
    assert all(line.startswith(f"{src}:") for line in lines)
    nums = [line[len(str(src)) + 1 :].split(":", 1)[0] for line in lines]
    assert "4" in nums and "9" in nums
    assert all(n.isdigit() for n in nums)
    assert not out.exists()


def test_failure_keeps_existing_output(tmp_path):
    src = tmp_path / "bad.md"
    src.write_text(BAD, encoding="utf-8")
    out = tmp_path / "keep.pptx"
    out.write_bytes(b"old")
    assert build.main([str(src), "-o", str(out)]) == 1
    assert out.read_bytes() == b"old"


def test_render_failure_keeps_existing_output(tmp_path, monkeypatch):
    src = tmp_path / "a.md"
    src.write_text(GOOD, encoding="utf-8")
    out = tmp_path / "keep.pptx"
    out.write_bytes(b"old")

    def boom(deck, path):
        Path(path).write_bytes(b"partial")
        raise RuntimeError("x")

    monkeypatch.setattr(build, "render", boom)
    try:
        build.main([str(src), "-o", str(out)])
    except RuntimeError:
        pass
    assert out.read_bytes() == b"old"
    assert [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"] == []


def test_grid_reference_resolves_relative_to_manuscript(tmp_path):
    (tmp_path / "g.txt").write_text("#+\n*.\n", encoding="utf-8")
    src = tmp_path / "a.md"
    src.write_text("# 題\n---\n## 図\n![絵](g.txt)\n", encoding="utf-8")
    out = tmp_path / "a.pptx"
    assert build.main([str(src), "-o", str(out)]) == 0


def test_missing_manuscript_exits_1(tmp_path, capsys):
    assert build.main([str(tmp_path / "none.md"), "-o", str(tmp_path / "o.pptx")]) == 1
    assert "none.md" in capsys.readouterr().err


def test_wrong_arguments_exit_1():
    assert build.main([]) == 1


def test_runs_as_script(tmp_path):
    src = tmp_path / "a.md"
    src.write_text(GOOD, encoding="utf-8")
    out = tmp_path / "a.pptx"
    r = subprocess.run(
        [sys.executable, build.__file__, str(src), "-o", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert out.exists()


def test_output_without_o_is_rejected(tmp_path):
    src = tmp_path / "a.md"
    src.write_text(GOOD, encoding="utf-8")
    out = tmp_path / "a.pptx"
    assert build.main([str(src), str(out)]) != 0
    assert not out.exists()
    assert build.main([str(src)]) != 0
