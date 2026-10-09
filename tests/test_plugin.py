import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
MANIFEST = PLUGIN / ".claude-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
WRITER = PLUGIN / "agents" / "writer.md"
CRITIC = PLUGIN / "agents" / "critic.md"
FIXTURE = ROOT / "tests" / "fixtures" / "ai_tells.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter(path: Path) -> tuple[dict[str, str], str]:
    m = re.match(r"---\n(.*?)\n---\n(.*)", path.read_text(encoding="utf-8"), re.DOTALL)
    assert m, f"{path.name} に frontmatter がない"
    fields = {}
    for ln in m.group(1).splitlines():
        key, _, value = ln.partition(":")
        fields[key.strip()] = value.strip()
    return fields, m.group(2)


def tool_list(fields: dict[str, str]) -> list[str]:
    return [t.strip() for t in fields["tools"].split(",")]


def test_plugin_manifest_has_the_required_fields():
    m = load(MANIFEST)
    assert m["name"] == "less-is-more-slide"
    for key in ("version", "description", "license"):
        assert isinstance(m[key], str) and m[key], key
    assert m["license"] == "MIT"
    assert m["author"]["name"]


def test_marketplace_lists_exactly_the_one_plugin_from_plugin_dir():
    m = load(MARKETPLACE)
    assert m["name"] and m["owner"]["name"]
    assert len(m["plugins"]) == 1
    entry = m["plugins"][0]
    assert entry["name"] == load(MANIFEST)["name"] == "less-is-more-slide"
    assert entry["source"] == "./plugin"
    assert (ROOT / entry["source"] / ".claude-plugin" / "plugin.json").is_file()


def test_critic_can_only_read():
    fields, _ = frontmatter(CRITIC)
    assert fields["name"] == "critic"
    assert tool_list(fields) == ["Read", "Glob", "Grep"]


def test_writer_tools_and_name():
    fields, _ = frontmatter(WRITER)
    assert fields["name"] == "writer"
    assert tool_list(fields) == ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]


def test_both_agents_use_the_slide_skill():
    for path in (WRITER, CRITIC):
        fields, body = frontmatter(path)
        assert fields["skills"] == "[slide]", path.name
        assert "Skill `slide`" in body, path.name
        assert "references/writing.md" in body, path.name


def test_critic_body_forbids_writing_and_fixes_the_reply_format():
    _, body = frontmatter(CRITIC)
    assert "書き換えない" in body
    for col in ("スライド番号", "引用", "書き直し"):
        assert col in body


def test_writer_body_requires_the_generator_and_both_paths():
    _, body = frontmatter(WRITER)
    assert "build.py" in body
    assert "references/format.md" in body
    assert "直接編集" in body
    assert "パス" in body


def test_ai_tells_fixture_plants_five_kinds():
    text = FIXTURE.read_text(encoding="utf-8")
    planted = {
        2: "革新的",
        3: "- 対応時間が短くなる\n- 担当者の負担が減る\n- 満足度が上がる",
        4: "なぜ今チャットボットなのか？",
        7: "本日のアジェンダ",
        12: "見ていきましょう",
    }
    for n, needle in planted.items():
        assert needle in text, n


def test_agents_use_the_skill_folder_path_given_in_the_message_first():
    for path in (WRITER, CRITIC):
        _, body = frontmatter(path)
        assert "渡された Skill のフォルダ" in body, path.name
        assert body.index("渡された Skill のフォルダ") < body.index("探す"), path.name
    _, writer = frontmatter(WRITER)
    assert "<渡されたフォルダ>/scripts/build.py" in writer
    _, critic = frontmatter(CRITIC)
    assert "<渡されたフォルダ>/references/writing.md" in critic
