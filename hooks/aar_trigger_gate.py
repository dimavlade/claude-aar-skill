"""Stop hook for the aar skill: if I correct my own delivered work, the review has started.

Ворота запуска разбора. Текст триггера в SKILL.md читается только тогда, когда скилл уже вызван,
поэтому «я снимаю эту рекомендацию» или «я ошибся» без вызова разбора проходят молча. Хук смотрит
мой текст этого хода (после последней реплики пользователя) и возвращает ход один раз, если в нём
есть собственное исправление сданного, а вызова скилла `aar` в этом ходе нет.

## Что ловится

«я ошибся», «был неправ», «снимаю», «отзываю», «беру назад», «идёт против», «противоречит цели»,
«это было неполно», «поправка:», «в первой версии ... ошибочно»; по-английски - "I was wrong",
"I made a mistake", "my mistake", "I retract", "I take that back", "I stand corrected",
"correction:", "that was wrong/incorrect/incomplete". Текст в «кавычках» и `коде` не считается.

## Что снимает ворота

Вызов `Skill` со скиллом `aar` в этом ходе; повторная остановка (`stop_hook_active`); скилла
`aar` нет ни в проекте (`.claude/skills/aar` в папке проекта или выше), ни в `~/.claude/skills/aar` (или `$CLAUDE_CONFIG_DIR/skills/aar`).

Хук ничего не пишет на диск и не ходит в сеть.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SELF_FIX = re.compile(
    # Русский
    r"\bя\s+(?:\w+\s+){0,2}?ошиб\w*|\bошибся\b|\bошиблась\b|был[аи]?\s+неправ\w*|"
    r"\bснимаю\b(?!\s+(?:\w+\s+){0,3}?(?:кадр|данн|замер|срез|выгрузк|цифр|скриншот|снимок|видео))|"
    r"\bотзываю\b|беру\s+(?:\w+\s+){0,2}?назад|ид[её]т\s+против|противоречит\s+(?:\w+\s+){0,2}?цел\w*|"
    r"это\s+было\s+(?:неполно|неверно)|\bпоправка\s*:|"
    r"в\s+первой\s+(?:версии|редакции)\s+(?:\w+\s+){0,6}?(?:ошибочно|неверно)|"
    # English
    r"\bI\s+was\s+wrong\b|\bI\s+made\s+(?:a|an)\s+(?:\w+\s+)?(?:mistake|error)\b|\bmy\s+mistake\b|"
    r"\bI\s+retract\b|\bI\s+take\s+(?:that|it|this)\s+back\b|\bI\s+stand\s+corrected\b|"
    r"\bcorrection\s*:|\b(?:that|this)\s+was\s+(?:wrong|incorrect|incomplete)\b",
    re.IGNORECASE,
)

_QUOTED = re.compile(r"```.*?```|«[^»\n]*»|`[^`\n]*`|\"[^\"\n]*\"", re.DOTALL)


def _rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    except OSError:
        return []
    return rows


def _is_user_turn(row: dict[str, Any]) -> bool:
    if row.get("type") != "user" or row.get("isMeta") or row.get("toolUseResult") is not None:
        return False
    message = row.get("message")
    if not isinstance(message, dict):
        return False
    content = message.get("content")
    if isinstance(content, list):
        return any(isinstance(p, dict) and p.get("type") == "text" for p in content)
    return isinstance(content, str)


def this_turn(rows: list[dict[str, Any]]) -> tuple[str, bool]:
    """Мой текст после последней реплики пользователя и был ли в нём вызов скилла aar."""
    texts: list[str] = []
    aar_called = False
    for row in reversed(rows):
        if _is_user_turn(row):
            break
        message = row.get("message")
        if row.get("type") != "assistant" or not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str):
            texts.append(content)
            continue
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text":
                texts.append(str(part.get("text", "")))
            elif part.get("type") == "tool_use" and part.get("name") == "Skill":
                skill = str((part.get("input") or {}).get("skill", ""))
                if skill.split(":")[-1] == "aar":
                    aar_called = True
    return "\n".join(reversed(texts)), aar_called


def self_fixes(answer: str) -> list[str]:
    bare = _QUOTED.sub("", answer)
    return [m.group(0) for m in SELF_FIX.finditer(bare)]


def skill_installed(project: Path, home: Path) -> bool:
    candidates = [p / ".claude" / "skills" / "aar" for p in (project, *project.parents)]
    candidates.append(home / ".claude" / "skills" / "aar")
    custom = os.environ.get("CLAUDE_CONFIG_DIR")
    if custom:
        candidates.append(Path(custom).expanduser() / "skills" / "aar")
    return any((d / "SKILL.md").is_file() for d in candidates)


def main() -> int:
    sys.stdin.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(event, dict) or event.get("stop_hook_active"):
        return 0
    if not skill_installed(Path(str(event.get("cwd") or ".")), Path.home()):
        return 0
    raw = event.get("transcript_path")
    answer, aar_called = "", False
    if isinstance(raw, str) and raw and Path(raw).is_file():
        answer, aar_called = this_turn(_rows(Path(raw)))
    if not answer:
        answer = str(event.get("last_assistant_message") or "")
    if aar_called:
        return 0
    found = self_fixes(answer)
    if not found:
        return 0
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sys.stderr.write(
        "В ответе исправлено собственное сданное (" + ", ".join(sorted(set(found)))[:200] + "), "
        "а разбор не запущен. Поправка закрывает случай, а не класс. Запусти скилл aar: "
        "нашёл пользователь - режим 2 (мета), нашёл сам - режим 1.\n"
        "Your answer corrects your own delivered work, but the aar review was not run. "
        "Run the aar skill: mode 2 if the user found the mistake, mode 1 if you did.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
