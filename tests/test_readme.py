import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"


def readme() -> str:
    return README.read_text(encoding="utf-8")


def test_claude_code_install_commands():
    text = readme()
    assert "claude plugin marketplace add joe-yama/less-is-more-slide" in text
    assert "claude plugin install less-is-more-slide@less-is-more-slide" in text


def test_copilot_cli_install_commands():
    text = readme()
    assert "copilot plugin marketplace add joe-yama/less-is-more-slide" in text
    assert "copilot plugin install less-is-more-slide@less-is-more-slide" in text


def test_names_uv_as_a_requirement():
    text = readme()
    assert re.search(r"uv.*(必要|入れ)", text)
    assert "https://docs.astral.sh/uv/" in text


def test_points_to_the_sample_manuscript_and_its_command():
    text = readme()
    assert "examples/sample.md" in text
    assert "uv run plugin/skills/slide/scripts/build.py examples/sample.md -o sample.pptx" in text
    assert (ROOT / "examples" / "sample.md").is_file()
