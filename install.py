"""Установка скилла aar для Claude Code. Install the aar skill for Claude Code.

    python install.py                      # для всех проектов: ~/.claude или CLAUDE_CONFIG_DIR
    python install.py --project <папка>    # в один проект: <папка>/.claude
    python install.py --no-hook            # только скилл, без хука Stop
    python install.py --lang en            # английский текст скилла (по умолчанию русский)
    python install.py --no-claude-md       # не вписывать правило автозапуска в CLAUDE.md
    python install.py --uninstall [--project <папка>]

Что делает:
  1. копирует skills/aar (или skills-en/aar) в <.claude>/skills/aar (прежняя версия - рядом, aar.bak-<время>);
  2. копирует hooks/aar_trigger_gate.py в <.claude>/hooks/;
  3. добавляет хук в раздел Stop файла <.claude>/settings.json (прежний файл - settings.json.bak-aar);
  4. создаёт журнал aar-log.md в папке настроек Claude Code, если его нет. Журнал при удалении не трогается;
  5. вписывает правило автозапуска в CLAUDE.md: общий (в папке настроек) или проекта (в корне проекта).
     Правило стоит между строками-границами <!-- aar:start --> и <!-- aar:end -->: повторная
     установка его заменяет, удаление вырезает. Прежний файл - CLAUDE.md.bak-aar.
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
RULE_START = "<!-- aar:start -->"
RULE_END = "<!-- aar:end -->"
RULE = {
    "ru": (
        "## Разбор ошибок в сданной работе (скилл aar)\n\n"
        "Если выяснилось, что сданное мной неверно - пользователь поправил меня, спросил «с чего ты\n"
        "взял?», или я сам пишу «ошибся», «поправка», «на самом деле» о своём прежнем ответе, - сразу,\n"
        "без напоминания, запускаю скилл `aar`. Ошибку нашёл пользователь - режим 2 (мета), нашёл я -\n"
        "режим 1. Новая задача или смена требований - не ошибка. Журнал разборов - `{journal}`,\n"
        "карта проверок проекта - `.claude/aar/checks-map.md`."
    ),
    "en": (
        "## Reviewing mistakes in delivered work (aar skill)\n\n"
        "If it turns out that something I delivered is wrong - the user corrected me, asked \"what\n"
        "makes you say that?\", or I write \"I was wrong\", \"correction\", \"actually\" about my own\n"
        "earlier answer - I run the `aar` skill right away, without being reminded. The user found it -\n"
        "mode 2 (meta); I found it - mode 1. A new task or changed requirements is not a mistake. The\n"
        "journal is `{journal}`, the project's checks map is `.claude/aar/checks-map.md`."
    ),
}


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


def _strip_rule(text: str) -> str:
    start = text.find(RULE_START)
    end = text.find(RULE_END, start)
    if start == -1 or end == -1:
        return text
    before = text[:start].rstrip("\n")
    after = text[end + len(RULE_END):].lstrip("\n")
    return before + ("\n\n" if before and after else "\n" if before else "") + after


def write_rule(claude_md: Path, lang: str, journal: Path) -> None:
    old = claude_md.read_text(encoding="utf-8-sig") if claude_md.is_file() else ""
    if old:
        shutil.copy2(claude_md, claude_md.with_name(claude_md.name + ".bak-aar"))
    rest = _strip_rule(old).rstrip("\n")
    block = f"{RULE_START}\n{RULE[lang].format(journal=journal.as_posix())}\n{RULE_END}\n"
    claude_md.parent.mkdir(parents=True, exist_ok=True)
    claude_md.write_text((rest + "\n\n" if rest else "") + block, encoding="utf-8")


def remove_rule(claude_md: Path) -> bool:
    if not claude_md.is_file():
        return False
    old = claude_md.read_text(encoding="utf-8-sig")
    new = _strip_rule(old)
    if new == old:
        return False
    shutil.copy2(claude_md, claude_md.with_name(claude_md.name + ".bak-aar"))
    claude_md.write_text(new, encoding="utf-8")
    return True


def install(claude_dir: Path, home: Path, project: bool, with_hook: bool, lang: str = "ru",
            claude_md: Path | None = None) -> None:
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

    if claude_md is not None:
        write_rule(claude_md, lang, journal)
        print(f"правило автозапуска вписано в {claude_md}")

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


def uninstall(claude_dir: Path, claude_md: Path) -> None:
    if remove_rule(claude_md):
        print(f"правило автозапуска убрано из {claude_md}")
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
    parser.add_argument("--no-claude-md", action="store_true", help="не вписывать правило автозапуска в CLAUDE.md")
    parser.add_argument("--uninstall", action="store_true", help="удалить скилл, хук и правило")
    args = parser.parse_args(argv)

    home = config_dir()
    if args.project:
        if not args.project.is_dir():
            sys.exit(f"нет такой папки: {args.project}")
        claude_dir = args.project.resolve() / ".claude"
        claude_md = args.project.resolve() / "CLAUDE.md"
    else:
        claude_dir = home
        claude_md = home / "CLAUDE.md"

    if args.uninstall:
        uninstall(claude_dir, claude_md)
    else:
        install(claude_dir, home, bool(args.project), not args.no_hook, args.lang,
                None if args.no_claude_md else claude_md)
        print("Готово. Перезапустите Claude Code, чтобы он увидел скилл и хук.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
