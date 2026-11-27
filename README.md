# Task Manager

Навчальний сервіс керування задачами: FastAPI HTTP API і CLI, зберігання в JSON-файлах, сповіщення зовнішнього сервісу з Retry + Fallback, метрики Prometheus. Серед функцій персональних даних є експорт, анонімізація і згоди з версіями політики.

Хто що читає:

| Документ | Для кого | Про що |
|---|---|---|
| [docs/sdd.md](docs/sdd.md) | розробники | компоненти, C4, модель даних, API |
| [docs/isd.md](docs/isd.md) | DevOps, QA | топологія, середовища, змінні, CI, моніторинг, бекап |
| [docs/architecture/adr/](docs/architecture/adr/) | архітектор | чому JSON і чому Retry + Fallback |
| [docs/maintenance.md](docs/maintenance.md), [docs/handover.md](docs/handover.md) | власник | хто відповідає за документацію, передача проєкту |

## Швидкий старт

Потрібно: Python 3.13; для хуків – gitleaks і radon.

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
git config core.hooksPath .githooks          # gitleaks + MAX_CC=10 на кожен коміт
python -m tasks.seed_users                   # 3 користувачі, 5 задач у ./*.json
uvicorn mock_notifier.server:app --port 9100 &
uvicorn tasks.api:app --port 8000
curl localhost:8000/health                   # {"status":"ok"}
```

Перевірка: `python -m pytest`. На 2026-11-27 результат 118 passed, покриття 92%.

CLI без сервера:

```bash
python -m tasks.cli add "Написати звіт" --priority HIGH
python -m tasks.cli list
python -m tasks.cli stats
```

## API

Повний контракт описано в [SDD, розділ 5](docs/sdd.md#5-api-контракти). Маршрути `/api/users/{user_id}/...` вимагають заголовок `X-User-Id`. Це auth-заглушка навчального проєкту, а не продакшн-механізм.

| Маршрут | Що робить |
|---|---|
| `GET /health` | перевірка живості |
| `GET /tasks` | список задач |
| `GET /tasks/{task_id}` | одна задача, 404 якщо немає |
| `POST /tasks` | створити задачу (`priority` числом 1-3) і сповістити нотифікатор |
| `POST /api/users` | реєстрація |
| `GET /api/users/{user_id}/personal-data` | експорт персональних даних |
| `POST /api/users/{user_id}/anonymize` | анонімізація (Right to Erasure) |
| `POST /api/users/{user_id}/consents/{purpose}/grant` | надати згоду |
| `POST /api/users/{user_id}/consents/{purpose}/revoke` | відкликати згоду |
| `POST /api/users/{user_id}/send-marketing-email` | розсилка лише за дійсної згоди |
| `GET /metrics` | метрики Prometheus |

## Онбординг (перший день)

1. Виконати «Швидкий старт» і переконатися, що `pytest` зелений, а `git commit` запускає хук.
2. Прочитати [SDD](docs/sdd.md): C4-діаграму і розділ про свій компонент.
3. Прочитати [ISD](docs/isd.md): змінні оточення і Quality Gates.
4. Прочитати обидва [ADR](docs/architecture/adr/), щоб не повторювати відкинуті альтернативи.
5. Змінюючи код, оновлювати документацію в тому самому коміті ([правило](docs/maintenance.md)) і запускати `python scripts/doc_audit.py`. Exit code 0 означає, що документація не відстала від коду.

## Структура

```
tasks/           код: api.py, cli.py, моделі, сховище, нотифікатор, політики
mock_notifier/   заглушка зовнішнього сервісу сповіщень (fault injection)
tests/           pytest
scripts/         hotspots.py (CI), fin_sim.py (Лаба 9), doc_audit.py (аудит документації)
monitoring/      Prometheus + Grafana (docker-compose.monitoring.yml)
docs/            SDD, ISD, ADR, аудит, супровід, передача
```
