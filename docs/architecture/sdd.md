---
title: "SDD: Software Design Description"
owner: MarcoGr11
status: published
review_date: 2027-05-26
tags:
  - architecture
---

# SDD: Software Design Description, Task Manager

| Поле | Значення |
|---|---|
| Версія коду | Python 3.13, FastAPI; дата останньої зміни сторінки внизу (git-revision-date) |
| Власник документа | MarcoGr11 (єдиний автор комітів); формальна роль потребує підтвердження студента |
| Цикл перегляду | 180 днів (архітектурний), див. [[developer/maintenance]] |
| Інфраструктура | [[architecture/isd]] |
| Рішення | [[architecture/adr/0001-json-file-storage]], [[architecture/adr/0002-notifier-retry-fallback]] |

## 1. Призначення

Навчальний сервіс керування задачами з:

- HTTP API: задачі, користувачі, експорт персональних даних, анонімізація, згоди;
- CLI для локальної роботи;
- сповіщенням зовнішнього сервісу про нову задачу з Retry + Fallback;
- метриками Prometheus.

Дані зберігаються у JSON-файлах.

## 2. C4: Container diagram

```mermaid
C4Container
title Task Manager: контейнери
Person(user, "Користувач / клієнт API", "HTTP-запити з X-User-Id")
Person(dev, "Розробник", "CLI, seed-скрипти")
System_Boundary(tm, "Task Manager") {
  Container(api, "Task Manager API", "Python 3.13, FastAPI, uvicorn :8000", "REST API: задачі (список, одна за id), користувачі, згоди; /metrics")
  Container(cli, "CLI", "Python argparse", "add, list, stats, done")
  ContainerDb(files, "JSON-сховище", "tasks.json, users.json, consents.json", "TASKS_DB, USERS_DB, CONSENTS_DB")
}
System_Ext(notifier, "Notification service", "POST /notify; локально mock_notifier :9100")
System_Ext(prom, "Prometheus + Grafana", "scrape /metrics кожні 5 с")
Rel(user, api, "HTTP JSON")
Rel(dev, cli, "командний рядок")
Rel(api, files, "load/save, os.replace")
Rel(cli, files, "load/save")
Rel(api, notifier, "POST /notify, retry 3x, timeout NOTIFIER_TIMEOUT_SECONDS (1 с)", "httpx")
Rel(prom, api, "GET /metrics", "HTTP")
```

## 3. Компоненти

Кожен компонент має посилання на сусідів і на свій опис в ISD.

<a id="sdd-api"></a>

### 3.1 Task Manager API (`tasks/api.py`)

- **Відповідальність:**
    - HTTP-маршрути (розділ 5) і валідація вхідних даних через Pydantic (`TaskIn`, `UserIn`);
    - auth-заглушка `X-User-Id`, перевірка доступу `authorize_subject`;
    - аудит-події, кореляція `X-Correlation-Id`, `/metrics`.
