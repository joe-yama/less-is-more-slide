# /// script
# requires-python = ">=3.11"
# dependencies = ["python-pptx"]
# ///
"""原稿（Markdown 風のテキスト）を PPTX にする。

使い方:
    build.py <原稿.md> -o <出力.pptx>
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from slidekit.manuscript import ManuscriptError, parse
from slidekit.render import render


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="build.py", description="原稿を PPTX にする")
    parser.add_argument("source", help="原稿のパス")
    parser.add_argument("-o", "--output", required=True, help="出力する PPTX のパス")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code == 0 else 1
    src, out = Path(args.source), Path(args.output)

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
