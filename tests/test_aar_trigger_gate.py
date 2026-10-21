"""Ворота запуска разбора: собственное исправление без вызова aar возвращает ход."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "aar_trigger_gate.py"
sys.path.insert(0, str(HOOK.parent))

import aar_trigger_gate as gate  # noqa: E402

# Исправления сданного, прошедшие без разбора.
MISSED = [
    "Отсюда видно, что моя рекомендация 2 идёт против этой цели. Рекомендацию 2 я снимаю.",
    "В первой редакции я написал «конверсий нет», это было неполно.",
    "Да, я ошибся: функция вызывается дважды.",
    "Поправка: событие отправляется только на главной.",
    "You're right, I was wrong about the cache size.",
    "I made a mistake in the migration order.",
    "Correction: the endpoint returns 404, not 500.",
    "I retract recommendation 3.",
]

CLEAN = [
    "Снял повторный срез кабинета, сейчас разбираю расхождения.",
    "Новая посадочная по-прежнему отвечает 404, старая - 200.",
    "Хук сработал на моём предыдущем ответе, оба срабатывания ложные.",
    "Пользователь показал снимок: в группе выбор «Не оптимизировать» доступен.",
    "Снимаю полные кадры, чтобы найти свободное место.",
    "Снимаю свежие данные кабинета с 09.10.",
    "The test was wrong-footed by a flaky network, rerunning it now.",
    "Error handling is done in the middleware.",
    "The message says \"I was wrong\" when the user cancels.",
]


@pytest.mark.parametrize("text", MISSED)
def test_missed_trigger_is_caught(text: str) -> None:
    assert gate.self_fixes(text), text


@pytest.mark.parametrize("text", CLEAN)
def test_clean_passes(text: str) -> None:
    assert not gate.self_fixes(text), gate.self_fixes(text)


def _skill(root: Path) -> None:
    d = root / ".claude" / "skills" / "aar"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: aar\n---\n", encoding="utf-8")


def _run(tmp_path: Path, answer: str, *, aar: bool = False, active: bool = False,
         project_skill: bool = True, home_skill: bool = False, config_skill: bool = False) -> int:
    project = tmp_path / "project"
    home = tmp_path / "home"
    (project / "src").mkdir(parents=True)
    home.mkdir()
    if project_skill:
        _skill(project)
    if home_skill:
        _skill(home)
    content: list[dict[str, object]] = []
    if aar:
        content.append({"type": "tool_use", "name": "Skill", "input": {"skill": "aar"}})
    content.append({"type": "text", "text": answer})
    rows = [
        {"type": "user", "message": {"role": "user", "content": "Какая цель кампании?"}},
        {"type": "assistant", "message": {"role": "assistant", "content": content}},
    ]
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    event = {"transcript_path": str(transcript), "stop_hook_active": active, "cwd": str(project / "src")}
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
    env.update(HOME=str(home), USERPROFILE=str(home))
    if config_skill:
        config = tmp_path / "config"
        _skill(config)
        # В CLAUDE_CONFIG_DIR скиллы лежат прямо в skills/, без .claude
        (config / ".claude" / "skills").rename(config / "skills")
        env["CLAUDE_CONFIG_DIR"] = str(config)
    done = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(event, ensure_ascii=False).encode("utf-8"),
        capture_output=True, check=False, env=env,
    )
    return done.returncode


def test_returns_turn_without_aar(tmp_path: Path) -> None:
    assert _run(tmp_path, MISSED[0]) == 2


def test_passes_with_aar_call(tmp_path: Path) -> None:
    assert _run(tmp_path, MISSED[0], aar=True) == 0


def test_passes_second_stop(tmp_path: Path) -> None:
    assert _run(tmp_path, MISSED[0], active=True) == 0


def test_silent_without_aar_skill(tmp_path: Path) -> None:
    assert _run(tmp_path, MISSED[0], project_skill=False) == 0


def test_skill_in_home_counts(tmp_path: Path) -> None:
    assert _run(tmp_path, MISSED[4], project_skill=False, home_skill=True) == 2


def test_skill_in_claude_config_dir_counts(tmp_path: Path) -> None:
    assert _run(tmp_path, MISSED[2], project_skill=False, config_skill=True) == 2


def test_clean_answer_passes(tmp_path: Path) -> None:
    assert _run(tmp_path, CLEAN[0]) == 0
