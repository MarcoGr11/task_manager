# Changelog документації

Формат: [Keep a Changelog](https://keepachangelog.com/uk/1.1.0/). Версії документації позначаються тегами `docs-vMAJOR.MINOR`:

- MAJOR змінюється, коли змінюються шляхи або структура, тобто ламаються старі посилання;
- MINOR змінюється при новому вмісті.

Версія API живе окремо, в `info.version` файлу `docs/api/openapi.yaml` (SemVer).

З ЛР12 тут також фіксуються релізи застосунку (теги `vMAJOR.MINOR.PATCH`), бо зміни коду і документації йдуть одним RFC.

## [Unreleased]

## [1.1.0] - 2026-11-27

Реліз застосунку за [RFC-001](docs/change/rfc-001.md) і ECAB-2026-11-27, наслідок [INC-001](docs/incidents/inc-001.md).

**Міграції: немає.** `tasks.json`, `users.json`, `consents.json` не змінюють формат. Новий файл `NOTIFIER_OUTBOX` створюється лише під час першого збою доставки. API змінено лише additive, тож `info.version` OpenAPI лишається 1.0.1.

### Додано

- Outbox недоставлених нотифікацій `tasks/notifier_outbox.py` і ручна команда `python -m tasks.notifier_outbox replay` (CA-2, ADR-0005).
- Метрики `notifier_delivery_total{result}` і `notifier_outbox_pending`; алерт `NotifierFallbackRatio` (CA-1).
- Змінна оточення `NOTIFIER_OUTBOX`; outbox входить у `scripts/backup.py`.
- `scripts/ops_audit.py`, перевірка операційної готовності в CI (PA-1).

### Виправлено

- Втрата підтверджених задач під конкурентним `POST /tasks`: атомарний `TaskStorage.save` і блокування load-modify-save (CA-3).

### Змінено

- ADR-0002 переведено в `Superseded by ADR-0005` у частині втрати нотифікацій.

## [docs-v2.1] - 2026-11-27

### Додано

- Рівень 5 «Експлуатація»: [план супроводу](docs/maintenance-plan.md), [SLO](docs/slo.md) і `docs/slo.yaml`, runbook RB-001 і каталог алертів, RFC-001, IA-001, протокол CCB, release checklist, INC-001, PM-001, реконструкція legacy-підсистеми нотифікацій.
- ISD §4: розгортання з health-перевіркою, міграції, порядок відновлення, RTO/RPO, backup policy, restore drill.
- Пункт ORR у чек-листі CONTRIBUTING.

## [docs-v2.0] - 2026-11-27

### Змінено (breaking)

- Піраміда DaC. Сторінки перенесено:
    - `docs/sdd.md` → `docs/architecture/sdd.md`;
    - `docs/isd.md` → `docs/architecture/isd.md`;
    - `docs/maintenance.md` → `docs/developer/maintenance.md`;
    - `docs/handover.md` → `docs/developer/handover.md`.
- На старих шляхах залишено сторінки зі `status: deprecated` і переспрямуванням.
- Контракти API прибрано з README і SDD §5. Єдине джерело тепер `docs/api/openapi.yaml` (ADR-0003).

### Додано

- MkDocs Material (`mkdocs.yml`) з плагінами:
    - search, tags;
    - ezlinks (wikilinks), mermaid2;
    - git-revision-date-localized, swagger-ui-tag, mkdocstrings.
- `docs/developer/`: CONTRIBUTING з чек-листом docs-or-don't-merge, local-setup, standards.
- `docs/api/openapi.yaml`: OpenAPI 3.0.3, 10 маршрутів і `/metrics`, спільна схема `Error`. `info.version` 1.0.0, потім 1.0.1: задокументовано 400 для тіла, що не є JSON (дефект D-1, [перевірка дрейфу](docs/api/drift.md)).
- Сторінка API рендериться з YAML (Swagger UI). Довідник з docstring генерує mkdocstrings.
- `.spectral.yaml`. Попередження `info-contact` залишено свідомо: контакт власника не публікуємо, власника вказано в CODEOWNERS.
- ADR-0003 (OpenAPI як SSOT) і ADR-0004 (DaC на MkDocs), журнал ADR з правилами нумерації, статусів і незмінності.
- Front matter (`owner`, `status`, `review_date`, `tags`) у кожній сторінці `docs/`. Додано `.github/CODEOWNERS` і `scripts/review_dates.py`.
- `.github/workflows/docs.yml`: markdownlint, Spectral, review_date, `mkdocs build --strict`, GitHub Pages.
- Змінна оточення `CORS_ALLOW_ORIGINS` (ISD §3), щоб Swagger UI на сайті міг звертатися до локального API.

### Виправлено

- CI: крок markdownlint перевіряє лише `docs/**/*.md`, `README.md`, `CHANGELOG.md` (типовий glob action-у чіпляв `FINANCIAL_LEDGER.md`).
- Мертве посилання `../architecture/deployment.md` у `local-setup.md` (навмисний FAIL-дефект ЛР11) прибрано.

## [docs-v1.0] - 2026-11-27

### Додано

- ЛР10: README, SDD, ISD, ADR-0001, ADR-0002, maintenance, handover, аудит документації (`docs/audit/`), `scripts/doc_audit.py`. Коміти `0b6072c`..`dc56848`.
