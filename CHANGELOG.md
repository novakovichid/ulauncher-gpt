# Changelog

## Unreleased

- Полный рефакторинг в модульную архитектуру (`config`, `openai_client`, `presenters`, `extension`, `utils`).
- Миграция на OpenAI Responses API (`/v1/responses`).
- Валидация preferences и безопасная обработка ошибок.
- Добавлены retry/backoff для временных сетевых сбоев.
- Добавлены unit/integration тесты с coverage gate 85%.
- Добавлены CI workflow: lint/test/security/docs.
- Обновлен README и добавлен ADR по API-стратегии.
