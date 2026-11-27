# Changelog документації

Формат: [Keep a Changelog](https://keepachangelog.com/uk/1.1.0/). Версії документації позначаються тегами `docs-vMAJOR.MINOR`:

- MAJOR змінюється, коли змінюються шляхи або структура, тобто ламаються старі посилання;
- MINOR змінюється при новому вмісті.

Версія API живе окремо, в `info.version` файлу `docs/api/openapi.yaml` (SemVer).

## [Unreleased]

### Виправлено

- CI: крок markdownlint перевіряє лише `docs/**/*.md`, `README.md`, `CHANGELOG.md` (типовий glob action-у чіпляв `FINANCIAL_LEDGER.md`).
- Мертве посилання `../architecture/deployment.md` у `local-setup.md` (навмисний FAIL-дефект ЛР11) прибрано.

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

## [docs-v1.0] - 2026-11-27

### Додано

- ЛР10: README, SDD, ISD, ADR-0001, ADR-0002, maintenance, handover, аудит документації (`docs/audit/`), `scripts/doc_audit.py`. Коміти `0b6072c`..`dc56848`.
