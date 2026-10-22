"""Установка скилла aar для Claude Code. Install the aar skill for Claude Code.

    python install.py                      # для всех проектов: ~/.claude или CLAUDE_CONFIG_DIR
    python install.py --project <папка>    # в один проект: <папка>/.claude и <папка>/CLAUDE.md
    python install.py --no-hook            # без хука Stop
    python install.py --no-claude-md       # без правила автозапуска в CLAUDE.md
    python install.py --lang en            # английский текст скилла и правила (по умолчанию русский)
    python install.py --uninstall [--project <папка>]

Что делает:
  1. копирует skills/aar (или skills-en/aar) в <.claude>/skills/aar;
  2. копирует hooks/aar_trigger_gate.py в <.claude>/hooks/ и подключает его в разделе Stop
     файла <.claude>/settings.json;
  3. создаёт журнал aar-log.md в папке настроек Claude Code, если его нет (при удалении журнал
     не трогается);
  4. вписывает правило автозапуска в CLAUDE.md (общий - в папке настроек, проекта - в корне
     проекта) между строками <!-- aar:start --> и <!-- aar:end -->. Повторная установка
     заменяет блок, удаление вырезает его; остальной текст, окончания строк и BOM не меняются.

Всё, что меняется, сначала проверяется: при повреждённом settings.json или неполном блоке
правила установщик останавливается, ничего не записав. Прежние версии изменённых файлов
лежат в папке настроек Claude Code: aar-backups/<время>/.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK_NAME = "aar_trigger_gate.py"
RULE_START = "<!-- aar:start -->"
RULE_END = "<!-- aar:end -->"
_START_LINE = re.compile(r"^[ \t]*<!-- aar:start -->[ \t]*$", re.MULTILINE)
_END_LINE = re.compile(r"^[ \t]*<!-- aar:end -->[ \t]*$", re.MULTILINE)
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


class InstallError(Exception):
    pass


def config_dir() -> Path:
    """Папка настроек Claude Code: CLAUDE_CONFIG_DIR, если задана, иначе ~/.claude."""
    custom = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(custom).expanduser() if custom else Path.home() / ".claude"


# --- текстовые файлы с сохранением окончаний строк и BOM ---------------------------------

def _read_text(path: Path) -> tuple[str, str, bool]:
    """Текст с окончаниями строк \\n, исходное окончание строк, был ли BOM."""
    raw = path.read_bytes() if path.is_file() else b""
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n"), newline, bom


def _write_text(path: Path, text: str, newline: str, bom: bool) -> None:
    data = text.replace("\n", newline).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + data)


# --- резервные копии -------------------------------------------------------------------

class Backup:
    """Одна папка aar-backups/<время>/ на запуск в папке настроек Claude Code (не в проекте, чтобы
    копии не попали в его git); создаётся, только если есть что сохранить."""

    def __init__(self, home: Path) -> None:
        self.root = home / "aar-backups" / time.strftime("%Y%m%d-%H%M%S")

    def save(self, path: Path, name: str) -> None:
        if not path.exists():
            return
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, target, dirs_exist_ok=True)
        else:
            shutil.copy2(path, target)


# --- правило в CLAUDE.md ---------------------------------------------------------------

def _rule_span(text: str, path: Path) -> tuple[int, int] | None:
    starts = list(_START_LINE.finditer(text))
    ends = list(_END_LINE.finditer(text))
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or ends[0].start() < starts[0].end():
        raise InstallError(
            f"{path}: блок правила aar неполный или повторён (строк {RULE_START}: {len(starts)}, "
            f"{RULE_END}: {len(ends)}). Поправьте блок вручную или удалите его целиком и запустите снова.")
    end = ends[0].end()
    if text[end:end + 1] == "\n":
        end += 1
    return starts[0].start(), end


def _strip_rule(text: str, path: Path) -> str:
    span = _rule_span(text, path)
    if span is None:
        return text
    before, after = text[:span[0]].rstrip("\n"), text[span[1]:].lstrip("\n")
    if before and after:
        return before + "\n\n" + after
    return before + "\n" if before else after


def _journal_text(journal: Path) -> str:
    try:
        return "~/" + journal.relative_to(Path.home()).as_posix()
    except ValueError:
        return journal.as_posix()


def write_rule(claude_md: Path, lang: str, journal: Path, backup: Backup) -> None:
    text, newline, bom = _read_text(claude_md)
    rest = _strip_rule(text, claude_md).rstrip("\n")
    block = f"{RULE_START}\n{RULE[lang].format(journal=_journal_text(journal))}\n{RULE_END}\n"
    backup.save(claude_md, "CLAUDE.md")
    _write_text(claude_md, (rest + "\n\n" if rest else "") + block, newline, bom)


def remove_rule(claude_md: Path, backup: Backup) -> bool:
    if not claude_md.is_file():
        return False
    text, newline, bom = _read_text(claude_md)
    new = _strip_rule(text, claude_md)
    if new == text:
        return False
    backup.save(claude_md, "CLAUDE.md")
    if new.strip():
        _write_text(claude_md, new, newline, bom)
    else:
        claude_md.unlink()
    return True


# --- хук в settings.json ---------------------------------------------------------------

def _load_settings(path: Path) -> dict:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InstallError(f"{path}: не JSON ({exc}). Исправьте файл или поставьте с --no-hook.") from exc
    if not isinstance(data, dict):
        raise InstallError(f"{path}: ожидался объект JSON.")
    return data


def _save_settings(path: Path, data: dict, backup: Backup) -> None:
    backup.save(path, "settings.json")
    if not data:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _is_ours(entry: object) -> bool:
    return isinstance(entry, dict) and HOOK_NAME in str(entry.get("command", ""))


def _works(python: str) -> bool:
    try:
        done = subprocess.run([python, "-c", "import sys; sys.exit(sys.version_info < (3, 9))"],
                              capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0


def find_python() -> tuple[str, str]:
    """Имя Python для проекта (переносимое) и полный путь для общей установки."""
    for name in ("python3", "python"):
        found = shutil.which(name)
        if found and "WindowsApps" not in found and _works(found):
            return name, Path(found).as_posix()
    return Path(sys.executable).as_posix(), Path(sys.executable).as_posix()


def hook_command(claude_dir: Path, project: bool) -> str:
    portable, absolute = find_python()
    if project:
        return f'{portable} "$CLAUDE_PROJECT_DIR/.claude/hooks/{HOOK_NAME}"'
    return f'"{absolute}" "{(claude_dir / "hooks" / HOOK_NAME).as_posix()}"'


def register_hook(data: dict, command: str) -> bool:
    stop = data.setdefault("hooks", {}).setdefault("Stop", [])
    for group in stop:
        if isinstance(group, dict):
            for hook in group.get("hooks", []):
                if _is_ours(hook):
                    if hook.get("command") == command:
                        return False
                    hook["command"] = command
                    return True
    stop.append({"hooks": [{"type": "command", "command": command}]})
    return True


def unregister_hook(data: dict) -> bool:
    hooks = data.get("hooks")
    stop = hooks.get("Stop") if isinstance(hooks, dict) else None
    if not isinstance(stop, list):
        return False
    kept, changed = [], False
    for group in stop:
        if isinstance(group, dict) and isinstance(group.get("hooks"), list):
            rest = [h for h in group["hooks"] if not _is_ours(h)]
            changed |= len(rest) != len(group["hooks"])
            if rest:
                kept.append({**group, "hooks": rest})
        else:
            kept.append(group)
    if not changed:
        return False
    if kept:
        hooks["Stop"] = kept
    else:
        del hooks["Stop"]
        if not hooks:
            del data["hooks"]
    return True


# --- установка и удаление --------------------------------------------------------------

def _remove_if_empty(*dirs: Path) -> None:
    for d in dirs:
        try:
            d.rmdir()
        except OSError:
            pass


def install(claude_dir: Path, home: Path, project: bool, with_hook: bool, lang: str = "ru",
            claude_md: Path | None = None) -> None:
    skill_src = HERE / ("skills-en" if lang == "en" else "skills") / "aar"
    settings_path = claude_dir / "settings.json"

    # Сначала проверки: ничего не пишется, пока не ясно, что всё запишется.
    settings = _load_settings(settings_path) if with_hook else {}
    if claude_md is not None and claude_md.is_file():
        _rule_span(_read_text(claude_md)[0], claude_md)

    backup = Backup(home)
    skill_dst = claude_dir / "skills" / "aar"
    if skill_dst.exists():
        backup.save(skill_dst, "skill-aar")
        shutil.rmtree(skill_dst)
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
        write_rule(claude_md, lang, journal, backup)
        print(f"правило автозапуска вписано в {claude_md}")

    if with_hook:
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / "hooks" / HOOK_NAME, hooks_dir / HOOK_NAME)
        command = hook_command(claude_dir, project)
        if register_hook(settings, command):
            _save_settings(settings_path, settings, backup)
            print(f"хук подключён в {settings_path}: {command}")
        else:
            print(f"хук уже был подключён в {settings_path}, файл хука обновлён")

    if backup.root.exists():
        print(f"прежние версии изменённых файлов: {backup.root}")


def uninstall(claude_dir: Path, home: Path, claude_md: Path) -> None:
    settings_path = claude_dir / "settings.json"
    settings = _load_settings(settings_path)
    if claude_md.is_file():
        _rule_span(_read_text(claude_md)[0], claude_md)

    backup = Backup(home)
    if remove_rule(claude_md, backup):
        print(f"правило автозапуска убрано из {claude_md}")
    skill_dst = claude_dir / "skills" / "aar"
    if skill_dst.exists():
        shutil.rmtree(skill_dst)
        print(f"удалён скилл: {skill_dst}")
    hook = claude_dir / "hooks" / HOOK_NAME
    if hook.exists():
        hook.unlink()
        print(f"удалён хук: {hook}")
    if unregister_hook(settings):
        _save_settings(settings_path, settings, backup)
        print(f"хук отключён в {settings_path}")
    _remove_if_empty(claude_dir / "skills", claude_dir / "hooks")
    print("журнал aar-log.md и карты проверок .claude/aar/ оставлены")
    if backup.root.exists():
        print(f"прежние версии изменённых файлов: {backup.root}")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="Установка скилла aar для Claude Code")
    parser.add_argument("--project", type=Path, help="папка проекта; без неё - для всех проектов (~/.claude или CLAUDE_CONFIG_DIR)")
    parser.add_argument("--no-hook", action="store_true", help="не ставить хук Stop")
    parser.add_argument("--no-claude-md", action="store_true", help="не вписывать правило автозапуска в CLAUDE.md")
    parser.add_argument("--lang", choices=("ru", "en"), default="ru", help="язык текста скилла и правила")
    parser.add_argument("--uninstall", action="store_true", help="удалить скилл, хук и правило")
    args = parser.parse_args(argv)

    home = config_dir()
    if args.project:
        if not args.project.is_dir():
            print(f"нет такой папки: {args.project}", file=sys.stderr)
            return 1
        claude_dir = args.project.resolve() / ".claude"
        claude_md = args.project.resolve() / "CLAUDE.md"
    else:
        claude_dir = home
        claude_md = home / "CLAUDE.md"

    try:
        if args.uninstall:
            uninstall(claude_dir, home, claude_md)
        else:
            install(claude_dir, home, bool(args.project), not args.no_hook, args.lang,
                    None if args.no_claude_md else claude_md)
            print("Готово. Перезапустите Claude Code, чтобы он увидел скилл, хук и правило.")
    except InstallError as exc:
        print(f"Остановлено, ничего не записано: {exc}", file=sys.stderr)
        return 1
    if args.project and claude_dir.exists():
        _remove_if_empty(claude_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
