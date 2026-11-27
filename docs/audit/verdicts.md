---
title: "Матриця рішень по носіях (ЛР10)"
owner: MarcoGr11
status: published
review_date: 2027-02-25
tags:
  - audit
---

# Матриця рішень по носіях знань

Дата: 2026-11-27. Підстава: `docs/audit/inventory.md`, `docs/audit/decay_metrics.txt`.

| Носій | Діагноз | Рішення | Дія |
|---|---|---|---|
| `README.md` | Dead: немає | **оновити (створити)** | Призначення, швидкий старт, онбординг, перелік API, посилання на `docs/`. |
| `docs/sdd.md`, `docs/isd.md`, ADR | Відсутні | **оновити (створити)** | Паспорт архітектури та інфраструктури з коду. |
| `README_LAB2..9.md` (локальні) | Dead: втрачено з диска | **deprecated** | Не відновлювати з пам'яті. Чинне знання переноситься в SDD/ISD/ADR. Причина втрати потребує підтвердження студента. |
| Ghost-коміти «docs» (9 шт.) | Dead: опис без вмісту | **deprecated** | Історію не переписувати. Факт задокументовано в аудиті, нові коміти документації змінюють файли в `docs/`. |
| `~/Downloads/task_manager/README_LAB.md` | Dead: поза репозиторієм, стан Лаби 1 | **видалити** (з обігу) | Не посилатися на нього. Видалення з диска вирішує студент. |
| Коментар `tasks/notifier_resilient.py:11` → `README_LAB2.md` | Dead link | **оновити** | Перенаправити на `docs/architecture/adr/0002-notifier-retry-fallback.md`. |
| `.env.example` | Decay: 1 з 4 змінних | **оновити** | Додати `TASKS_DB`, `USERS_DB`, `CONSENTS_DB`, `NOTIFIER_URL`. |
| `.gitleaks.toml` allowlist | Dead path | **deprecated** | Залишити до підтвердження студента: зміна конфігурації безпеки виходить за межі документації. Позначено в ISD. |
| `.github/workflows/complexity.yml` | Актуальний (33 дні), але без опису | **оновити** (описати в ISD) | Стадії, тригери, артефакт. |
| `.githooks/*` | Актуальні | **оновити** (описати в README/ISD) | Крок активації хука в онбордингу. |
| `docker-compose.monitoring.yml`, `monitoring/` | Актуальні, без опису | **оновити** (описати в ISD) | Порти, scrape, retention, бекап. |
| `docker-compose.sonar.yml`, `sonar-project.properties`, `pytest.ini` | Конфіг, 75 днів, 24 коміти коду після | **оновити** (описати в ISD) | Quality Gate як текст. |
| `requirements.txt` | Актуальний | залишити | Без змін. |
| `FINANCIAL_LEDGER.md` | Процесний артефакт Лаби 9, не про систему | **deprecated** (для онбордингу) | Не включати в онбординг. Позначити в handover як артефакт процесу. |
| Docstrings `tasks/*.py` | 19 з 20 модулів | залишити | Правило «зміна коду = зміна документації» в `docs/maintenance.md`. |
| Повідомлення комітів | 19 з 54 у Conventional Commits | **оновити** (надалі) | Нові коміти тільки у форматі `type(scope): ...`. |

Знімок аудиту ЛР10 на 2026-11-27: шляхи `docs/sdd.md`, `docs/isd.md` у тексті відповідають тодішній структурі. Пов'язані: [[audit/inventory]], [[developer/handover]].
