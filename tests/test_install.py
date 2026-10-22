"""Установщик: ставит скилл, журнал, хук и правило; не теряет чужое; удаление не оставляет хвостов."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

INSTALL = Path(__file__).resolve().parents[1] / "install.py"
FOREIGN = {"type": "command", "command": "python other_gate.py"}


def _run(home: Path, *args: str, config_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
    env.update(HOME=str(home), USERPROFILE=str(home), PYTHONIOENCODING="utf-8")
    if config_dir is not None:
        env["CLAUDE_CONFIG_DIR"] = str(config_dir)
    return subprocess.run([sys.executable, str(INSTALL), *args], capture_output=True, text=True,
                          encoding="utf-8", env=env, check=False)


def _stop_commands(settings: Path) -> list[str]:
    data = json.loads(settings.read_text(encoding="utf-8"))
    return [h["command"] for g in data.get("hooks", {}).get("Stop", []) for h in g["hooks"]]


def _home(tmp_path: Path) -> tuple[Path, Path]:
    home = tmp_path / "home"
    claude = home / ".claude"
    claude.mkdir(parents=True)
    return home, claude


def test_global_install_and_uninstall(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    settings = claude / "settings.json"
    settings.write_text(json.dumps({"model": "opus", "hooks": {"Stop": [{"hooks": [FOREIGN]}]}}), encoding="utf-8")

    done = _run(home)
    assert done.returncode == 0, done.stderr
    assert (claude / "skills" / "aar" / "SKILL.md").is_file()
    assert (claude / "skills" / "aar" / "templates" / "checks-map.md").is_file()
    assert (claude / "hooks" / "aar_trigger_gate.py").is_file()
    assert (claude / "aar-log.md").is_file()
    commands = _stop_commands(settings)
    assert FOREIGN["command"] in commands
    assert sum("aar_trigger_gate.py" in c for c in commands) == 1
    assert json.loads(settings.read_text(encoding="utf-8"))["model"] == "opus"

    (claude / "aar-log.md").write_text("запись\n", encoding="utf-8")
    assert _run(home).returncode == 0
    assert sum("aar_trigger_gate.py" in c for c in _stop_commands(settings)) == 1
    assert (claude / "aar-log.md").read_text(encoding="utf-8") == "запись\n"
    # Копия прежнего скилла лежит вне skills/, иначе Claude Code видит второй скилл aar.
    assert [p.name for p in (claude / "skills").iterdir()] == ["aar"]
    assert list((claude / "aar-backups").glob("*/skill-aar/SKILL.md"))

    assert _run(home, "--uninstall").returncode == 0
    assert not (claude / "skills").exists()
    assert not (claude / "hooks").exists()
    assert _stop_commands(settings) == [FOREIGN["command"]]
    assert (claude / "aar-log.md").is_file()


def test_hook_uses_python_from_path_not_installer(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    assert _run(home, "--no-claude-md").returncode == 0
    command = _stop_commands(claude / "settings.json")[0]
    assert "WindowsApps" not in command
    python = command.split('"')[1]
    assert subprocess.run([python, "-c", "pass"], check=False).returncode == 0


def test_project_install_is_portable_and_uninstall_is_clean(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    project = tmp_path / "proj"
    project.mkdir()
    assert _run(home, "--project", str(project)).returncode == 0
    command = _stop_commands(project / ".claude" / "settings.json")[0]
    assert command.split()[0] in ("python3", "python")
    assert '"$CLAUDE_PROJECT_DIR/.claude/hooks/aar_trigger_gate.py"' in command
    rule = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert "`~/.claude/aar-log.md`" in rule
    assert str(tmp_path) not in rule and tmp_path.as_posix() not in rule
    assert (claude / "aar-log.md").is_file()
    assert not (claude / "skills").exists()

    assert _run(home, "--project", str(project), "--uninstall").returncode == 0
    assert sorted(p.name for p in project.iterdir()) == []


def test_respects_claude_config_dir(tmp_path: Path) -> None:
    home = tmp_path / "home"
    config = tmp_path / "config"
    home.mkdir()
    assert _run(home, config_dir=config).returncode == 0
    assert (config / "skills" / "aar" / "SKILL.md").is_file()
    assert (config / "aar-log.md").is_file()
    assert (config / "CLAUDE.md").is_file()
    assert "aar_trigger_gate.py" in _stop_commands(config / "settings.json")[0]
    assert not (home / ".claude").exists()


def test_english_version(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    assert _run(home, "--lang", "en", "--no-hook").returncode == 0
    text = (claude / "skills" / "aar" / "SKILL.md").read_text(encoding="utf-8")
    assert "name: aar" in text and "## Step 1" in text
    assert "method:" in (claude / "aar-log.md").read_text(encoding="utf-8")
    assert "run the `aar` skill" in (claude / "CLAUDE.md").read_text(encoding="utf-8")


def test_no_hook_and_no_claude_md(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    assert _run(home, "--no-hook", "--no-claude-md").returncode == 0
    assert (claude / "skills" / "aar" / "SKILL.md").is_file()
    assert not (claude / "settings.json").exists()
    assert not (claude / "CLAUDE.md").exists()


def test_claude_md_bytes_kept_through_install_and_uninstall(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    claude_md = claude / "CLAUDE.md"
    original = "﻿# Мои правила\r\n\r\nОтвечай коротко.\r\n".encode("utf-8")
    claude_md.write_bytes(original)

    assert _run(home).returncode == 0
    raw = claude_md.read_bytes()
    assert raw.startswith(original.rstrip(b"\r\n"))
    assert b"\n" not in raw.replace(b"\r\n", b"")
    assert raw.count(b"<!-- aar:start -->") == 1

    assert _run(home).returncode == 0
    assert claude_md.read_bytes().count(b"<!-- aar:start -->") == 1

    assert _run(home, "--uninstall").returncode == 0
    assert claude_md.read_bytes() == original
    assert list((claude / "aar-backups").glob("*/CLAUDE.md"))


def test_lang_switch_replaces_rule(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    assert _run(home, "--no-hook").returncode == 0
    assert _run(home, "--no-hook", "--lang", "en").returncode == 0
    text = (claude / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.count("<!-- aar:start -->") == 1
    assert "run the `aar` skill" in text and "запускаю скилл" not in text


def test_rule_in_the_middle_and_inline_markers_are_safe(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    claude_md = claude / "CLAUDE.md"
    head = "# A\n\nПометки `<!-- aar:start -->` и `<!-- aar:end -->` - про скилл.\n"
    claude_md.write_text(head, encoding="utf-8")
    assert _run(home, "--no-hook").returncode == 0
    claude_md.write_text(claude_md.read_text(encoding="utf-8") + "\n# B\n", encoding="utf-8")
    assert _run(home, "--no-hook", "--uninstall").returncode == 0
    assert claude_md.read_text(encoding="utf-8") == head + "\n# B\n"


def test_broken_block_stops_before_any_write(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    claude_md = claude / "CLAUDE.md"
    broken = "# rules\n\n<!-- aar:start -->\nправило без конца\n\nkeep me\n"
    claude_md.write_text(broken, encoding="utf-8")
    for args in ((), ("--uninstall",)):
        done = _run(home, *args)
        assert done.returncode == 1
        assert "ничего не записано" in done.stderr
        assert claude_md.read_text(encoding="utf-8") == broken
    assert not (claude / "skills").exists()
    assert not (claude / "settings.json").exists()


def test_broken_settings_stops_before_any_write(tmp_path: Path) -> None:
    home, claude = _home(tmp_path)
    settings = claude / "settings.json"
    settings.write_text("{ broken", encoding="utf-8")
    done = _run(home)
    assert done.returncode == 1
    assert settings.read_text(encoding="utf-8") == "{ broken"
    assert not (claude / "skills").exists()
    assert not (claude / "CLAUDE.md").exists()
