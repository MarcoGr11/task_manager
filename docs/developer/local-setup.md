---
title: Локальне середовище
owner: MarcoGr11
status: published
review_date: 2027-02-25
tags:
  - developer
  - ops
---

# Локальне середовище

Потрібно: Python 3.13; для хуків gitleaks і radon; для перевірок документації Node.js (Spectral, markdownlint). Змінні оточення та порти описано в [[architecture/isd]].

## Запуск сервісу

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
git config core.hooksPath .githooks          # gitleaks + MAX_CC=10 на кожен коміт
python -m tasks.seed_users                   # 3 користувачі, 5 задач у ./*.json
uvicorn mock_notifier.server:app --port 9100 &
uvicorn tasks.api:app --port 8000
curl localhost:8000/health                   # {"status":"ok"}
```

Контракти маршрутів: [[api/index|API]]. Розгортання в prod: [deployment](../architecture/deployment.md).

## CLI без сервера

```bash
python -m tasks.cli add "Написати звіт" --priority HIGH
python -m tasks.cli list
python -m tasks.cli stats
```

## Тести

```bash
python -m pytest
```

## Документація локально

```bash
pip install -r requirements-docs.txt
mkdocs serve                                  # http://127.0.0.1:8000, або --dev-addr 127.0.0.1:8001 поруч з API
mkdocs build --strict                         # те саме, що в CI
python scripts/review_dates.py                # прострочені review_date
python scripts/doc_audit.py                   # маршрути і змінні описані в документації
npx @stoplight/spectral-cli lint docs/api/openapi.yaml --ruleset .spectral.yaml
npx markdownlint-cli2 "docs/**/*.md" README.md CHANGELOG.md
```

Щоб «Try it out» у Swagger UI звертався до локального API з іншого порту, запустіть API з `CORS_ALLOW_ORIGINS=http://127.0.0.1:8001`.

Правила внеску: [CONTRIBUTING](CONTRIBUTING.md). Стандарти: [[developer/standards]].
