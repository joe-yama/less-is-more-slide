# /// script
# requires-python = ">=3.11"
# dependencies = ["python-pptx"]
# ///
"""原稿（Markdown 風のテキスト）を PPTX にする。

使い方:
    build.py <原稿.md> <出力.pptx>
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from slidekit.manuscript import ManuscriptError, parse
from slidekit.render import render


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("使い方: build.py <原稿.md> <出力.pptx>", file=sys.stderr)
        return 1
    src, out = Path(argv[0]), Path(argv[1])

    try:
        text = src.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"{src}: 原稿を読めません: {e}", file=sys.stderr)
        return 1

    try:
        deck = parse(text, src.resolve().parent)
    except ManuscriptError as e:
        for p in e.problems:
            print(f"{src}:{p.line}: {p.message}", file=sys.stderr)
        return 1

    # 途中で失敗しても既存の出力を壊さないよう、一時ファイルに書いて置き換える
    fd, tmp = tempfile.mkstemp(dir=out.parent, prefix=out.name, suffix=".tmp")
    os.close(fd)
    try:
        render(deck, Path(tmp))
        os.replace(tmp, out)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
