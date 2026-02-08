# Ulauncher GPT (Responses API)

[![CI](https://github.com/novakovichid/ulauncher-gpt/actions/workflows/ci.yml/badge.svg)](https://github.com/novakovichid/ulauncher-gpt/actions/workflows/ci.yml)
[![Security](https://github.com/novakovichid/ulauncher-gpt/actions/workflows/security.yml/badge.svg)](https://github.com/novakovichid/ulauncher-gpt/actions/workflows/security.yml)
[![Docs](https://github.com/novakovichid/ulauncher-gpt/actions/workflows/docs.yml/badge.svg)](https://github.com/novakovichid/ulauncher-gpt/actions/workflows/docs.yml)
[![Coverage](https://img.shields.io/badge/coverage-85%25%2B-brightgreen)](https://github.com/novakovichid/ulauncher-gpt/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/novakovichid/ulauncher-gpt?sort=semver)](https://github.com/novakovichid/ulauncher-gpt/releases)

Плагин для [Ulauncher](https://ulauncher.io/), который отправляет запрос в OpenAI через **Responses API** и возвращает ответ прямо в лаунчер.

![Скриншот](images/screenshot.png)

## Что сделано

- Миграция на `https://api.openai.com/v1/responses`.
- Ручной запуск запросов по настраиваемому суффиксу (без автосрабатывания по debounce-таймауту).
- Явные действия после генерации: `Предпросмотр ответа` и `Скопировать полный ответ`.
- Безопасная обработка ошибок API (HTTP/network/JSON).
- Ретраи для временных сбоев сети.
- Валидация настроек пользователя.
- Unit/integration тесты с покрытием (порог `85%`).
- CI quality gates: lint, type-check, tests, security.
- Автодоки ключевых модулей через `pdoc`.

## Установка

1. Откройте Ulauncher.
2. Перейдите в `Preferences -> Extensions`.
3. Нажмите `Add extension`.
4. Вставьте URL репозитория: `https://github.com/novakovichid/ulauncher-gpt`.

## Настройки

- `api_key`: ключ OpenAI.
- `gpt_kw`, `gpt_kw_alt_1`, `gpt_kw_alt_2`: несколько keyword-алиасов для запуска плагина.
- `model`: `gpt-4.1-mini`, `gpt-4.1`, `gpt-4o-mini` или `custom` (в UI подписаны Tier мощности и ориентиры цены за 1M токенов input/output).
- `endpoint_url`: по умолчанию `https://api.openai.com/v1/responses`.
- `reasoning_effort`, `verbosity`, `temperature`, `top_p`, penalties.
- `submit_suffix`: строка-триггер отправки (например `;;`).
- `debug_mode`: безопасная диагностика (секреты маскируются).
- `locale`: `ru` / `en`.

## Просмотр доступных моделей по API-ключу

- Базовый запуск запроса: `gpt <ваш запрос><submit_suffix>` (например `gpt как дела;;`)
- Введите в Ulauncher: `gpt /models`
- Плагин вызовет `GET /v1/models` с вашим ключом и покажет список доступных моделей.
- Enter на первой строке копирует полный список, Enter на модели копирует команду выбора.
- В списке есть ранжирование мощности: `Tier 1` (мощнее) -> `Tier 2` -> `Tier 3`.

## Выбор модели из доступных

- Выбрать модель из разрешенных ключом: `gpt /use-model <model_id>`
- Сбросить runtime-выбор и вернуться к модели из настроек: `gpt /clear-model`
- В списке `gpt /models` активная модель помечается `[active]`.

## Локальная разработка

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
pytest
ruff check .
black --check .
mypy ulauncher_gpt
```

## Автодоки

```bash
pdoc ulauncher_gpt -o docs/api
```

## Проверка актуальности API/моделей

Проверено на дату **2026-02-07** по официальным источникам OpenAI:

- https://platform.openai.com/docs/api-reference/responses/object
- https://platform.openai.com/docs/api-reference/chat
- https://developers.openai.com/blog/responses-api
- https://platform.openai.com/docs/models/gpt-5-mini/

Примечание: в плагине по умолчанию используется whitelist для аккаунтов без верификации (`gpt-4.1-mini`, `gpt-4.1`, `gpt-4o-mini`).
Цены в подписи моделей основаны на OpenAI pricing snapshot от 2026-02-07 и могут меняться.

## Ограничения

- В CI нет e2e с реальным API-ключом (только mock HTTP).
- Плагин синхронный (`requests`), без async.
