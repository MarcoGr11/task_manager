---
title: Перевірка дрейфу API
owner: MarcoGr11
status: published
review_date: 2027-02-25
tags:
  - api
  - ops
---

# Перевірка дрейфу: openapi.yaml проти запущеного API

Перевірка 2026-11-27, сервер `uvicorn tasks.api:app --port 8000`, seed `python -m tasks.seed_users`.

| Перевірка | Команда | Результат |
|---|---|---|
| Набір операцій | порівняння `GET /openapi.json` (FastAPI, code-first) з `docs/api/openapi.yaml` | 11 операцій і там, і там, розбіжностей у маршрутах немає |
| Контрактні тести, прогін 1 | `schemathesis run docs/api/openapi.yaml --url http://localhost:8000 --checks all --max-examples 30 -H "X-User-Id: 1"` (без `anonymize`, бо він незворотно змінює дані) | 644 тест-кейси, 7 унікальних збоїв |
| Контрактні тести, прогін 2 (той самий seed, після виправлення специфікації) | те саме з `--seed 287805701175605226833628122546386525190` | 527 тест-кейсів, 4 унікальні збої |
| Згенерований SDK | `openapi-generator-cli generate -g python`, виклики `list_tasks`, `create_task`, `get_task`, `health` | усі пройшли; `get_task(999)` повернув 404 `Task not found` |

## Дефекти

| ID | Що знайдено | Тип | Статус |
|---|---|---|---|
| D-1 | `POST /tasks` і `POST /api/users` на тіло, що не є JSON, повертають 400 `There was an error parsing the body`, а специфікація знала тільки 201/422 (Schemathesis ST103) | дрейф документації | **виправлено**: відповідь `400` додано в `openapi.yaml`, `info.version` 1.0.0 → 1.0.1 |
| D-2 | `OPTIONS /tasks` повертає 405 з `Allow: GET`, хоча маршрут підтримує і `POST` (ST205). Starlette формує `Allow` лише з першого зареєстрованого маршруту шляху | дефект коду (фреймворк) | відкрито |
| D-3 | `POST /api/users` з валідним за схемою тілом відповідає 422 `Invalid registration data`, якщо email уже зареєстрований (ST202). Для конфлікту доречніший код 409 | дефект семантики API; поведінку задокументовано як 422 | відкрито, рішення за власником |
| D-4 | Запит з невідомим заголовком `x-schemathesis-unknown-property` приймається (ST201, `personal-data`, `grant`, у прогоні 1 також `revoke`) | хибнопозитивний результат: HTTP дозволяє додаткові заголовки | прийнято, не виправляється |
| D-5 | OpenAPI 3.1: згенерований Python SDK падав на `create_task` (`due_date`, `owner_id`: «Input should be a valid date/integer» для `null`). openapi-generator 7.14.0 підтримує 3.1 як beta | несумісність інструменту | **виправлено**: специфікацію переведено на 3.0.3 з `nullable: true` ([[architecture/adr/0003-openapi-as-source-of-truth]]) |

Попередження Schemathesis: `POST /api/users/{user_id}/send-marketing-email` повертав лише 403. Це очікувано, бо в seed користувач 1 не має згоди `MARKETING_EMAIL`, і Policy Gate каже `DENY`.

Пов'язані: [[api/index|API]], [CONTRIBUTING](../developer/CONTRIBUTING.md).
