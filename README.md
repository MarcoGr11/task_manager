# Task Manager

Навчальний сервіс керування задачами:

- FastAPI HTTP API і CLI;
- зберігання в JSON-файлах;
- сповіщення зовнішнього сервісу з Retry + Fallback;
- метрики Prometheus;
- експорт і анонімізація персональних даних, згоди з версіями політики.

Документація зібрана як код у `docs/` і публікується на сайті <https://marcogr11.github.io/task_manager/>.

## Піраміда документації

| Рівень | Де | Для кого |
|---|---|---|
| 1. Огляд | цей README, [docs/index.md](docs/index.md) | усі |
| 2. Розробник | [docs/developer/](docs/developer/): [швидкий старт](docs/developer/local-setup.md), [CONTRIBUTING](docs/developer/CONTRIBUTING.md), [стандарти](docs/developer/standards.md) | розробники, QA |
| 3. API | [docs/api/openapi.yaml](docs/api/openapi.yaml) (єдине джерело контрактів), Swagger UI на сайті | інтегратори, QA |
| 4. Архітектура | [SDD](docs/architecture/sdd.md), [ISD](docs/architecture/isd.md), [ADR](docs/architecture/adr/index.md) | архітектор, DevOps |

Перший крок нового учасника: [docs/developer/local-setup.md](docs/developer/local-setup.md).

## Definition of Done для документації

Зміна вважається готовою, коли виконано всі пункти. CI (`.github/workflows/docs.yml`) перевіряє їх автоматично.

| Критерій | Перевірка | Поріг |
|---|---|---|
| OpenAPI валідний і відповідає правилам | `spectral lint docs/api/openapi.yaml --ruleset .spectral.yaml` | 0 errors; warnings обґрунтовано в CHANGELOG |
| Markdown без порушень стилю | `markdownlint-cli2` з `.markdownlint-cli2.yaml` | 0 errors |
| Сайт збирається без попереджень | `mkdocs build --strict` | exit 0: немає мертвих посилань і сторінок поза nav |
| Front matter і review_date | `python scripts/review_dates.py` | 0 помилок front matter; прострочені сторінки переглянуто або переведено в `deprecated` |
| Код і документація узгоджені | `python scripts/doc_audit.py` | exit 0: кожен маршрут є в OpenAPI, кожна змінна оточення є в ISD |
| Запис у CHANGELOG | [CHANGELOG.md](CHANGELOG.md) | є рядок у `Unreleased` |
