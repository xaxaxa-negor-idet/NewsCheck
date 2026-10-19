# NewsCheck — Проект 1

Мониторинг новостных Telegram-каналов и проверка фактов. Полные требования: `D:\NewsCheck_Проект1_Полная_спецификация.md`.

## Быстрый старт

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m newscheck migrate
venv\Scripts\python -m newscheck check
```

## Команды

- `python -m newscheck migrate` — создать/обновить базу `newscheck.db`;
- `python -m newscheck check` — проверить конфигурацию (dry-run, destination);
- `python -m pytest` — тесты.

## Настройки

Секреты хранятся в `.env` (не в git): `TELEGRAM_BOT_TOKEN`, `LLM_ENDPOINT`, `LLM_API_KEY`.
Поведение (пороги, интервалы, шаблоны) хранится в таблице `config` базы SQLite.

## Dry-run

По умолчанию включён (`dry_run=true`). Публикация идёт в консоль. Боевой режим — только ручным переключением в config.

## Состояние

- Схема БД, миграции, очередь задач, config — реализованы;
- адаптер Telegram (публичные страницы), collector, дедуп, версии сообщений, медиа — реализованы;
- JSON-схемы и валидаторы LLM — реализованы;
- детерминированный расчёт статуса — реализован;
- публикация (formatter, console, Telegram destination) — реализована;
- поиск: GDELT, канонизация URL, снимки страниц — реализовано;
- LLM-интеграция — ожидает ключ владельца.
