"""Установщик: ставит скилл, журнал и хук, не дублирует хук и не трогает чужие настройки."""

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


def test_global_install_and_uninstall(tmp_path: Path) -> None:
    home = tmp_path / "home"
    claude = home / ".claude"
    claude.mkdir(parents=True)
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
    assert any(p.name.startswith("aar.bak-") for p in (claude / "skills").iterdir())

    assert _run(home, "--uninstall").returncode == 0
    assert not (claude / "skills" / "aar").exists()
    assert not (claude / "hooks" / "aar_trigger_gate.py").exists()
    assert _stop_commands(settings) == [FOREIGN["command"]]
    assert (claude / "aar-log.md").is_file()


def test_project_install_uses_project_dir(tmp_path: Path) -> None:
    home = tmp_path / "home"
    project = tmp_path / "proj"
    home.mkdir()
    project.mkdir()
    assert _run(home, "--project", str(project)).returncode == 0
    commands = _stop_commands(project / ".claude" / "settings.json")
    assert commands and "$CLAUDE_PROJECT_DIR/.claude/hooks/aar_trigger_gate.py" in commands[0]
    assert (project / ".claude" / "skills" / "aar" / "SKILL.md").is_file()
    assert (home / ".claude" / "aar-log.md").is_file()
    assert not (home / ".claude" / "skills").exists()


def test_respects_claude_config_dir(tmp_path: Path) -> None:
    home = tmp_path / "home"
    config = tmp_path / "config"
    home.mkdir()
    assert _run(home, config_dir=config).returncode == 0
    assert (config / "skills" / "aar" / "SKILL.md").is_file()
    assert (config / "aar-log.md").is_file()
    assert "aar_trigger_gate.py" in _stop_commands(config / "settings.json")[0]
    assert not (home / ".claude").exists()


def test_english_version(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    assert _run(home, "--lang", "en", "--no-hook").returncode == 0
    text = (home / ".claude" / "skills" / "aar" / "SKILL.md").read_text(encoding="utf-8")
    assert "name: aar" in text
    assert "## Step 1" in text
    assert "method:" in (home / ".claude" / "aar-log.md").read_text(encoding="utf-8")


def test_no_hook_leaves_settings_alone(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    assert _run(home, "--no-hook").returncode == 0
    assert (home / ".claude" / "skills" / "aar" / "SKILL.md").is_file()
    assert not (home / ".claude" / "settings.json").exists()


def test_claude_md_rule_added_once_and_removed(tmp_path: Path) -> None:
    home = tmp_path / "home"
    claude = home / ".claude"
    claude.mkdir(parents=True)
    claude_md = claude / "CLAUDE.md"
    claude_md.write_text("# Мои правила\n\nОтвечай коротко.\n", encoding="utf-8")

    assert _run(home).returncode == 0
    text = claude_md.read_text(encoding="utf-8")
    assert text.startswith("# Мои правила\n\nОтвечай коротко.\n")
    assert text.count("<!-- aar:start -->") == 1
    assert "скилл `aar`" in text
    assert (claude / "aar-log.md").as_posix() in text

    assert _run(home).returncode == 0
    assert claude_md.read_text(encoding="utf-8").count("<!-- aar:start -->") == 1

    assert _run(home, "--uninstall").returncode == 0
    assert claude_md.read_text(encoding="utf-8") == "# Мои правила\n\nОтвечай коротко.\n"


def test_claude_md_rule_in_project_root_and_english(tmp_path: Path) -> None:
    home = tmp_path / "home"
    project = tmp_path / "proj"
    home.mkdir()
    project.mkdir()
    assert _run(home, "--project", str(project), "--lang", "en").returncode == 0
    text = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert "run the `aar` skill" in text
    assert not (home / ".claude" / "CLAUDE.md").exists()


def test_no_claude_md_flag(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    assert _run(home, "--no-claude-md").returncode == 0
    assert not (home / ".claude" / "CLAUDE.md").exists()


def test_broken_settings_is_not_overwritten(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    settings = home / ".claude" / "settings.json"
    settings.write_text("{ broken", encoding="utf-8")
    done = _run(home)
    assert done.returncode != 0
    assert settings.read_text(encoding="utf-8") == "{ broken"
