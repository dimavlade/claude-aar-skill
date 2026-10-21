# aar - разбор ошибок для Claude Code

Скилл для [Claude Code](https://docs.claude.com/en/docs/claude-code), который превращает каждую
ошибку в уже сданной работе в исправление процесса, а не только этого случая. Название - от
after-action review, разбора после действия.

Обычно, когда вы находите ошибку Claude, он извиняется и чинит конкретное место. Через неделю
та же ошибка приходит из другого файла. Скилл `aar` заставляет ответить на три разных вопроса:

| Уровень | Вопрос | Чем чинится |
|---|---|---|
| Случай | Что сломалось? | Правкой |
| Проверка | Почему ни одна проверка проекта этого не поймала? | Тестом, хуком, новым видом проверки |
| Способ работы | Какое рабочее допущение Claude произвело ошибку? | Переводом допущения в машинную проверку |

И выбрать исправление по лестнице: сначала новый вид проверки или автоматика (тест, хук, отказ
CI), и только если они невозможны - шаг в инструкции, правило в `CLAUDE.md` или строка в памяти.
Правила вида «быть внимательнее» скилл запрещает: они висят в каждом запросе и не срабатывают.

## Что в пакете

```
skills/aar/SKILL.md                 сам скилл: восемь шагов разбора, два режима, лестница исправлений
skills/aar/templates/aar-log.md     шаблон журнала разборов (один на все проекты)
skills/aar/templates/checks-map.md  шаблон карты проверок проекта
skills/aar/templates/run-ledger.md  шаблон ведомости одного разбора
hooks/aar_trigger_gate.py           хук Stop: не даёт Claude поправить себя без разбора
install.py                          установка и удаление
tests/                              тесты хука и установщика
```

## Установка

Нужны Claude Code и Python 3.9 или новее.

```bash
git clone <адрес этого репозитория>
cd claude-aar-skill
python install.py
```

Это установит скилл для всех ваших проектов (в `~/.claude/skills/aar`), хук в
`~/.claude/hooks/` и `~/.claude/settings.json`, и создаст журнал `~/.claude/aar-log.md`. Если
папка настроек Claude Code перенесена переменной `CLAUDE_CONFIG_DIR`, всё ставится туда.
Перезапустите Claude Code.

Другие варианты:

```bash
python install.py --project /путь/к/проекту   # только в один проект, в его .claude/
python install.py --no-hook                    # только скилл, без хука
python install.py --uninstall                  # удалить (журнал остаётся)
```

Прежний `settings.json` сохраняется рядом как `settings.json.bak-aar`, прежняя версия скилла - как
`aar.bak-<время>`. Если `settings.json` повреждён, установщик его не трогает и останавливается.

Без установщика: скопируйте папку `skills/aar` в `~/.claude/skills/` или в `.claude/skills/`
проекта. Хук тогда подключается вручную:

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [ { "type": "command", "command": "python ~/.claude/hooks/aar_trigger_gate.py" } ] }
    ]
  }
}
```

## Как это работает

**Запуск.** Скилл вызывается сам, когда выясняется, что сданное неверно: вы поправили Claude,
спросили «с чего ты взял?», или он сам написал «я ошибся», «поправка». Можно вызвать и вручную:
`/aar`.

**Хук.** Описание скилла Claude читает не всегда. Хук `aar_trigger_gate.py` смотрит на ответ
Claude в конце хода: если там есть собственное исправление («я ошибся», «снимаю рекомендацию»,
"I was wrong", "correction:") и разбор не запущен, хук один раз возвращает ход с просьбой
запустить `aar`. Хук ничего не пишет на диск и не ходит в сеть.

**Два режима.** Ошибку нашёл сам Claude - обычный разбор. Ошибку нашли вы - мета-разбор: кроме
случая разбирается, почему ошибка дошла до человека, не встретив ни одной проверки, и какое
рабочее допущение Claude её произвело.

**Журнал** `~/.claude/aar-log.md` - одна строка на разбор, все проекты. В контекст не грузится;
Claude грепает его, чтобы увидеть повтор («это уже разбиралось - значит, прошлое исправление не
сработало») и доказать, что ошибка - привычка, а не совпадение.

**Карта проверок** `.claude/aar/checks-map.md` в каждом проекте - какие виды проверок у проекта
есть, что каждый ловит, чего не ловит и когда обязателен. Claude создаёт её при первом
мета-разборе по шаблону, из того, что действительно есть в проекте (тесты, CI, хуки). Чем
честнее заполнена колонка «чего не ловит», тем точнее разбор находит белые пятна.

## Чтобы работало лучше

- **Ставьте хук.** Без него скилл запускается, только когда Claude сам вспомнит о нём.
- **Добавьте в `CLAUDE.md` проекта** две строки:

  ```markdown
  Ошибку в сданной работе разбирай скиллом aar. Журнал разборов - ~/.claude/aar-log.md,
  карта проверок проекта - .claude/aar/checks-map.md.
  ```

- **Говорите прямо, когда нашли ошибку.** Достаточно «ты ошибся» или «с чего ты взял?» - это
  включает мета-разбор.
- **Смотрите на исправление, а не на извинение.** Хороший разбор кончается тестом, хуком или
  строкой карты, которые доказанно ловят ошибку. Если в отчёте только «впредь буду внимательнее»,
  попросите довести до ступени 0 или 1.

## Язык

Текст скилла на русском. Claude отвечает на языке пользователя, хук ловит фразы на русском и
английском.

## English

`aar` (after-action review) is a Claude Code skill for mistakes found in work Claude already
reported as done. Instead of "sorry, fixed", Claude answers three separate questions - what broke,
why no check in the project caught it, and which of its working assumptions produced it - and picks
a fix from a ladder that prefers a new kind of check or automation (test, hook, CI gate) over rules
and memory notes. A shared journal (`~/.claude/aar-log.md`) lets it detect repeats across projects,
and a per-project checks map (`.claude/aar/checks-map.md`) shows which kinds of checks exist and
what each one misses.

Install: `python install.py` (all projects) or `python install.py --project <dir>`, then restart
Claude Code. The optional Stop hook returns the turn once if Claude corrects its own earlier answer
("I was wrong", "correction:") without running the review. The skill text is in Russian; Claude
replies in the user's language.

## Лицензия

MIT, см. `LICENSE`.
