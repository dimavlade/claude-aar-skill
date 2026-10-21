"""Установка скилла aar для Claude Code. Install the aar skill for Claude Code.

    python install.py                      # для всех проектов: ~/.claude или CLAUDE_CONFIG_DIR
    python install.py --project <папка>    # в один проект: <папка>/.claude
    python install.py --no-hook            # только скилл, без хука Stop
    python install.py --lang en            # английский текст скилла (по умолчанию русский)
    python install.py --uninstall [--project <папка>]

Что делает:
  1. копирует skills/aar (или skills-en/aar) в <.claude>/skills/aar (прежняя версия - рядом, aar.bak-<время>);
  2. копирует hooks/aar_trigger_gate.py в <.claude>/hooks/;
  3. добавляет хук в раздел Stop файла <.claude>/settings.json (прежний файл - settings.json.bak-aar);
  4. создаёт журнал aar-log.md в папке настроек Claude Code, если его нет. Журнал при удалении не трогается.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK_NAME = "aar_trigger_gate.py"


def config_dir() -> Path:
    """Папка настроек Claude Code: CLAUDE_CONFIG_DIR, если задана, иначе ~/.claude."""
    custom = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(custom).expanduser() if custom else Path.home() / ".claude"


def _load_settings(path: Path) -> dict:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        sys.exit(f"{path}: не JSON ({exc}). Исправьте файл или поставьте с --no-hook.")
    if not isinstance(data, dict):
        sys.exit(f"{path}: ожидался объект JSON.")
    return data


def _save_settings(path: Path, data: dict) -> None:
    if path.is_file():
        shutil.copy2(path, path.with_name(path.name + ".bak-aar"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _is_ours(entry: object) -> bool:
    return isinstance(entry, dict) and HOOK_NAME in str(entry.get("command", ""))


def _hook_command(claude_dir: Path, project: bool) -> str:
    python = Path(sys.executable).as_posix()
    target = "$CLAUDE_PROJECT_DIR/.claude/hooks/" + HOOK_NAME if project else (claude_dir / "hooks" / HOOK_NAME).as_posix()
    return f'"{python}" "{target}"'


def register_hook(settings_path: Path, command: str) -> bool:
    data = _load_settings(settings_path)
    stop = data.setdefault("hooks", {}).setdefault("Stop", [])
    for group in stop:
        if isinstance(group, dict) and any(_is_ours(h) for h in group.get("hooks", [])):
            return False
    stop.append({"hooks": [{"type": "command", "command": command}]})
    _save_settings(settings_path, data)
    return True


def unregister_hook(settings_path: Path) -> bool:
    data = _load_settings(settings_path)
    stop = data.get("hooks", {}).get("Stop")
    if not isinstance(stop, list):
        return False
    changed = False
    kept = []
    for group in stop:
        if isinstance(group, dict) and isinstance(group.get("hooks"), list):
            hooks = [h for h in group["hooks"] if not _is_ours(h)]
            if len(hooks) != len(group["hooks"]):
                changed = True
            if hooks:
                kept.append({**group, "hooks": hooks})
        else:
            kept.append(group)
    if not changed:
        return False
    if kept:
        data["hooks"]["Stop"] = kept
    else:
        del data["hooks"]["Stop"]
    _save_settings(settings_path, data)
    return True


def install(claude_dir: Path, home: Path, project: bool, with_hook: bool, lang: str = "ru") -> None:
    skill_src = HERE / ("skills-en" if lang == "en" else "skills") / "aar"
    skill_dst = claude_dir / "skills" / "aar"
    if skill_dst.exists():
        backup = skill_dst.with_name("aar.bak-" + time.strftime("%Y%m%d-%H%M%S"))
        shutil.move(str(skill_dst), str(backup))
        print(f"прежний скилл сохранён: {backup}")
    shutil.copytree(skill_src, skill_dst)
    print(f"скилл: {skill_dst}")

    journal = home / "aar-log.md"
    if not journal.exists():
        journal.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_src / "templates" / "aar-log.md", journal)
        print(f"журнал создан: {journal}")
    else:
        print(f"журнал уже есть: {journal}")

    if not with_hook:
        return
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / "hooks" / HOOK_NAME, hooks_dir / HOOK_NAME)
    settings = claude_dir / "settings.json"
    if register_hook(settings, _hook_command(claude_dir, project)):
        print(f"хук добавлен в {settings}")
    else:
        print(f"хук уже был в {settings}, файл хука обновлён")


def uninstall(claude_dir: Path) -> None:
    skill_dst = claude_dir / "skills" / "aar"
    if skill_dst.exists():
        shutil.rmtree(skill_dst)
        print(f"удалён скилл: {skill_dst}")
    hook = claude_dir / "hooks" / HOOK_NAME
    if hook.exists():
        hook.unlink()
        print(f"удалён хук: {hook}")
    if unregister_hook(claude_dir / "settings.json"):
        print(f"хук убран из {claude_dir / 'settings.json'}")
    print("журнал aar-log.md оставлен")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="Установка скилла aar для Claude Code")
    parser.add_argument("--project", type=Path, help="папка проекта; без неё - для всех проектов (~/.claude или CLAUDE_CONFIG_DIR)")
    parser.add_argument("--no-hook", action="store_true", help="не ставить хук Stop")
    parser.add_argument("--lang", choices=("ru", "en"), default="ru", help="язык текста скилла")
    parser.add_argument("--uninstall", action="store_true", help="удалить скилл и хук")
    args = parser.parse_args(argv)

    home = config_dir()
    if args.project:
        if not args.project.is_dir():
            sys.exit(f"нет такой папки: {args.project}")
        claude_dir = args.project.resolve() / ".claude"
    else:
        claude_dir = home

    if args.uninstall:
        uninstall(claude_dir)
    else:
        install(claude_dir, home, bool(args.project), not args.no_hook, args.lang)
        print("Готово. Перезапустите Claude Code, чтобы он увидел скилл и хук.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
