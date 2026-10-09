# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""格子ファイル（または icon:<名前>）をドット絵の PNG にする。

使い方:
    pixel.py <格子.txt | icon:名前> -o <出力.png> [--scale N]
    pixel.py --list
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from slidekit.grid import GridError, icon_names, resolve
from slidekit.png import encode_png

DEFAULT_SCALE = 16
MIN_SCALE, MAX_SCALE = 1, 64


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pixel.py", description="格子をドット絵の PNG にする")
    p.add_argument("source", nargs="?", help="格子ファイル（.txt）か icon:<名前>")
    p.add_argument("-o", "--output", help="出力する PNG のパス")
    p.add_argument("--scale", type=int, default=DEFAULT_SCALE, help="拡大率 1〜64（既定 16）")
    p.add_argument("--list", action="store_true", help="同梱アイコンの名前を出す")
    return p


def _write_atomically(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def main(argv: list[str]) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1

    if args.list:
        print("\n".join(icon_names()))
        return 0
    if not args.source or not args.output:
        print("格子ファイルと -o の出力先が要ります", file=sys.stderr)
        return 1
    if not MIN_SCALE <= args.scale <= MAX_SCALE:
        print(f"拡大率は {MIN_SCALE}〜{MAX_SCALE} の整数です: {args.scale}", file=sys.stderr)
        return 1

    try:
        grid = resolve(args.source, Path.cwd())
    except GridError as e:
        for p in e.problems:
            where = f"{p.line}" if p.col is None else f"{p.line}:{p.col}"
            print(f"{args.source}:{where}: {p.message}", file=sys.stderr)
        return 1

    _write_atomically(Path(args.output), encode_png(grid, args.scale))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
