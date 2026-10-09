import struct
import subprocess
import sys
from pathlib import Path

import pixel
from slidekit.grid import icon_names

SCRIPT = Path(pixel.__file__)


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_list_prints_14_names_one_per_line(capsys):
    assert pixel.main(["--list"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 14
    assert lines == icon_names()


def test_icon_default_scale_is_256(tmp_path):
    out = tmp_path / "gear.png"
    assert pixel.main(["icon:gear", "-o", str(out)]) == 0
    assert png_size(out) == (256, 256)


def test_explicit_scale(tmp_path):
    out = tmp_path / "gear.png"
    assert pixel.main(["icon:gear", "-o", str(out), "--scale", "2"]) == 0
    assert png_size(out) == (32, 32)


def test_grid_file(tmp_path):
    grid = tmp_path / "a.txt"
    grid.write_text("#+\n*.\n", encoding="utf-8")
    out = tmp_path / "a.png"
    assert pixel.main([str(grid), "-o", str(out), "--scale", "10"]) == 0
    assert png_size(out) == (20, 20)


def test_invalid_grid_exits_1_with_reason_and_writes_nothing(tmp_path, capsys):
    grid = tmp_path / "bad.txt"
    grid.write_text("###\n##x\n", encoding="utf-8")
    out = tmp_path / "bad.png"
    assert pixel.main([str(grid), "-o", str(out)]) == 1
    err = capsys.readouterr().err
    assert "2" in err and "3" in err and "x" in err
    assert not out.exists()


def test_invalid_grid_keeps_existing_output(tmp_path):
    grid = tmp_path / "bad.txt"
    grid.write_text("x\n", encoding="utf-8")
    out = tmp_path / "keep.png"
    out.write_bytes(b"old")
    assert pixel.main([str(grid), "-o", str(out)]) == 1
    assert out.read_bytes() == b"old"


def test_unknown_icon_exits_1(tmp_path, capsys):
    out = tmp_path / "x.png"
    assert pixel.main(["icon:nope", "-o", str(out)]) == 1
    assert "nope" in capsys.readouterr().err
    assert not out.exists()


def test_scale_out_of_range_exits_1(tmp_path):
    out = tmp_path / "x.png"
    for scale in ("0", "65"):
        assert pixel.main(["icon:gear", "-o", str(out), "--scale", scale]) == 1
    assert not out.exists()


def test_runs_as_a_standalone_script(tmp_path):
    out = tmp_path / "gear.png"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "icon:gear", "-o", str(out)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert png_size(out) == (256, 256)
