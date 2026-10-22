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

## Самый простой способ установки

Скажите своему Claude Code:

> Установи скилл из https://github.com/dimavlade/claude-aar-skill

Он прочитает раздел ниже и сделает всё сам.

## Для Claude: как установить этот скилл / For Claude: how to install this skill

If a user asked you to install this skill, follow these steps. Если пользователь попросил вас
установить этот скилл, выполните эти шаги.

1. Clone the repository into a temporary folder:
   `git clone --depth 1 https://github.com/dimavlade/claude-aar-skill <temp>/claude-aar-skill`.
2. Read `install.py` before running it and tell the user in one or two sentences what it will
   change: it copies the skill to `skills/aar` and the hook to `hooks/` of the Claude Code config
   folder (`~/.claude` or `$CLAUDE_CONFIG_DIR`), adds the hook to the `Stop` section of
   `settings.json`, creates the journal `aar-log.md` if it is missing, and adds an auto-trigger
   rule to `CLAUDE.md` between `<!-- aar:start -->` and `<!-- aar:end -->`. Previous versions of
   changed files are kept as `*.bak-aar`.
3. Choose the language: the user writes in Russian - no flag; otherwise add `--lang en`.
4. Choose the scope: all projects - no flag (default); only the current project, if the user
   asked for that - `--project <path to the project>`.
5. Run `python install.py [flags]` from the cloned folder (`python3` where `python` is missing;
   Python 3.9+). Do not edit `settings.json` or `CLAUDE.md` by hand: the installer does it,
   keeps backups and does not duplicate entries on reinstall.
6. Show the user the installer output and tell them to restart Claude Code so it loads the skill
   and the hook. To remove: `python install.py --uninstall` (with the same `--project`, if used).

## Что в пакете

```
skills/aar/SKILL.md                 сам скилл: восемь шагов разбора, два режима, лестница исправлений
skills/aar/templates/aar-log.md     шаблон журнала разборов (один на все проекты)
skills/aar/templates/checks-map.md  шаблон карты проверок проекта
skills/aar/templates/run-ledger.md  шаблон ведомости одного разбора
skills-en/aar/                      то же на английском (python install.py --lang en)
hooks/aar_trigger_gate.py           хук Stop: не даёт Claude поправить себя без разбора
install.py                          установка и удаление
tests/                              тесты хука и установщика
```

## Установка

Нужны Claude Code и Python 3.9 или новее.

```bash
git clone https://github.com/dimavlade/claude-aar-skill
cd claude-aar-skill
python install.py
```

Установщик делает четыре вещи для всех ваших проектов:
- копирует скилл в `~/.claude/skills/aar`;
- ставит хук в `~/.claude/hooks/` и подключает его в `~/.claude/settings.json`;
- создаёт журнал `~/.claude/aar-log.md`, если его нет;
- вписывает правило автозапуска в `~/.claude/CLAUDE.md`.

Если папка настроек Claude Code перенесена переменной `CLAUDE_CONFIG_DIR`, всё ставится туда.
После установки перезапустите Claude Code.

Другие варианты:

```bash
python install.py --project /путь/к/проекту   # только в один проект: его .claude/ и CLAUDE.md
python install.py --no-hook                    # без хука
python install.py --no-claude-md               # без правила в CLAUDE.md
python install.py --lang en                    # английский текст скилла и правила
python install.py --uninstall                  # удалить скилл, хук и правило (журнал остаётся)
```

Прежние версии изменённых файлов сохраняются рядом: `settings.json.bak-aar`, `CLAUDE.md.bak-aar`,
`aar.bak-<время>`. Правило в `CLAUDE.md` стоит между строками `<!-- aar:start -->` и
`<!-- aar:end -->`. Повторная установка заменяет его, а не дописывает второе, удаление вырезает
его, остальной текст файла не трогается. Если `settings.json` повреждён, установщик его не
трогает и останавливается.

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

- **Не отключайте хук и правило в `CLAUDE.md`.** Описание скилла Claude читает не всегда.
  Правило напоминает о разборе в каждом запросе, а хук ловит случаи, когда Claude поправил себя
  и забыл о разборе.

- **Говорите прямо, когда нашли ошибку.** Достаточно «ты ошибся» или «с чего ты взял?» - это
  включает мета-разбор.
- **Смотрите на исправление, а не на извинение.** Хороший разбор кончается тестом, хуком или
  строкой карты, которые доказанно ловят ошибку. Если в отчёте только «впредь буду внимательнее»,
  попросите довести до ступени 0 или 1.

## Язык

Скилл есть на русском (`skills/aar`, ставится по умолчанию) и на английском (`skills-en/aar`,
ключ `--lang en`). Содержание одинаковое. На каком бы языке ни был текст скилла, Claude отвечает
на языке пользователя. Хук ловит фразы на обоих языках.

## English

`aar` (after-action review) is a Claude Code skill for mistakes found in work Claude already
reported as done. Instead of "sorry, fixed", Claude answers three separate questions - what broke,
why no check in the project caught it, and which of its working assumptions produced it - and picks
a fix from a ladder that prefers a new kind of check or automation (test, hook, CI gate) over rules
and memory notes. A shared journal (`~/.claude/aar-log.md`) lets it detect repeats across projects,
and a per-project checks map (`.claude/aar/checks-map.md`) shows which kinds of checks exist and
what each one misses.

Easiest install: tell your Claude Code "Install the skill from
https://github.com/dimavlade/claude-aar-skill" - it follows the "For Claude" section above.
Manual install of the English version: `python install.py --lang en` (all projects) or
`python install.py --lang en --project <dir>`, then restart Claude Code. The installer also adds a
short auto-trigger rule to `CLAUDE.md` (between `<!-- aar:start -->` and `<!-- aar:end -->`).
`--no-hook` and `--no-claude-md` skip the hook and the rule, `--uninstall` removes everything except
the journal. If `CLAUDE_CONFIG_DIR` is set, the global
install goes there. The Stop hook returns the turn once if Claude corrects its own earlier answer
("I was wrong", "correction:") without running the review. Claude replies in the user's language.

## Лицензия

MIT, см. `LICENSE`.