- **Залежності:**
    - [Сховище](#sdd-storage) і [Нотифікатор](#sdd-notifier);
    - [Доменна логіка](#sdd-domain): `consent_policy`, `privacy`, `models`;
    - `logging_utils`; зовнішні бібліотеки `prometheus-fastapi-instrumentator` і `psutil`.
- **Інфраструктура:** [[architecture/isd#isd-api|ISD: API-процес]].

<a id="sdd-cli"></a>

### 3.2 CLI (`tasks/cli.py`)

- **Відповідальність:** команди `add`, `list`, `stats`, `done` над `tasks.json` у поточному каталозі (`DEFAULT_DB`).
- **Залежності:** [Сховище](#sdd-storage), [Доменна логіка](#sdd-domain) (`reports`).
- **Інфраструктура:** [[architecture/isd#isd-envs|ISD: середовище dev]].

<a id="sdd-domain"></a>

### 3.3 Доменна логіка

- **Модулі:** `models.py`, `reports.py`, `consent_policy.py`, `privacy.py`, `logging_utils.py`, `task_services.py`, `task_ports.py`, `notification_services.py`.
- **Відповідальність:**
    - модель задачі та звіти (статуси, прострочені задачі, urgency, CSV);
    - політика згод: перевірка версії політики та історія;
    - експорт і анонімізація персональних даних;
    - фільтр PII у логах.
- **Сервісні класи Лаби 8** (`TaskService`, `ConsentService`, `NotificationDispatcher`, `ReportExporter` через Protocol-порти) покриті тестами, але API їх ще не використовує: API працює зі сховищем напряму.
- **Залежності:** [Сховище](#sdd-storage) (лише через типи `Task` і `Consent`).
- **Інфраструктура:** не має окремого розгортання, працює в процесі [[architecture/isd#isd-api|API]].

<a id="sdd-storage"></a>

### 3.4 Сховище (`tasks/storage.py`, `tasks/user_storage.py`, `tasks/consent.py`)

- **Відповідальність:**
    - `TaskStorage` читає і пише список `Task` у JSON;
    - `JsonStorage`, `UserStorage` і `ConsentStorage` працюють з dataclass-записами;
    - `save_all` спершу серіалізує всі файли в `*.tmp`, потім виконує `os.replace` для кожного файлу. Атомарність гарантована на рівні файлу, а не між файлами.
- **Залежності:** лише stdlib. Рішення описано в [[architecture/adr/0001-json-file-storage|ADR-0001]].
- **Інфраструктура:** [[architecture/isd#isd-storage|ISD: сховище і бекап]].

<a id="sdd-notifier"></a>

### 3.5 Клієнт нотифікатора (`tasks/notifier_resilient.py`)

- **Відповідальність:** `notify_task_created` надсилає `POST NOTIFIER_URL` з такими параметрами:

  | Параметр | Значення |
  |---|---|
  | Максимум спроб | 3 |
  | Timeout спроби | `NOTIFIER_TIMEOUT_SECONDS`, за замовчуванням 1.0 с |
  | Backoff | 0.2 с, потім 0.4 с, плюс jitter до 0.1 с |
  | Що повторюється | помилки транспорту і HTTP 5xx |

  Якщо доставка не вдалася, функція повертає `delivered: false` без винятку. Задачу при цьому вже збережено.
- **Outbox (з 1.1.0, RFC-001).** Після fallback задача дописується JSON-рядком у `NOTIFIER_OUTBOX` (`tasks/notifier_outbox.py`). Повторна доставка лише вручну: `python -m tasks.notifier_outbox replay`. Рішення: [[architecture/adr/0005-notification-outbox|ADR-0005]].
- **Метрики.** `notifier_delivery_total{result="delivered|fallback|lost"}` і `notifier_outbox_pending`. Вони живлять SLI `background_notifications` ([[slo]]) і алерт `NotifierFallbackRatio`.
- `tasks/notifier.py` – базовий клієнт без retry. Ні код, ні тести його не імпортують (dead code).
- **Залежності:** `httpx`, зовнішній [Notification service](#sdd-mock). Рішення описано в [[architecture/adr/0002-notifier-retry-fallback|ADR-0002]].
- **Інфраструктура:** [[architecture/isd#isd-env|ISD: змінні оточення]].

<a id="sdd-mock"></a>

### 3.6 Mock Notifier (`mock_notifier/server.py`)

- **Відповідальність:** заглушка зовнішнього сервісу для fault injection.
    - `POST /_control?mode=ok|timeout|error` перемикає режим;
    - `POST /notify` відповідає `{"status":"sent"}`, 503 у режимі `error` і затримкою 10 с у режимі `timeout`.
- **Залежності:** FastAPI. Використовується [клієнтом нотифікатора](#sdd-notifier).
- **Інфраструктура:** [[architecture/isd#isd-topology|ISD: топологія]].

<a id="sdd-seed"></a>

### 3.7 Seed та імпорт (`tasks/seed.py`, `tasks/seed_users.py`, `tasks/legacy_import.py`)

- **Відповідальність:**
    - `seed` генерує N задач (5000 за замовчуванням) для навантажувальних тестів;
    - `seed_users` створює 3 користувачі та 5 задач;
    - `legacy_import` імпортує CSV-подібний формат.
- **Залежності:** [Сховище](#sdd-storage).
- **Інфраструктура:** [[architecture/isd#isd-envs|ISD: середовища]].

## 4. Модель даних

| Сутність | Поля | Файл |
|---|---|---|
| `Task` | `id:int`, `title:str`, `priority: Priority(LOW=1, MEDIUM=2, HIGH=3)`, `status: Status(todo, in_progress, done)`, `due_date: date or null`, `tags: list[str]`, `owner_id: int or null` (→ `User.id`) | `TASKS_DB` |
| `User` | `id`, `name`, `email`, `phone`, `password_hash` (pbkdf2_sha256, 600 000 ітерацій), `reset_token`, `marketing_opt_in_source`, `is_admin`, `anonymized_at` | `USERS_DB` |
| `Consent` | `user_id` (→ `User.id`), `purpose` (`MARKETING_EMAIL`, `OPTIONAL_ANALYTICS`), `is_granted`, `policy_version` (поточна `2026-09`), `granted_at`, `withdrawn_at`, `source`, `updated_at`, `history: list[dict]` | `CONSENTS_DB` |

Правила:

- `password_hash`, `reset_token` і `is_admin` ніколи не повертаються назовні.
- Згода, видана для старішої версії політики, недійсна.

## 5. API-контракти

Єдине джерело правди для контрактів – `docs/api/openapi.yaml`, рішення зафіксовано в [[architecture/adr/0003-openapi-as-source-of-truth|ADR-0003]]. Інтерактивна сторінка: [[api/index|API]]. SDD не повторює маршрути, коди відповідей і схеми.
