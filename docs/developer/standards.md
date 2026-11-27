---
title: Стандарти
owner: MarcoGr11
status: published
review_date: 2027-02-25
tags:
  - developer
---

# Стандарти

## Код

| Правило | Як перевіряється |
|---|---|
| Цикломатична складність функції ≤ 10 | pre-commit `.githooks/complexity_check.sh` (radon, `MAX_CC=10`) |
| Жодних секретів у коді та історії | pre-commit gitleaks, allowlist `.gitleaks.toml` |
| Тести зелені | `python -m pytest` |
| Публічні модулі мають docstring | довідник [[api/reference]] будується з docstring |

## Коміти

Формат Conventional Commits: `type(scope): опис`, типи `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `chore`.

## Документація

Кожен `.md` у `docs/` починається з front matter:

```yaml
---
title: Назва
owner: MarcoGr11            # власник, також у .github/CODEOWNERS
status: published           # draft | in-review | published | deprecated
review_date: 2027-02-25     # дата наступного перегляду
tags: [architecture]        # architecture | api | ops | developer | adr | audit
---
```

- Посилання між документами пишуться як wikilinks `[[architecture/sdd]]`. Їх розуміють Obsidian і MkDocs (плагін ezlinks).
- Один факт живе в одному місці (SSOT). Контракти API тільки в `docs/api/openapi.yaml`, змінні оточення тільки в [[architecture/isd]].
- Сторінка зі `status: deprecated` містить лише посилання на заміну.
- Цикли перегляду: 90 днів для експлуатаційних сторінок, 180 для архітектурних ([[developer/maintenance]]).

## ADR

Правила нумерації, статусів і незмінності: [[architecture/adr/index|журнал ADR]].
