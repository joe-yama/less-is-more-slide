"""添え訳のない原稿の出力が変わらないことを、部品ごとの SHA-256 で固定する。

基準 `fixtures/sample_parts.json` は、添え訳を足す前のコードで `examples/sample.md` から作った
PPTX の、`docProps/core.xml`（日時が入る）を除く部品の SHA-256。

基準を作り直してよい条件（design.md「後方互換は部品ごとのハッシュで固定する」）:
python-pptx や lxml などの版の更新で、添え訳と関係なくハッシュが変わったときだけ。
更新前のコードの出力と比べて、違いが版の更新によるものだと確かめたうえで、
その版の更新の変更の中で作り直す。添え訳の変更のために作り直してはならない。
"""

import hashlib
import json
import zipfile
from pathlib import Path

from slidekit.manuscript import parse
from slidekit.render import render

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
BASELINE = Path(__file__).resolve().parent / "fixtures" / "sample_parts.json"
EXCLUDED = {"docProps/core.xml"}


def part_hashes(pptx: Path) -> dict[str, str]:
    with zipfile.ZipFile(pptx) as z:
        return {
            n: hashlib.sha256(z.read(n)).hexdigest()
            for n in sorted(z.namelist())
            if n not in EXCLUDED
        }


def build_sample(out: Path) -> dict[str, str]:
    text = (EXAMPLES / "sample.md").read_text(encoding="utf-8")
    render(parse(text, EXAMPLES), out)
    return part_hashes(out)


def test_sample_output_matches_baseline(tmp_path):
    expected = json.loads(BASELINE.read_text(encoding="utf-8"))
    actual = build_sample(tmp_path / "sample.pptx")
    assert set(actual) == set(expected)
    assert {n: h for n, h in actual.items() if h != expected[n]} == {}
