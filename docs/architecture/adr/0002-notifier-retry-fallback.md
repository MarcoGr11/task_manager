---
title: "ADR-0002: Retry + Fallback нотифікатора"
owner: MarcoGr11
status: published
adr_status: Superseded by ADR-0005
review_date: 2027-05-26
tags:
  - architecture
  - adr
---

# ADR-0002: Retry + Fallback нотифікатора

- **Номер:** 0002
- **Статус:** Superseded by ADR-0005 (2026-11-27) у частині «нотифікацію, що не дійшла, втрачено». Retry, backoff і fallback із 201 лишаються чинними. Рішення діяло з `6fd3115` (2026-09-27); ADR записано ретроспективно 2026-11-27. Замінює посилання на неіснуючий `README_LAB2.md`.
- **Компонент:** [[architecture/sdd#sdd-notifier|SDD: Клієнт нотифікатора]], [[architecture/isd#isd-env|ISD: змінні оточення]]

## Контекст

`POST /tasks` після збереження задачі сповіщає зовнішній сервіс (`NOTIFIER_URL`). Базовий клієнт `tasks/notifier.py` робив один виклик без retry. Тому збій нотифікатора, який імітується через `mock_notifier` у режимах `error` і `timeout`, ламав створення задачі, хоча задача вже записана.

## Розглянуті альтернативи

| Варіант | За | Проти |
|---|---|---|
| Один виклик без retry (`notifier.py`) | найпростіше | короткочасний збій призводить до помилки клієнта |
| **Обмежений retry + backoff + jitter + fallback (обрано)** | переживає транзієнтні збої, ніколи не кидає виняток назовні | додає затримку до 3.8 с у найгіршому випадку, нотифікацію можна втратити |
| Circuit breaker | швидко відмовляє при тривалому збої | стан між запитами, складніше тестувати |
| Черга або outbox (асинхронно) | доставка гарантована, API не чекає | брокер або фоновий воркер, нова інфраструктура |

## Рішення

`notify_task_created` у `tasks/notifier_resilient.py` працює так:

| Параметр | Значення |
|---|---|
| Максимум спроб `MAX_ATTEMPTS` | 3 |
| Timeout однієї спроби | `NOTIFIER_TIMEOUT_SECONDS`, за замовчуванням 1.0 с (налаштовується з `ae1578c`) |
| Backoff між спробами | `0.2 * 2^(n-1)` с |
| Jitter | до 0.1 с |

Повторюються лише `httpx.TransportError` і HTTP 5xx. Помилки 4xx не повторюються. Після вичерпання спроб функція логує ERROR і повертає `{"delivered": false, "attempts": n}`. API повертає 201 з полями `notification_delivered` і `notification_attempts`.

## Наслідки

- **Плюси:**
    - створення задачі не залежить від доступності нотифікатора;
    - клієнт бачить результат доставки у відповіді.
- **Тести:** 6 тестів у `tests/test_resilience.py`, зокрема `test_fallback_after_persistent_503`, `test_client_error_is_not_retried` і `test_api_degrades_gracefully_when_notifier_down`.
- **Мінуси:**
    - `POST /tasks` синхронно чекає до 3 × 1.0 + 0.6 + 0.2 = 3.8 с;
    - нотифікацію, що не дійшла, не буде доставлено повторно: outbox відсутній;
    - `tasks/notifier.py` залишився як dead code.
- **Коли переглянути:** якщо потрібна гарантована доставка (outbox) або p95 `POST /tasks` має бути меншим за 1 с.
